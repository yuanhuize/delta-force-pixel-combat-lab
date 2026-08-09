const { chromium } = require('playwright');
const fs = require('fs');
const http = require('http');
const path = require('path');

const root = path.resolve(__dirname, '../build/web-desktop');
const artifactDir = path.resolve(__dirname, '../artifacts/president_office_r2');
const directionDir = path.join(artifactDir, 'operator_8dir');
fs.mkdirSync(directionDir, { recursive: true });

if (!fs.existsSync(path.join(root, 'index.html'))) {
  throw new Error('Web build is missing. Build Cocos Creator web-desktop before running the smoke test.');
}

const mime = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.json': 'application/json',
  '.css': 'text/css; charset=utf-8',
  '.wasm': 'application/wasm',
  '.bin': 'application/octet-stream',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.ico': 'image/x-icon',
};

const server = http.createServer((request, response) => {
  const requestPath = decodeURIComponent((request.url || '/').split('?')[0]);
  const relative = requestPath === '/' ? 'index.html' : requestPath.replace(/^\/+/, '');
  const target = path.resolve(root, relative);
  if (!target.startsWith(root) || !fs.existsSync(target) || fs.statSync(target).isDirectory()) {
    response.writeHead(404);
    response.end('Not found');
    return;
  }
  response.writeHead(200, { 'Content-Type': mime[path.extname(target)] || 'application/octet-stream' });
  fs.createReadStream(target).pipe(response);
});

const rooms = [
  ['west_entry_corridor', '1'],
  ['east_entry_corridor', '2'],
  ['outside_hall', '3'],
  ['main_hall', '4'],
  ['left_keycard_room', '5'],
  ['right_cinema', '6'],
];

const directions = [
  { index: 0, name: 'Down', keys: ['s'] },
  { index: 1, name: 'DownRight', keys: ['s', 'd'] },
  { index: 2, name: 'Right', keys: ['d'] },
  { index: 3, name: 'UpRight', keys: ['w', 'd'] },
  { index: 4, name: 'Up', keys: ['w'] },
  { index: 5, name: 'UpLeft', keys: ['w', 'a'] },
  { index: 6, name: 'Left', keys: ['a'] },
  { index: 7, name: 'DownLeft', keys: ['s', 'a'] },
];

let browser;
let page;
const errors = [];
const warnings = [];

const qaState = () => page.evaluate(() => globalThis.__PRESIDENT_OFFICE_R2_QA__ ?? null);

(async () => {
  await new Promise(resolve => server.listen(8468, '127.0.0.1', resolve));
  browser = await chromium.launch({
    headless: true,
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  });
  page = await browser.newPage({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1 });
  page.on('pageerror', error => errors.push(`pageerror: ${error.message}`));
  page.on('console', message => {
    if (message.type() === 'error') errors.push(`console: ${message.text()}`);
    if (message.type() === 'warning') warnings.push(`console: ${message.text()}`);
  });

  await page.goto('http://127.0.0.1:8468', { waitUntil: 'networkidle' });
  await page.waitForSelector('canvas');
  try {
    await page.waitForFunction(() => globalThis.__PRESIDENT_OFFICE_R2_QA__?.ready === true, null, { timeout: 20000 });
  } catch (error) {
    const state = await qaState();
    await page.screenshot({ path: path.join(artifactDir, '0_load_failure.png') });
    throw new Error(`R2 scene did not become ready: ${JSON.stringify({ state, errors, warnings })}; ${error.message}`);
  }

  const canvasLocator = page.locator('canvas');
  await canvasLocator.click({ position: { x: 640, y: 360 } });
  await page.evaluate(() => document.querySelector('canvas')?.focus());

  let initialState = await qaState();
  if (
    initialState.operatorMode !== 'A_ART'
    || initialState.dualVersionGate !== 'SCENE_DUAL_VERSION_NOT_READY'
    || initialState.bVersionStatus !== 'WAITING_Q_BRIDGE_PIPELINE_CANDIDATE_READY_AND_USER_APPROVED_Q_MASTER'
  ) {
    throw new Error(`Q Bridge gate mismatch: ${JSON.stringify(initialState)}`);
  }
  await page.keyboard.press('v');
  await page.waitForTimeout(80);
  initialState = await qaState();
  if (initialState.operatorMode !== 'A_ART') {
    throw new Error(`V entered an unapproved B mode: ${JSON.stringify(initialState)}`);
  }

  const waitForRoom = async (roomId, timeout = 5000) => {
    await page.waitForFunction(expected => globalThis.__PRESIDENT_OFFICE_R2_QA__?.roomId === expected, roomId, { timeout });
  };

  const visited = [];
  for (const [roomId, key] of rooms) {
    await page.keyboard.press(key);
    try {
      await waitForRoom(roomId);
    } catch (error) {
      const state = await qaState();
      throw new Error(`Keyboard room switch failed: ${JSON.stringify({ expected: roomId, key, state })}; ${error.message}`);
    }
    await page.waitForTimeout(120);
    await page.screenshot({ path: path.join(artifactDir, `${key}_${roomId}.png`) });
    visited.push(await qaState());
  }
  if (visited.some(state => state.gate !== 'ART_APPROVED' || state.threeDGate !== '3D_APPROVED_TECH_PROOF_ONLY')) {
    throw new Error(`PM gate mismatch during six-room traversal: ${JSON.stringify(visited)}`);
  }
  if (visited.some(state => state.operatorAsset !== 'weilong_v2_1/weilong_body_core_run_8dir_12f_v2_1')) {
    throw new Error(`Unexpected operator runtime asset: ${JSON.stringify(visited)}`);
  }

  await page.keyboard.press('3');
  await waitForRoom('outside_hall');
  const directionChecks = [];
  for (const direction of directions) {
    for (const key of direction.keys) await page.keyboard.down(key);
    await page.waitForFunction(expected => globalThis.__PRESIDENT_OFFICE_R2_QA__?.direction === expected, direction.index, { timeout: 2000 });
    await page.waitForTimeout(140);
    const state = await qaState();
    for (const key of [...direction.keys].reverse()) await page.keyboard.up(key);
    if (state.directionName !== direction.name || state.walkFrame < 0 || state.walkFrame > 11) {
      throw new Error(`Eight-direction mapping failed: ${JSON.stringify({ direction, state })}`);
    }
    if (
      JSON.stringify(state.cell) !== JSON.stringify([128, 128])
      || JSON.stringify(state.footAnchor) !== JSON.stringify([64, 116])
      || state.fps !== 18
      || state.runtimeScale !== 1
      || state.pixelSnap !== true
      || state.preserveWalkFrameOnDirectionChange !== true
      || !state.renderPosition.every(Number.isInteger)
    ) {
      throw new Error(`Approved operator runtime contract failed: ${JSON.stringify(state)}`);
    }
    await page.waitForTimeout(40);
    await page.screenshot({ path: path.join(directionDir, `${direction.index}_${direction.name}.png`) });
    directionChecks.push(state);
  }

  await page.keyboard.down('d');
  const sampledFrames = [];
  for (let index = 0; index < 16; index += 1) {
    await page.waitForTimeout(55);
    sampledFrames.push((await qaState()).walkFrame);
  }
  await page.keyboard.up('d');
  const distinctFrames = [...new Set(sampledFrames)];
  if (distinctFrames.length < 8 || sampledFrames.some(frame => frame < 0 || frame > 11)) {
    throw new Error(`18fps/12-frame animation did not advance continuously: ${JSON.stringify(sampledFrames)}`);
  }

  await page.keyboard.down('d');
  await page.waitForFunction(() => {
    const state = globalThis.__PRESIDENT_OFFICE_R2_QA__;
    return state?.direction === 2 && state?.walkFrame === 5;
  }, null, { timeout: 3000 });
  const beforeDirectionChange = await qaState();
  await page.keyboard.down('w');
  await page.waitForFunction(() => globalThis.__PRESIDENT_OFFICE_R2_QA__?.direction === 3, null, { timeout: 1000 });
  const afterDirectionChange = await qaState();
  await page.screenshot({ path: path.join(artifactDir, '8_preserve_walkframe_turn.png') });
  await page.keyboard.up('w');
  await page.keyboard.up('d');
  if (![beforeDirectionChange.walkFrame, (beforeDirectionChange.walkFrame + 1) % 12].includes(afterDirectionChange.walkFrame)) {
    throw new Error(`Direction change reset or skipped walkFrame: ${JSON.stringify({ beforeDirectionChange, afterDirectionChange })}`);
  }

  for (let round = 0; round < 3; round += 1) {
    for (const direction of directions) {
      for (const key of direction.keys) await page.keyboard.down(key);
      await page.waitForTimeout(28);
      for (const key of [...direction.keys].reverse()) await page.keyboard.up(key);
    }
  }
  await page.waitForTimeout(100);

  await page.keyboard.press('c');
  await page.waitForTimeout(120);
  await page.screenshot({ path: path.join(artifactDir, '7_outside_hall_collision_overlay.png') });

  const doorChecks = [];

  await page.keyboard.press('5');
  await waitForRoom('left_keycard_room');
  await page.waitForTimeout(320);
  await page.keyboard.press('e');
  await page.waitForTimeout(220);
  let state = await qaState();
  if (state.roomId !== 'left_keycard_room') throw new Error('Left keycard door opened without a QA keycard');
  doorChecks.push('left_keycard_locked_without_card');

  await page.keyboard.press('k');
  await page.waitForTimeout(80);
  state = await qaState();
  if (!state.hasDebugKeycard) throw new Error('QA keycard toggle did not update runtime state');
  await page.keyboard.press('e');
  await waitForRoom('main_hall');
  doorChecks.push('left_keycard_opens_with_card');

  await page.waitForTimeout(320);
  await page.keyboard.press('6');
  await waitForRoom('right_cinema');
  await page.waitForTimeout(320);
  await page.keyboard.press('e');
  await waitForRoom('main_hall');
  doorChecks.push('right_cinema_open_passage');

  await page.waitForTimeout(320);
  await page.keyboard.press('4');
  await waitForRoom('main_hall');
  await page.waitForTimeout(320);
  await page.keyboard.press('e');
  await waitForRoom('outside_hall');
  await page.waitForTimeout(320);
  await page.keyboard.press('e');
  await waitForRoom('main_hall');
  doorChecks.push('main_outside_center_door_roundtrip');

  await page.keyboard.press('3');
  await waitForRoom('outside_hall');
  await page.keyboard.down('a');
  await page.waitForTimeout(900);
  await page.keyboard.up('a');
  await page.waitForTimeout(80);
  const boundaryState = await qaState();
  if (boundaryState.roomId !== 'outside_hall' || boundaryState.position[0] < 58) {
    throw new Error(`Outside hall boundary collision failed: ${JSON.stringify(boundaryState)}`);
  }
  doorChecks.push('outside_hall_left_boundary_collision');

  const canvas = await page.locator('canvas').boundingBox();
  const result = {
    ok: errors.length === 0 && warnings.length === 0,
    status: 'A_SCALE1_SCENE_QA_PASS_B_Q_BRIDGE_LOCKED',
    url: 'http://127.0.0.1:8468',
    canvas,
    visited,
    directionChecks,
    animation: { sampledFrames, distinctFrames, fps: 18, frameCount: 12 },
    phasePreservation: { beforeDirectionChange, afterDirectionChange },
    doorChecks,
    boundaryState,
    errors,
    warnings,
  };
  fs.writeFileSync(path.join(artifactDir, 'smoke-result.json'), `${JSON.stringify(result, null, 2)}\n`);
  console.log(JSON.stringify(result, null, 2));
  await browser.close();
  await new Promise(resolve => server.close(resolve));
  if (!result.ok) process.exitCode = 1;
})().catch(error => {
  console.error(error);
  const failure = {
    ok: false,
    status: 'A_SCALE1_SCENE_QA_FAILED_B_Q_BRIDGE_LOCKED',
    error: error.message,
    errors,
    warnings,
  };
  fs.writeFileSync(path.join(artifactDir, 'smoke-result.json'), `${JSON.stringify(failure, null, 2)}\n`);
  if (browser) void browser.close();
  server.close();
  process.exitCode = 1;
});
