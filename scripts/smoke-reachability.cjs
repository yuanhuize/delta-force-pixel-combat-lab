const { chromium } = require('playwright');
const fs = require('fs');
const http = require('http');
const path = require('path');

const projectRoot = path.resolve(__dirname, '..');
const buildRoot = path.join(projectRoot, 'build/web-desktop');
const artifactDir = path.join(projectRoot, 'artifacts/president_office_r2');
const config = JSON.parse(fs.readFileSync(path.join(projectRoot, 'assets/resources/president_office_r2/data/president_office_rooms_r2.json'), 'utf8'));
const gridStep = 16;
const radius = config.probeRadius;
const navigationClearanceRadius = radius + 8;
const port = 8469;

fs.mkdirSync(artifactDir, { recursive: true });

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

function circleIntersectsRect(x, y, rect) {
  const [rx, ry, width, height] = rect;
  const closestX = Math.max(rx, Math.min(x, rx + width));
  const closestY = Math.max(ry, Math.min(y, ry + height));
  const dx = x - closestX;
  const dy = y - closestY;
  return dx * dx + dy * dy < navigationClearanceRadius * navigationClearanceRadius;
}

function canStand(room, x, y) {
  const [bx, by, width, height] = room.playableBounds;
  if (x - radius < bx || x + radius > bx + width || y - radius < by || y + radius > by + height) return false;
  return !room.colliders.some(collider => circleIntersectsRect(x, y, collider.rect));
}

function pointRectDistance(x, y, rect) {
  const [rx, ry, width, height] = rect;
  const closestX = Math.max(rx, Math.min(x, rx + width));
  const closestY = Math.max(ry, Math.min(y, ry + height));
  return Math.hypot(x - closestX, y - closestY);
}

function nearestFree(room, point) {
  const snapped = point.map(value => Math.round(value / gridStep) * gridStep);
  for (let ring = 0; ring < 20; ring += 1) {
    for (let dx = -ring; dx <= ring; dx += 1) {
      for (const dy of [-ring, ring]) {
        const candidate = [snapped[0] + dx * gridStep, snapped[1] + dy * gridStep];
        if (canStand(room, candidate[0], candidate[1])) return candidate;
      }
    }
    for (let dy = -ring + 1; dy < ring; dy += 1) {
      for (const dx of [-ring, ring]) {
        const candidate = [snapped[0] + dx * gridStep, snapped[1] + dy * gridStep];
        if (canStand(room, candidate[0], candidate[1])) return candidate;
      }
    }
  }
  throw new Error(`No free grid point near ${JSON.stringify(point)}`);
}

function buildComponent(room, startPoint) {
  const start = nearestFree(room, startPoint);
  const queue = [start];
  const parent = new Map([[start.join(','), null]]);
  const points = new Map([[start.join(','), start]]);
  for (let index = 0; index < queue.length; index += 1) {
    const [x, y] = queue[index];
    for (const [dx, dy] of [[gridStep, 0], [-gridStep, 0], [0, gridStep], [0, -gridStep]]) {
      const next = [x + dx, y + dy];
      const key = next.join(',');
      if (!parent.has(key) && canStand(room, next[0], next[1])) {
        parent.set(key, [x, y]);
        points.set(key, next);
        queue.push(next);
      }
    }
  }
  return { start, parent, points: [...points.values()] };
}

function findPath(room, startPoint, goalPoint) {
  const start = nearestFree(room, startPoint);
  const goal = nearestFree(room, goalPoint);
  const queue = [start];
  const parent = new Map([[start.join(','), null]]);
  for (let index = 0; index < queue.length; index += 1) {
    const current = queue[index];
    if (current[0] === goal[0] && current[1] === goal[1]) break;
    for (const [dx, dy] of [[gridStep, 0], [-gridStep, 0], [0, gridStep], [0, -gridStep]]) {
      const next = [current[0] + dx, current[1] + dy];
      const key = next.join(',');
      if (!parent.has(key) && canStand(room, next[0], next[1])) {
        parent.set(key, current);
        queue.push(next);
      }
    }
  }
  assert(parent.has(goal.join(',')), `No foot-circle path to ${JSON.stringify(goalPoint)}`);
  const path = [];
  for (let cursor = goal; cursor; cursor = parent.get(cursor.join(','))) path.push(cursor);
  path.reverse();
  const compressed = [path[0]];
  let previousDirection = null;
  for (let index = 1; index < path.length; index += 1) {
    const direction = [Math.sign(path[index][0] - path[index - 1][0]), Math.sign(path[index][1] - path[index - 1][1])];
    if (previousDirection && (direction[0] !== previousDirection[0] || direction[1] !== previousDirection[1])) {
      compressed.push(path[index - 1]);
    }
    previousDirection = direction;
  }
  compressed.push(path[path.length - 1]);
  return compressed.filter((point, index) => index === 0 || point[0] !== compressed[index - 1][0] || point[1] !== compressed[index - 1][1]);
}

function extremalTargets(room) {
  const component = buildComponent(room, room.spawn);
  return {
    minX: component.points.reduce((best, point) => point[0] < best[0] ? point : best, component.start),
    maxX: component.points.reduce((best, point) => point[0] > best[0] ? point : best, component.start),
    minY: component.points.reduce((best, point) => point[1] < best[1] ? point : best, component.start),
    maxY: component.points.reduce((best, point) => point[1] > best[1] ? point : best, component.start),
  };
}

function doorTarget(room, doorId) {
  const door = room.doors.find(candidate => candidate.id === doorId);
  assert(door, `Missing door ${doorId}`);
  const component = buildComponent(room, room.spawn);
  return component.points.reduce((best, point) => pointRectDistance(point[0], point[1], door.rect) < pointRectDistance(best[0], best[1], door.rect) ? point : best, component.start);
}

const mime = {
  '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.json': 'application/json',
  '.css': 'text/css; charset=utf-8', '.wasm': 'application/wasm', '.bin': 'application/octet-stream', '.png': 'image/png',
};

const server = http.createServer((request, response) => {
  const requestPath = decodeURIComponent((request.url || '/').split('?')[0]);
  const relative = requestPath === '/' ? 'index.html' : requestPath.replace(/^\/+/, '');
  const target = path.resolve(buildRoot, relative);
  if (!target.startsWith(buildRoot) || !fs.existsSync(target) || fs.statSync(target).isDirectory()) {
    response.writeHead(404);
    response.end('Not found');
    return;
  }
  response.writeHead(200, { 'Content-Type': mime[path.extname(target)] || 'application/octet-stream' });
  fs.createReadStream(target).pipe(response);
});

let browser;
let page;
const errors = [];
const warnings = [];
const pressed = new Set();
const trajectory = [];
const visitedThroughDoors = [];

async function qaState() {
  return page.evaluate(() => globalThis.__PRESIDENT_OFFICE_R2_QA__ ?? null);
}

async function setPressed(next) {
  for (const key of [...pressed]) {
    if (!next.has(key)) {
      await page.keyboard.up(key);
      pressed.delete(key);
    }
  }
  for (const key of next) {
    if (!pressed.has(key)) {
      await page.keyboard.down(key);
      pressed.add(key);
    }
  }
}

async function driveToPoint(roomId, target) {
  let unchanged = 0;
  let previous = null;
  for (let iteration = 0; iteration < 500; iteration += 1) {
    const state = await qaState();
    assert(state.roomId === roomId, `Unexpected room while moving: ${state.roomId}, expected ${roomId}`);
    const [x, y] = state.position;
    trajectory.push({ roomId, position: [x, y], mode: state.operatorMode });
    const dx = target[0] - x;
    const dy = target[1] - y;
    if (Math.abs(dx) <= 5 && Math.abs(dy) <= 5) {
      await setPressed(new Set());
      return;
    }
    const next = new Set();
    if (Math.abs(dx) > 5) next.add(dx > 0 ? 'd' : 'a');
    else if (Math.abs(dy) > 5) next.add(dy > 0 ? 's' : 'w');
    if (Math.max(Math.abs(dx), Math.abs(dy)) > 42) next.add('Shift');
    await setPressed(next);
    await page.waitForTimeout(32);
    const key = `${x},${y}`;
    unchanged = key === previous ? unchanged + 1 : 0;
    previous = key;
    assert(unchanged < 18, `Movement stalled in ${roomId} near ${JSON.stringify([x, y])}, target ${JSON.stringify(target)}`);
  }
  throw new Error(`Movement timeout in ${roomId} toward ${JSON.stringify(target)}`);
}

async function moveTo(roomId, goal) {
  const start = (await qaState()).position;
  const waypoints = findPath(config.rooms[roomId], start, goal);
  for (const waypoint of waypoints) await driveToPoint(roomId, waypoint);
}

async function interactDoor(fromRoom, doorId, toRoom) {
  await moveTo(fromRoom, doorTarget(config.rooms[fromRoom], doorId));
  await setPressed(new Set());
  await page.keyboard.press('e');
  await page.waitForFunction(expected => globalThis.__PRESIDENT_OFFICE_R2_QA__?.roomId === expected, toRoom, { timeout: 3000 });
  visitedThroughDoors.push({ from: fromRoom, doorId, to: toRoom, spawn: (await qaState()).position });
  await page.waitForTimeout(280);
}

function coverageFor(roomId) {
  const points = trajectory.filter(sample => sample.roomId === roomId).map(sample => sample.position);
  const xs = points.map(point => point[0]);
  const ys = points.map(point => point[1]);
  const bounds = config.rooms[roomId].playableBounds;
  return {
    sampleCount: points.length,
    min: [Math.min(...xs), Math.min(...ys)],
    max: [Math.max(...xs), Math.max(...ys)],
    span: [Math.max(...xs) - Math.min(...xs), Math.max(...ys) - Math.min(...ys)],
    ratio: [
      Number(((Math.max(...xs) - Math.min(...xs)) / bounds[2]).toFixed(4)),
      Number(((Math.max(...ys) - Math.min(...ys)) / bounds[3]).toFixed(4)),
    ],
  };
}

(async () => {
  assert(fs.existsSync(path.join(buildRoot, 'index.html')), 'Web build is missing');
  await new Promise(resolve => server.listen(port, '127.0.0.1', resolve));
  browser = await chromium.launch({ headless: true, executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' });
  page = await browser.newPage({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1 });
  page.on('pageerror', error => errors.push(`pageerror: ${error.message}`));
  page.on('console', message => {
    if (message.type() === 'error') errors.push(`console: ${message.text()}`);
    if (message.type() === 'warning') warnings.push(`console: ${message.text()}`);
  });
  await page.goto(`http://127.0.0.1:${port}`, { waitUntil: 'networkidle' });
  await page.waitForFunction(() => globalThis.__PRESIDENT_OFFICE_R2_QA__?.ready === true, null, { timeout: 20000 });
  await page.locator('canvas').click({ position: { x: 640, y: 360 } });

  let state = await qaState();
  assert(state.runtimeScale === 1 && state.collisionShape === 'foot_circle' && state.collisionRadius === 16, `A scale/collision mismatch: ${JSON.stringify(state)}`);
  assert(state.operatorMode === 'A_ART' && state.bVersionStatus === 'WAITING_Q_BRIDGE_PIPELINE_CANDIDATE_READY_AND_USER_APPROVED_Q_MASTER', `dual gate mismatch: ${JSON.stringify(state)}`);
  await page.keyboard.press('v');
  await page.waitForTimeout(80);
  state = await qaState();
  assert(state.operatorMode === 'A_ART', 'V must not enter B mode before Q Bridge and user-approved Q master are both available');

  for (const target of Object.values(extremalTargets(config.rooms.outside_hall))) await moveTo('outside_hall', target);
  await page.screenshot({ path: path.join(artifactDir, 'a_scale1_outside_full_reach.png') });

  await interactDoor('outside_hall', 'D1', 'west_entry_corridor');
  await interactDoor('west_entry_corridor', 'D1_BACK', 'outside_hall');
  await interactDoor('outside_hall', 'D2', 'east_entry_corridor');
  await interactDoor('east_entry_corridor', 'D2_BACK', 'outside_hall');
  await interactDoor('outside_hall', 'D3', 'main_hall');

  for (const target of Object.values(extremalTargets(config.rooms.main_hall))) await moveTo('main_hall', target);
  await page.screenshot({ path: path.join(artifactDir, 'a_scale1_main_full_reach.png') });

  await moveTo('main_hall', doorTarget(config.rooms.main_hall, 'D4'));
  await page.keyboard.press('k');
  await page.waitForTimeout(80);
  await page.keyboard.press('e');
  await page.waitForFunction(() => globalThis.__PRESIDENT_OFFICE_R2_QA__?.roomId === 'left_keycard_room', null, { timeout: 3000 });
  visitedThroughDoors.push({ from: 'main_hall', doorId: 'D4', to: 'left_keycard_room', spawn: (await qaState()).position });
  await page.waitForTimeout(280);
  await interactDoor('left_keycard_room', 'D4_BACK', 'main_hall');
  await interactDoor('main_hall', 'O1', 'right_cinema');
  await interactDoor('right_cinema', 'O1_BACK', 'main_hall');

  const outsideCoverage = coverageFor('outside_hall');
  const mainCoverage = coverageFor('main_hall');
  assert(outsideCoverage.ratio[0] >= 0.7 && outsideCoverage.ratio[1] >= 0.7, `outside_hall actual trajectory coverage below 70%: ${JSON.stringify(outsideCoverage)}`);
  assert(mainCoverage.ratio[0] >= 0.7 && mainCoverage.ratio[1] >= 0.7, `main_hall actual trajectory coverage below 70%: ${JSON.stringify(mainCoverage)}`);
  assert(new Set(visitedThroughDoors.flatMap(edge => [edge.from, edge.to])).size === 6, `Not all six rooms were reached through doors: ${JSON.stringify(visitedThroughDoors)}`);
  assert(errors.length === 0 && warnings.length === 0, `Browser console is not clean: ${JSON.stringify({ errors, warnings })}`);

  const result = {
    ok: true,
    status: 'A_SCALE1_FULL_REACHABILITY_PASS_B_Q_BRIDGE_LOCKED',
    operatorMode: 'A_ART',
    runtimeScale: 1,
    collisionShape: 'foot_circle',
    collisionRadius: radius,
    navigationClearanceRadius,
    outsideCoverage,
    mainCoverage,
    visitedThroughDoors,
    trajectorySampleCount: trajectory.length,
    trajectory,
    errors,
    warnings,
  };
  fs.writeFileSync(path.join(artifactDir, 'reachability-browser-result.json'), `${JSON.stringify(result, null, 2)}\n`);
  console.log(JSON.stringify({ ...result, trajectory: `[${trajectory.length} samples]` }, null, 2));
  await setPressed(new Set());
  await browser.close();
  await new Promise(resolve => server.close(resolve));
})().catch(async error => {
  await setPressed(new Set()).catch(() => {});
  const failure = { ok: false, status: 'A_SCALE1_FULL_REACHABILITY_FAILED_B_Q_BRIDGE_LOCKED', error: error.message, trajectorySampleCount: trajectory.length, trajectory, visitedThroughDoors, errors, warnings };
  fs.writeFileSync(path.join(artifactDir, 'reachability-browser-result.json'), `${JSON.stringify(failure, null, 2)}\n`);
  console.error(error);
  if (browser) await browser.close().catch(() => {});
  server.close();
  process.exitCode = 1;
});
