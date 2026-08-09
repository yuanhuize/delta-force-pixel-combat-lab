const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const root = path.resolve(__dirname, '..');
const resourcesRoot = path.join(root, 'assets/resources');
const scenePath = path.join(root, 'assets/scenes/PresidentOfficeR2.scene');
const dataRoot = path.join(resourcesRoot, 'president_office_r2');
const graphPath = path.join(dataRoot, 'data/president_office_room_graph_r2.json');
const roomsPath = path.join(dataRoot, 'data/president_office_rooms_r2.json');
const contractPath = path.join(dataRoot, 'operator_contract/approved_operator_atlas_contract_r1.json');
const operatorRoot = path.join(resourcesRoot, 'weilong_v2_1');
const operatorAtlasPath = path.join(operatorRoot, 'weilong_body_core_run_8dir_12f_v2_1.png');
const operatorAnchorsPath = path.join(operatorRoot, 'weilong_elbow_anchors_8dir_12f_v2_1.json');
const operatorSpecPath = path.join(operatorRoot, 'spec_v2_1.json');
const operatorApprovalPath = path.join(operatorRoot, 'ART_APPROVAL_MANIFEST.json');
const expectedDirections = ['Down', 'DownRight', 'Right', 'UpRight', 'Up', 'UpLeft', 'Left', 'DownLeft'];
const expectedRuntimeHashes = {
  [operatorAtlasPath]: 'aeed19fe787a7355f4a362fb9d1fb556702a9692562950fc0991c3d64bd7de0b',
  [operatorAnchorsPath]: '9a59fa24f0c32da775416eafe57fcf4bc0dfa344b607923c8cca644ad598416d',
  [operatorSpecPath]: '14ced3c8c6259fc7905d1f1bd0efdc40ca14bc1478c732ddeba5ac67a7785fd8',
};

const expectedRooms = [
  'outside_hall',
  'main_hall',
  'left_keycard_room',
  'right_cinema',
  'west_entry_corridor',
  'east_entry_corridor',
];

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

function readJson(file) {
  return JSON.parse(fs.readFileSync(file, 'utf8'));
}

function walk(directory) {
  if (!fs.existsSync(directory)) return [];
  return fs.readdirSync(directory, { withFileTypes: true }).flatMap(entry => {
    const file = path.join(directory, entry.name);
    return entry.isDirectory() ? walk(file) : [file];
  });
}

function pngSize(file) {
  const header = fs.readFileSync(file).subarray(0, 24);
  assert(header.toString('ascii', 1, 4) === 'PNG', `${file} is not a PNG`);
  return [header.readUInt32BE(16), header.readUInt32BE(20)];
}

function sha256(file) {
  return crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
}

function sameRoomSet(value, label) {
  const actual = Object.keys(value).sort();
  const expected = [...expectedRooms].sort();
  assert(JSON.stringify(actual) === JSON.stringify(expected), `${label} must contain exactly the six R2 rooms`);
}

function circleIntersectsRect(x, y, radius, rect) {
  const [rx, ry, width, height] = rect;
  const closestX = Math.max(rx, Math.min(x, rx + width));
  const closestY = Math.max(ry, Math.min(y, ry + height));
  const dx = x - closestX;
  const dy = y - closestY;
  return dx * dx + dy * dy < radius * radius;
}

function assertSafeSpawn(roomId, spawn, label, rooms) {
  const room = rooms[roomId];
  const [x, y] = spawn;
  const [bx, by, width, height] = room.playableBounds;
  const radius = roomsConfig.probeRadius;
  assert(x - radius >= bx && x + radius <= bx + width && y - radius >= by && y + radius <= by + height, `${label} is outside ${roomId} playable bounds`);
  const overlap = room.colliders.find(collider => circleIntersectsRect(x, y, radius, collider.rect));
  assert(!overlap, `${label} overlaps ${roomId} collider ${overlap?.id}`);
}

const runtimeFiles = walk(resourcesRoot);
const bannedPattern = /(test0?2|prototype[_ -]?[145]|luna[_ -]?(v|prototype)?[_ -]?[345]|weilong[_ -]?(p|prototype)?[_ -]?1|candidate)/i;
const bannedFiles = runtimeFiles
  .map(file => path.relative(resourcesRoot, file))
  .filter(file => bannedPattern.test(file));
assert(bannedFiles.length === 0, `banned runtime assets found: ${bannedFiles.join(', ')}`);

const outsidePresidentOffice = runtimeFiles
  .map(file => path.relative(resourcesRoot, file))
  .filter(file => !file.startsWith('president_office_r2/') && !file.startsWith('weilong_v2_1/'))
  .filter(file => !['president_office_r2.meta', 'weilong_v2_1.meta', '.DS_Store'].includes(file));
assert(outsidePresidentOffice.length === 0, `unexpected runtime resources found: ${outsidePresidentOffice.join(', ')}`);

const formalOperatorFiles = walk(operatorRoot)
  .map(file => path.relative(operatorRoot, file))
  .filter(file => !file.endsWith('.meta'))
  .sort();
const expectedFormalOperatorFiles = [
  'ART_APPROVAL_MANIFEST.json',
  'spec_v2_1.json',
  'weilong_body_core_run_8dir_12f_v2_1.png',
  'weilong_elbow_anchors_8dir_12f_v2_1.json',
].sort();
assert(JSON.stringify(formalOperatorFiles) === JSON.stringify(expectedFormalOperatorFiles), `formal operator runtime folder contains unexpected files: ${formalOperatorFiles.join(', ')}`);
for (const [file, expectedHash] of Object.entries(expectedRuntimeHashes)) {
  assert(fs.existsSync(file), `approved runtime asset is missing: ${file}`);
  assert(sha256(file) === expectedHash, `approved runtime asset hash mismatch: ${path.basename(file)}`);
}
assert(JSON.stringify(pngSize(operatorAtlasPath)) === JSON.stringify([1536, 1024]), 'approved operator atlas must be 1536x1024 (12x8 cells)');

assert(fs.existsSync(scenePath), 'PresidentOfficeR2.scene is missing');
const sceneText = fs.readFileSync(scenePath, 'utf8');
assert(sceneText.includes('PresidentOfficeR2'), 'PresidentOfficeR2 scene name is missing');
assert(!/LunaRigLab|test0?2/i.test(sceneText), 'legacy character runtime reference remains in the startup scene');

const graph = readJson(graphPath);
const roomsConfig = readJson(roomsPath);
const contract = readJson(contractPath);
const operatorSpec = readJson(operatorSpecPath);
const operatorAnchors = readJson(operatorAnchorsPath);
const operatorApproval = readJson(operatorApprovalPath);
sameRoomSet(graph.rooms, 'room graph');
sameRoomSet(roomsConfig.rooms, 'collision config');
assert(roomsConfig.defaultRoom === 'outside_hall', 'default room must be the outside hall');
assert(/independent data|never sampled from PNG/i.test(roomsConfig.collisionSource), 'collision source must explicitly reject PNG-derived collision');

for (const roomId of expectedRooms) {
  const room = roomsConfig.rooms[roomId];
  assert(Array.isArray(room.colliders), `${roomId} has no authored collider list`);
  assert(Array.isArray(room.doors), `${roomId} has no authored door list`);
  const pngPath = path.join(resourcesRoot, `${room.asset}.png`);
  assert(fs.existsSync(pngPath), `${roomId} PNG is missing`);
  assert(JSON.stringify(pngSize(pngPath)) === JSON.stringify(room.assetSize), `${roomId} PNG dimensions do not match config`);
  const pngMeta = readJson(`${pngPath}.meta`);
  const textureMeta = Object.values(pngMeta.subMetas).find(meta => meta.name === 'texture');
  assert(textureMeta?.userData?.minfilter === 'nearest' && textureMeta?.userData?.magfilter === 'nearest', `${roomId} texture must use nearest filtering`);
  assert(textureMeta?.userData?.mipfilter === 'none', `${roomId} texture mip filter must be none`);
  assertSafeSpawn(roomId, room.spawn, `${roomId} default spawn`, roomsConfig.rooms);
  for (const door of room.doors) {
    if (door.target && door.targetSpawn) assertSafeSpawn(door.target, door.targetSpawn, `${roomId}.${door.id} target spawn`, roomsConfig.rooms);
  }
}

const outside = roomsConfig.rooms.outside_hall;
assert(outside.doors.length === 3, 'outside hall must have exactly west, east, and top-center doors');
assert(!outside.doors.some(door => /bottom|south/i.test(`${door.id} ${door.label}`)), 'outside hall bottom wall must stay sealed');
const keycardDoor = roomsConfig.rooms.main_hall.doors.find(door => door.id === 'D4');
assert(keycardDoor?.kind === 'keycard_locked' && keycardDoor.target === 'left_keycard_room', 'D4 must be the left keycard door');
const cinemaDoor = roomsConfig.rooms.main_hall.doors.find(door => door.id === 'O1');
assert(cinemaDoor?.kind === 'open' && cinemaDoor.target === 'right_cinema', 'O1 must be the right open cinema passage');

assert(contract.status === 'ART_APPROVED' && contract.approvedVersion === 'V2.1', 'operator contract must use ART_APPROVED V2.1');
assert(contract.assetPath === 'weilong_v2_1/weilong_body_core_run_8dir_12f_v2_1', 'operator assetPath must point to the frozen elbow body-core atlas');
assert(contract.anchorsPath === 'weilong_v2_1/weilong_elbow_anchors_8dir_12f_v2_1', 'operator anchorsPath mismatch');
assert(contract.specPath === 'weilong_v2_1/spec_v2_1', 'operator specPath mismatch');
assert(contract.approvalManifestPath === 'weilong_v2_1/ART_APPROVAL_MANIFEST', 'operator approval manifest path mismatch');
assert(JSON.stringify(contract.cellSize) === JSON.stringify([128, 128]), 'operator cells must be 128x128');
assert(JSON.stringify(contract.directionOrder) === JSON.stringify(expectedDirections), 'operator direction order mismatch');
assert(contract.directionCount === 8 && contract.framesPerDirection === 12 && contract.fps === 18, 'operator atlas timing contract mismatch');
assert(contract.preserveWalkFrameOnDirectionChange === true, 'direction switching must preserve walkFrame');
assert(contract.filter === 'nearest' && contract.pixelSnap === true, 'nearest and pixel-snap are required');
assert(JSON.stringify(contract.footAnchor) === JSON.stringify([64, 116]), 'operator foot anchor must be [64,116]');
assert(contract.runtimeScale === 2, 'operator runtime scale must be the approved integer 2x');
assert(contract.allowedRuntimeScales.every(Number.isInteger), 'all allowed operator scales must be integers');
assert(contract.forbiddenRuntimeScales.includes(1.5), '1.5x operator scale must remain forbidden');
assert(contract.threeDBranch.status === '3D_APPROVED_TECH_PROOF_ONLY', '3D V2 approval scope must remain TECH_PROOF_ONLY');
assert(contract.threeDBranch.approvedAssetId === 'WL_Tactical_Rifle_Run_V2', 'unexpected approved 3D technical proof asset');
assert(contract.threeDBranch.runtimeEntry === null, '3D technical proof must not gain a runtime entry implicitly');
assert(contract.threeDBranch.formalPixelAsset === false && contract.threeDBranch.proof128IsFormalPixelAsset === false, '3D/128 proofs must not be treated as formal pixel art');
assert(contract.threeDBranch.mixWithPixelAtlas === false, '3D technical proof must not mix with the pixel atlas');

assert(JSON.stringify(operatorSpec.cell) === JSON.stringify([128, 128]), 'approved spec cell mismatch');
assert(JSON.stringify(operatorSpec.directions) === JSON.stringify(expectedDirections), 'approved spec direction order mismatch');
assert(operatorSpec.framesPerDirection === 12 && operatorSpec.fps === 18, 'approved spec animation timing mismatch');
assert(JSON.stringify(operatorSpec.footPoint) === JSON.stringify([64, 116]), 'approved spec foot point mismatch');
assert(operatorSpec.characterPreviewScale === 2 && operatorSpec.movementPixelSnap === true, 'approved spec scale/pixel-snap mismatch');
assert(operatorSpec.bodySplit === false, 'approved spec must describe one complete body core, not a body split');

assert(operatorAnchors.schemaVersion === '2.1', 'approved anchors schema mismatch');
assert(JSON.stringify(operatorAnchors.directions) === JSON.stringify(expectedDirections), 'approved anchors direction order mismatch');
assert(operatorAnchors.framesPerDirection === 12, 'approved anchors frame count mismatch');
assert(JSON.stringify(operatorAnchors.footPoint) === JSON.stringify([64, 116]), 'approved anchors foot point mismatch');
for (const direction of expectedDirections) {
  assert(Array.isArray(operatorAnchors.frames[direction]) && operatorAnchors.frames[direction].length === 12, `approved anchors must contain 12 frames for ${direction}`);
}

assert(operatorApproval.status === 'ART_APPROVED' && operatorApproval.approvedVersion === 'V2.1', 'PM approval manifest mismatch');
assert(JSON.stringify(operatorApproval.runtimeContract.directions) === JSON.stringify(expectedDirections), 'approval manifest direction order mismatch');
assert(operatorApproval.runtimeContract.runtimeScale === 2 && operatorApproval.runtimeContract.pixelSnap === true, 'approval manifest runtime scale/pixel-snap mismatch');
assert(operatorApproval.restrictions.runtimeBody === 'elbow_body_core_only', 'runtime must use only the elbow body core');
assert(operatorApproval.restrictions.fullbodySourceRuntimeAllowed === false, 'fullbody source must remain QA-only');
assert(operatorApproval.restrictions.attackArmsHandsWeaponsIncluded === false, 'attack hands/weapon must remain absent in this integration');
assert(operatorApproval.restrictions.candidateOrRejectedAssetsAllowed === false, 'candidate/rejected assets must remain blocked');
assert(operatorApproval.restrictions.threeD128ProofAllowed === false, '3D 128 proof must remain blocked from pixel runtime');

const operatorPngMeta = readJson(`${operatorAtlasPath}.meta`);
const operatorTextureMeta = Object.values(operatorPngMeta.subMetas).find(meta => meta.name === 'texture');
assert(operatorTextureMeta?.userData?.minfilter === 'nearest' && operatorTextureMeta?.userData?.magfilter === 'nearest', 'operator texture must use nearest filtering');
assert(operatorTextureMeta?.userData?.mipfilter === 'none', 'operator texture mip filter must be none');

const runtimeSourceText = [
  fs.readFileSync(scenePath, 'utf8'),
  fs.readFileSync(path.join(root, 'assets/scripts/PresidentOfficeR2Lab.ts'), 'utf8'),
  fs.readFileSync(path.join(root, 'assets/scripts/ApprovedOperatorAtlasContract.ts'), 'utf8'),
].join('\n');
assert(!/(test0?2|prototype[_ -]?1|luna[_ -]?(v|prototype)?[_ -]?[345]|frames_128|frames_512|fullbody_run|3d.*proof.*png)/i.test(runtimeSourceText), 'forbidden candidate/rejected/fullbody/3D proof reference found in runtime source');

console.log(JSON.stringify({
  ok: true,
  status: 'ART_APPROVED_RUNTIME_STATIC_OK',
  rooms: expectedRooms.length,
  runtimeFiles: runtimeFiles.length,
  operatorGate: contract.status,
  threeDGate: contract.threeDBranch.status,
  operatorVersion: contract.approvedVersion,
  operatorRuntimeFiles: formalOperatorFiles,
  operatorHashes: Object.fromEntries(Object.entries(expectedRuntimeHashes).map(([file]) => [path.basename(file), sha256(file)])),
}, null, 2));
