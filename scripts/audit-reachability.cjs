const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const configPath = path.join(root, 'assets/resources/president_office_r2/data/president_office_rooms_r2.json');
const artifactDir = path.join(root, 'artifacts/president_office_r2');
const outputPath = path.join(artifactDir, 'reachability-data-audit.json');
const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
const step = 4;
const radius = config.probeRadius;

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

function circleIntersectsRect(x, y, rect) {
  const [rx, ry, width, height] = rect;
  const closestX = Math.max(rx, Math.min(x, rx + width));
  const closestY = Math.max(ry, Math.min(y, ry + height));
  const dx = x - closestX;
  const dy = y - closestY;
  return dx * dx + dy * dy < radius * radius;
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
  const [targetX, targetY] = point;
  const snappedX = Math.round(targetX / step) * step;
  const snappedY = Math.round(targetY / step) * step;
  for (let ring = 0; ring < 30; ring += 1) {
    for (let dx = -ring; dx <= ring; dx += 1) {
      for (const dy of [-ring, ring]) {
        const x = snappedX + dx * step;
        const y = snappedY + dy * step;
        if (canStand(room, x, y)) return [x, y];
      }
    }
    for (let dy = -ring + 1; dy < ring; dy += 1) {
      for (const dx of [-ring, ring]) {
        const x = snappedX + dx * step;
        const y = snappedY + dy * step;
        if (canStand(room, x, y)) return [x, y];
      }
    }
  }
  throw new Error(`No free point near ${JSON.stringify(point)}`);
}

function auditRoom(roomId, room) {
  const start = nearestFree(room, room.spawn);
  const queue = [start];
  const visited = new Set([start.join(',')]);
  const extrema = {
    minX: [...start],
    maxX: [...start],
    minY: [...start],
    maxY: [...start],
  };
  const doorMinDistance = Object.fromEntries(room.doors.map(door => [door.id, Number.POSITIVE_INFINITY]));

  for (let index = 0; index < queue.length; index += 1) {
    const [x, y] = queue[index];
    if (x < extrema.minX[0]) extrema.minX = [x, y];
    if (x > extrema.maxX[0]) extrema.maxX = [x, y];
    if (y < extrema.minY[1]) extrema.minY = [x, y];
    if (y > extrema.maxY[1]) extrema.maxY = [x, y];
    for (const door of room.doors) {
      doorMinDistance[door.id] = Math.min(doorMinDistance[door.id], pointRectDistance(x, y, door.rect));
    }
    for (const [dx, dy] of [[step, 0], [-step, 0], [0, step], [0, -step]]) {
      const next = [x + dx, y + dy];
      const key = next.join(',');
      if (!visited.has(key) && canStand(room, next[0], next[1])) {
        visited.add(key);
        queue.push(next);
      }
    }
  }

  const [bx, by, width, height] = room.playableBounds;
  const coverage = {
    width: (extrema.maxX[0] - extrema.minX[0]) / width,
    height: (extrema.maxY[1] - extrema.minY[1]) / height,
  };
  assert(coverage.width >= 0.7 && coverage.height >= 0.7, `${roomId} connected floor span is below 70%`);
  for (const door of room.doors) {
    assert(doorMinDistance[door.id] <= 105, `${roomId}.${door.id} cannot be reached within interaction range`);
  }

  return {
    spawn: room.spawn,
    snappedStart: start,
    playableBounds: room.playableBounds,
    reachableGridPoints: visited.size,
    extrema,
    spanPixels: [extrema.maxX[0] - extrema.minX[0], extrema.maxY[1] - extrema.minY[1]],
    coverage: {
      width: Number(coverage.width.toFixed(4)),
      height: Number(coverage.height.toFixed(4)),
    },
    doorMinDistance: Object.fromEntries(Object.entries(doorMinDistance).map(([id, distance]) => [id, Number(distance.toFixed(2))])),
  };
}

const rooms = Object.fromEntries(Object.entries(config.rooms).map(([roomId, room]) => [roomId, auditRoom(roomId, room)]));

for (const [roomId, room] of Object.entries(config.rooms)) {
  for (const door of room.doors) {
    if (!door.target || !door.targetSpawn) continue;
    const targetRoom = config.rooms[door.target];
    assert(canStand(targetRoom, door.targetSpawn[0], door.targetSpawn[1]), `${roomId}.${door.id} target spawn is blocked in ${door.target}`);
  }
}

const result = {
  ok: true,
    status: 'A_COLLISION_DATA_AUDIT_PASS_B_Q_BRIDGE_LOCKED',
  collisionModel: 'foot_circle',
  collisionRadius: radius,
  gridStep: step,
  minimumRequiredSpan: 0.7,
  rooms,
};

fs.mkdirSync(artifactDir, { recursive: true });
fs.writeFileSync(outputPath, `${JSON.stringify(result, null, 2)}\n`);
console.log(JSON.stringify(result, null, 2));
