import {
  _decorator,
  Color,
  Component,
  EventKeyboard,
  Graphics,
  HorizontalTextAlignment,
  input,
  Input,
  JsonAsset,
  KeyCode,
  Label,
  Mask,
  Node,
  Rect,
  resources,
  Size,
  Sprite,
  SpriteFrame,
  Texture2D,
  UITransform,
  Vec2,
  VerticalTextAlignment,
} from 'cc';

import { APPROVED_OPERATOR_ATLAS_CONTRACT, ApprovedOperatorAnimationClock } from './ApprovedOperatorAtlasContract';

const { ccclass } = _decorator;

type RoomId =
  | 'outside_hall'
  | 'main_hall'
  | 'left_keycard_room'
  | 'right_cinema'
  | 'west_entry_corridor'
  | 'east_entry_corridor';

type RectData = [number, number, number, number];

interface DoorData {
  id: string;
  kind: 'open' | 'keycard_locked' | 'external_boundary';
  rect: RectData;
  target?: RoomId;
  targetSpawn?: [number, number];
  requiredItem?: string;
  label: string;
}

interface ColliderData {
  id: string;
  rect: RectData;
  height: 'low' | 'half' | 'high';
}

interface RoomData {
  displayName: string;
  asset: string;
  assetSize: [number, number];
  playableBounds: RectData;
  spawn: [number, number];
  doors: DoorData[];
  colliders: ColliderData[];
}

interface RoomsConfig {
  version: string;
  collisionSource: string;
  defaultRoom: RoomId;
  probeRadius: number;
  rooms: Record<RoomId, RoomData>;
}

interface OperatorContractData {
  status?: string;
  approvedVersion?: string;
  assetPath?: string | null;
  anchorsPath?: string;
  specPath?: string;
  approvalManifestPath?: string;
  cellSize?: [number, number];
  directionOrder?: string[];
  framesPerDirection?: number;
  fps?: number;
  footAnchor?: [number, number];
  runtimeScale?: number;
  preserveWalkFrameOnDirectionChange?: boolean;
  filter?: string;
  pixelSnap?: boolean;
  threeDBranch?: { status?: string; runtimeEntry?: string | null; formalPixelAsset?: boolean; proof128IsFormalPixelAsset?: boolean; mixWithPixelAtlas?: boolean };
}

interface OperatorSpecData {
  cell?: [number, number];
  directions?: string[];
  framesPerDirection?: number;
  fps?: number;
  footPoint?: [number, number];
  characterPreviewScale?: number;
  movementPixelSnap?: boolean;
  bodySplit?: boolean;
}

interface OperatorAnchorsData {
  schemaVersion?: string;
  directions?: string[];
  framesPerDirection?: number;
  coordinateSpace?: string;
  footPoint?: [number, number];
  frames?: Record<string, unknown[]>;
}

interface OperatorApprovalData {
  status?: string;
  approvedVersion?: string;
  runtimeContract?: {
    cell?: [number, number];
    directions?: string[];
    framesPerDirection?: number;
    fps?: number;
    footPoint?: [number, number];
    runtimeScale?: number;
    filter?: string;
    pixelSnap?: boolean;
    preserveWalkFrameOnDirectionChange?: boolean;
  };
  restrictions?: {
    runtimeBody?: string;
    fullbodySourceRuntimeAllowed?: boolean;
    attackArmsHandsWeaponsIncluded?: boolean;
    candidateOrRejectedAssetsAllowed?: boolean;
    threeD128ProofAllowed?: boolean;
    approvedPixelsFrozen?: boolean;
  };
}

interface DualVersionContractData {
  status?: string;
  switchKey?: string;
  shared?: {
    directionOrder?: string[];
    targetVisibleHeight?: [number, number];
    filter?: string;
    pixelSnap?: boolean;
    collisionShape?: string;
    collisionRadius?: number;
    mixedLayersAllowed?: boolean;
  };
  versions?: {
    A_ART?: { status?: string; assetPath?: string; framesPerDirection?: number; runtimeScale?: number; containsForearmsHandsRifle?: boolean };
    B_Q_BRIDGE?: {
      status?: string;
      assetPath?: null;
      specPath?: null;
      approvalManifestPath?: null;
      framesPerDirection?: null;
      containsCompleteBodyArmsHandsRifle?: boolean;
      prerequisites?: { qBridgePipelineCandidateReady?: boolean; userApprovedQMaster?: boolean };
    };
  };
  runtimeRestrictions?: {
    aAndBShareFrames?: boolean;
    aAndBShareLayers?: boolean;
    bMayMasqueradeAsArtApproved?: boolean;
    singleDirection3DProofAllowed?: boolean;
    threeD128ProofAllowed?: boolean;
    rawThreeDDirectDownsampleAllowed?: boolean;
  };
}

const ROOM_ORDER: RoomId[] = [
  'west_entry_corridor',
  'east_entry_corridor',
  'outside_hall',
  'main_hall',
  'left_keycard_room',
  'right_cinema',
];

const VIEWPORT_WIDTH = 960;
const VIEWPORT_HEIGHT = 540;
const THREE_D_GATE = '3D_APPROVED_TECH_PROOF_ONLY';
const ART_GATE = 'ART_APPROVED';

const COLORS = {
  shell: new Color(5, 9, 12, 255),
  panel: new Color(10, 20, 25, 242),
  border: new Color(65, 181, 172, 255),
  text: new Color(229, 241, 238, 255),
  muted: new Color(142, 181, 177, 255),
  cyan: new Color(60, 225, 211, 255),
  amber: new Color(255, 190, 80, 255),
  blocked: new Color(255, 92, 84, 110),
  lowCover: new Color(71, 183, 226, 85),
  highCover: new Color(255, 151, 73, 95),
  door: new Color(77, 255, 210, 150),
};

@ccclass('PresidentOfficeR2Lab')
export class PresidentOfficeR2Lab extends Component {
  private config!: RoomsConfig;
  private currentRoomId!: RoomId;
  private currentRoom!: RoomData;
  private roomFrames = new Map<RoomId, SpriteFrame>();
  private pressed = new Set<KeyCode>();
  private logicalPosition = new Vec2();
  private viewportNode!: Node;
  private roomRoot!: Node;
  private backgroundNode!: Node;
  private backgroundSprite!: Sprite;
  private overlayNode!: Node;
  private overlay!: Graphics;
  private operatorNode!: Node;
  private operatorSprite!: Sprite;
  private operatorFrames: SpriteFrame[][] = [];
  private animationClock = new ApprovedOperatorAnimationClock();
  private dualContract!: DualVersionContractData;
  private operatorMoving = false;
  private roomLabel!: Label;
  private statusLabel!: Label;
  private helpLabel!: Label;
  private gateLabel!: Label;
  private assetsReady = false;
  private showCollision = false;
  private hasDebugKeycard = false;
  private transitionCooldown = 0;
  private toastUntil = 0;
  private toastMessage = '';

  start(): void {
    this.createStage();
    this.publishQaState({ ready: false, roomId: null, gate: ART_GATE, threeDGate: THREE_D_GATE, viewport: [VIEWPORT_WIDTH, VIEWPORT_HEIGHT], cameraMode: 'follow' });
    this.bindInput();
    void this.loadSceneAssets();
  }

  onDestroy(): void {
    input.off(Input.EventType.KEY_DOWN, this.onKeyDown, this);
    input.off(Input.EventType.KEY_UP, this.onKeyUp, this);
  }

  update(dt: number): void {
    if (!this.assetsReady) return;
    this.transitionCooldown = Math.max(0, this.transitionCooldown - dt);

    const movement = this.movementVector();
    this.operatorMoving = movement.lengthSqr() > 0;
    if (this.operatorMoving) {
      movement.normalize();
      this.animationClock.setDirection(this.directionForMovement(movement));
      const speed = this.pressed.has(KeyCode.SHIFT_LEFT) ? 440 : 270;
      this.tryMove(movement.x * speed * dt, movement.y * speed * dt);
    }
    this.animationClock.update(dt, this.operatorMoving);
    this.applyOperatorFrame();

    this.placeOperator();
    this.updateStatus();
    this.publishCurrentQaState();
  }

  private createStage(): void {
    const shell = new Node('SceneShell');
    shell.layer = this.node.layer;
    shell.addComponent(UITransform).setContentSize(1280, 720);
    this.node.addChild(shell);
    const shellGraphics = shell.addComponent(Graphics);
    shellGraphics.fillColor = COLORS.shell;
    shellGraphics.fillRect(-640, -360, 1280, 720);
    shellGraphics.fillColor = COLORS.panel;
    shellGraphics.roundRect(-625, 280, 1250, 65, 8);
    shellGraphics.fill();
    shellGraphics.roundRect(-625, -346, 1250, 56, 8);
    shellGraphics.fill();
    shellGraphics.strokeColor = COLORS.border;
    shellGraphics.lineWidth = 1;
    shellGraphics.roundRect(-625, 280, 1250, 65, 8);
    shellGraphics.stroke();
    shellGraphics.roundRect(-625, -346, 1250, 56, 8);
    shellGraphics.stroke();

    this.roomLabel = this.createLabel('RoomLabel', 0, 323, 20, COLORS.text, 1220);
    this.roomLabel.string = '总裁室 R2 · 正在载入六房场景';
    this.statusLabel = this.createLabel('StatusLabel', 0, 294, 14, COLORS.cyan, 1220);
    this.statusLabel.string = '读取正式 Cocos 地图资源与独立碰撞数据……';
    this.helpLabel = this.createLabel('HelpLabel', 0, -314, 13, COLORS.text, 1230);
    this.helpLabel.string = 'WASD/方向键移动　Shift 快速移动　E/空格开门　V 查看B版闸门　K 调试卡　C 碰撞层　1–6 QA切房　R 重置';
    this.gateLabel = this.createLabel('GateLabel', 0, -336, 11, COLORS.muted, 1230);
    this.gateLabel.string = 'A 美术版 · 威龙 V2.1 肘部身体核心 · 1× nearest · B 等待 Q Bridge 与用户批准Q版母版';

    this.viewportNode = new Node('FollowCameraViewport960x540');
    this.viewportNode.layer = this.node.layer;
    this.viewportNode.setPosition(0, -8, 0);
    this.viewportNode.addComponent(UITransform).setContentSize(VIEWPORT_WIDTH, VIEWPORT_HEIGHT);
    const viewportMask = this.viewportNode.addComponent(Mask);
    viewportMask.type = Mask.Type.GRAPHICS_RECT;
    this.node.addChild(this.viewportNode);

    const viewportBorder = new Node('ViewportBorder');
    viewportBorder.layer = this.node.layer;
    viewportBorder.setPosition(0, -8, 0);
    viewportBorder.addComponent(UITransform).setContentSize(VIEWPORT_WIDTH, VIEWPORT_HEIGHT);
    const viewportBorderGraphics = viewportBorder.addComponent(Graphics);
    viewportBorderGraphics.strokeColor = COLORS.border;
    viewportBorderGraphics.lineWidth = 2;
    viewportBorderGraphics.rect(-VIEWPORT_WIDTH / 2, -VIEWPORT_HEIGHT / 2, VIEWPORT_WIDTH, VIEWPORT_HEIGHT);
    viewportBorderGraphics.stroke();
    this.node.addChild(viewportBorder);

    this.roomRoot = new Node('RoomRoot');
    this.roomRoot.layer = this.node.layer;
    this.viewportNode.addChild(this.roomRoot);

    this.backgroundNode = new Node('RoomBackground');
    this.backgroundNode.layer = this.node.layer;
    this.backgroundSprite = this.backgroundNode.addComponent(Sprite);
    this.backgroundSprite.sizeMode = Sprite.SizeMode.CUSTOM;
    this.backgroundSprite.trim = false;
    this.roomRoot.addChild(this.backgroundNode);

    this.overlayNode = new Node('AuthoredCollisionOverlay');
    this.overlayNode.layer = this.node.layer;
    this.overlay = this.overlayNode.addComponent(Graphics);
    this.roomRoot.addChild(this.overlayNode);

    this.operatorNode = new Node('WeilongApprovedV2_1ElbowBodyCore');
    this.operatorNode.layer = this.node.layer;
    const operatorTransform = this.operatorNode.addComponent(UITransform);
    operatorTransform.setContentSize(APPROVED_OPERATOR_ATLAS_CONTRACT.cellWidth, APPROVED_OPERATOR_ATLAS_CONTRACT.cellHeight);
    operatorTransform.setAnchorPoint(
      APPROVED_OPERATOR_ATLAS_CONTRACT.footPoint[0] / APPROVED_OPERATOR_ATLAS_CONTRACT.cellWidth,
      (APPROVED_OPERATOR_ATLAS_CONTRACT.cellHeight - APPROVED_OPERATOR_ATLAS_CONTRACT.footPoint[1]) / APPROVED_OPERATOR_ATLAS_CONTRACT.cellHeight,
    );
    this.operatorNode.setScale(APPROVED_OPERATOR_ATLAS_CONTRACT.runtimeScale, APPROVED_OPERATOR_ATLAS_CONTRACT.runtimeScale, 1);
    this.operatorSprite = this.operatorNode.addComponent(Sprite);
    this.operatorSprite.sizeMode = Sprite.SizeMode.CUSTOM;
    this.operatorSprite.trim = false;
    this.roomRoot.addChild(this.operatorNode);
  }

  private createLabel(name: string, x: number, y: number, size: number, color: Color, width: number): Label {
    const node = new Node(name);
    node.layer = this.node.layer;
    node.setPosition(x, y, 0);
    const transform = node.addComponent(UITransform);
    transform.setContentSize(width, size + 10);
    const label = node.addComponent(Label);
    label.fontSize = size;
    label.lineHeight = size + 3;
    label.color = color;
    label.horizontalAlign = HorizontalTextAlignment.CENTER;
    label.verticalAlign = VerticalTextAlignment.CENTER;
    this.node.addChild(node);
    return label;
  }

  private bindInput(): void {
    input.on(Input.EventType.KEY_DOWN, this.onKeyDown, this);
    input.on(Input.EventType.KEY_UP, this.onKeyUp, this);
  }

  private readonly onKeyDown = (event: EventKeyboard): void => {
    this.pressed.add(event.keyCode);
    if (!this.assetsReady) return;
    if (event.keyCode === KeyCode.KEY_E || event.keyCode === KeyCode.SPACE) {
      this.tryDoorInteraction();
    } else if (event.keyCode === KeyCode.KEY_C) {
      this.showCollision = !this.showCollision;
      this.redrawOverlay();
      this.toast(this.showCollision ? '已显示独立碰撞层' : '已隐藏独立碰撞层');
    } else if (event.keyCode === KeyCode.KEY_K) {
      this.hasDebugKeycard = !this.hasDebugKeycard;
      this.toast(this.hasDebugKeycard ? 'QA：已授予测试钥匙卡' : 'QA：已移除测试钥匙卡');
    } else if (event.keyCode === KeyCode.KEY_R) {
      this.logicalPosition.set(this.currentRoom.spawn[0], this.currentRoom.spawn[1]);
      this.toast('已重置到当前房间出生点');
    } else if (event.keyCode === KeyCode.KEY_V) {
      this.toast('B 版等待 Q_BRIDGE_PIPELINE_CANDIDATE_READY 与用户批准Q版母版；当前保持 A 美术版');
    } else {
      const jumpIndex = this.qaRoomIndex(event.keyCode);
      if (jumpIndex >= 0) this.switchRoom(ROOM_ORDER[jumpIndex]);
    }
  };

  private readonly onKeyUp = (event: EventKeyboard): void => {
    this.pressed.delete(event.keyCode);
  };

  private qaRoomIndex(key: KeyCode): number {
    const keys = [KeyCode.DIGIT_1, KeyCode.DIGIT_2, KeyCode.DIGIT_3, KeyCode.DIGIT_4, KeyCode.DIGIT_5, KeyCode.DIGIT_6];
    return keys.indexOf(key);
  }

  private movementVector(): Vec2 {
    let x = 0;
    let y = 0;
    if (this.pressed.has(KeyCode.KEY_A) || this.pressed.has(KeyCode.ARROW_LEFT)) x -= 1;
    if (this.pressed.has(KeyCode.KEY_D) || this.pressed.has(KeyCode.ARROW_RIGHT)) x += 1;
    if (this.pressed.has(KeyCode.KEY_W) || this.pressed.has(KeyCode.ARROW_UP)) y -= 1;
    if (this.pressed.has(KeyCode.KEY_S) || this.pressed.has(KeyCode.ARROW_DOWN)) y += 1;
    return new Vec2(x, y);
  }

  private directionForMovement(movement: Vec2): number {
    const horizontal = movement.x < 0 ? -1 : movement.x > 0 ? 1 : 0;
    const vertical = movement.y < 0 ? -1 : movement.y > 0 ? 1 : 0;
    if (vertical > 0) return horizontal < 0 ? 7 : horizontal > 0 ? 1 : 0;
    if (vertical < 0) return horizontal < 0 ? 5 : horizontal > 0 ? 3 : 4;
    return horizontal < 0 ? 6 : 2;
  }

  private tryMove(dx: number, dy: number): void {
    const nextX = this.logicalPosition.x + dx;
    const nextY = this.logicalPosition.y + dy;
    if (this.canStandAt(nextX, this.logicalPosition.y)) this.logicalPosition.x = nextX;
    if (this.canStandAt(this.logicalPosition.x, nextY)) this.logicalPosition.y = nextY;
  }

  private canStandAt(x: number, y: number): boolean {
    const radius = this.config.probeRadius;
    const [bx, by, bw, bh] = this.currentRoom.playableBounds;
    if (x - radius < bx || x + radius > bx + bw || y - radius < by || y + radius > by + bh) return false;
    return !this.currentRoom.colliders.some(({ rect }) => this.circleIntersectsRect(x, y, radius, rect));
  }

  private circleIntersectsRect(x: number, y: number, radius: number, rect: RectData): boolean {
    const [rx, ry, rw, rh] = rect;
    const closestX = Math.max(rx, Math.min(x, rx + rw));
    const closestY = Math.max(ry, Math.min(y, ry + rh));
    const dx = x - closestX;
    const dy = y - closestY;
    return dx * dx + dy * dy < radius * radius;
  }

  private tryDoorInteraction(): void {
    if (this.transitionCooldown > 0) return;
    const door = this.nearestDoor(105);
    if (!door) {
      this.toast('附近没有可交互房门');
      return;
    }
    if (door.kind === 'external_boundary') {
      this.toast('外部区域未纳入本轮六房测试');
      return;
    }
    if (door.kind === 'keycard_locked' && !this.hasDebugKeycard) {
      this.toast('左侧刷卡房已锁定；按 K 授予 QA 测试卡');
      return;
    }
    if (!door.target || !door.targetSpawn) {
      this.toast('房门缺少目标房间数据');
      return;
    }
    this.switchRoom(door.target, door.targetSpawn);
    this.transitionCooldown = 0.25;
  }

  private nearestDoor(maxDistance: number): DoorData | undefined {
    let best: DoorData | undefined;
    let bestDistance = maxDistance;
    for (const door of this.currentRoom.doors) {
      const [x, y, width, height] = door.rect;
      const nearestX = Math.max(x, Math.min(this.logicalPosition.x, x + width));
      const nearestY = Math.max(y, Math.min(this.logicalPosition.y, y + height));
      const distance = Math.hypot(this.logicalPosition.x - nearestX, this.logicalPosition.y - nearestY);
      if (distance < bestDistance) {
        bestDistance = distance;
        best = door;
      }
    }
    return best;
  }

  private switchRoom(roomId: RoomId, spawn?: [number, number]): void {
    const room = this.config.rooms[roomId];
    const frame = this.roomFrames.get(roomId);
    if (!room || !frame) throw new Error(`Room asset unavailable: ${roomId}`);
    this.currentRoomId = roomId;
    this.currentRoom = room;
    this.backgroundSprite.spriteFrame = frame;
    const [width, height] = room.assetSize;
    this.backgroundNode.getComponent(UITransform)!.setContentSize(width, height);
    this.roomRoot.setScale(1, 1, 1);
    const initial = spawn ?? room.spawn;
    this.logicalPosition.set(initial[0], initial[1]);
    this.roomLabel.string = `总裁室 R2 · ${room.displayName}`;
    this.redrawOverlay();
    this.placeOperator();
    this.publishCurrentQaState();
    this.toast(`已进入：${room.displayName}`);
  }

  private placeOperator(): void {
    const [width, height] = this.currentRoom.assetSize;
    const operatorX = Math.round(this.logicalPosition.x - width / 2);
    const operatorY = Math.round(height / 2 - this.logicalPosition.y);
    this.operatorNode.setPosition(operatorX, operatorY, 0);

    const minCameraX = VIEWPORT_WIDTH / 2 - width / 2;
    const maxCameraX = width / 2 - VIEWPORT_WIDTH / 2;
    const minCameraY = VIEWPORT_HEIGHT / 2 - height / 2;
    const maxCameraY = height / 2 - VIEWPORT_HEIGHT / 2;
    const cameraX = Math.max(minCameraX, Math.min(-operatorX, maxCameraX));
    const cameraY = Math.max(minCameraY, Math.min(-operatorY, maxCameraY));
    this.roomRoot.setPosition(Math.round(cameraX), Math.round(cameraY), 0);
  }

  private redrawOverlay(): void {
    this.overlay.clear();
    if (!this.showCollision) return;
    const [width, height] = this.currentRoom.assetSize;
    for (const collider of this.currentRoom.colliders) {
      const [x, y, rectWidth, rectHeight] = collider.rect;
      this.overlay.fillColor = collider.height === 'low' ? COLORS.lowCover : collider.height === 'half' ? COLORS.highCover : COLORS.blocked;
      this.overlay.fillRect(x - width / 2, height / 2 - y - rectHeight, rectWidth, rectHeight);
    }
    this.overlay.strokeColor = COLORS.door;
    this.overlay.lineWidth = 4;
    for (const door of this.currentRoom.doors) {
      const [x, y, rectWidth, rectHeight] = door.rect;
      this.overlay.rect(x - width / 2, height / 2 - y - rectHeight, rectWidth, rectHeight);
      this.overlay.stroke();
    }
  }

  private updateStatus(): void {
    const door = this.nearestDoor(105);
    const gate = this.hasDebugKeycard ? '测试钥匙卡：有' : '测试钥匙卡：无';
    if (performance.now() < this.toastUntil) {
      this.statusLabel.string = this.toastMessage;
    } else if (door) {
      const verb = door.kind === 'external_boundary' ? '边界' : door.kind === 'keycard_locked' ? '刷卡门' : '开放门';
      this.statusLabel.string = `${gate} · 附近：${door.label}（${verb}，按 E）`;
    } else {
      this.statusLabel.string = `${gate} · 威龙 ${APPROVED_OPERATOR_ATLAS_CONTRACT.directionOrder[this.animationClock.direction]} F${this.animationClock.walkFrame + 1}/12 · (${Math.round(this.logicalPosition.x)}, ${Math.round(this.logicalPosition.y)})`;
    }
  }

  private toast(message: string): void {
    this.toastMessage = message;
    this.toastUntil = performance.now() + 1600;
  }

  private async loadSceneAssets(): Promise<void> {
    try {
      const [configAsset, graphAsset, contractAsset, dualContractAsset, specAsset, anchorsAsset, approvalAsset] = await Promise.all([
        this.loadJson('president_office_r2/data/president_office_rooms_r2'),
        this.loadJson('president_office_r2/data/president_office_room_graph_r2'),
        this.loadJson('president_office_r2/operator_contract/approved_operator_atlas_contract_r1'),
        this.loadJson('president_office_r2/operator_contract/dual_version_runtime_contract_r1'),
        this.loadJson(APPROVED_OPERATOR_ATLAS_CONTRACT.specPath),
        this.loadJson(APPROVED_OPERATOR_ATLAS_CONTRACT.anchorsPath),
        this.loadJson(APPROVED_OPERATOR_ATLAS_CONTRACT.approvalManifestPath),
      ]);
      this.config = configAsset.json as RoomsConfig;
      this.dualContract = dualContractAsset.json as DualVersionContractData;
      const graph = graphAsset.json as { rooms?: Record<string, unknown> };
      const contract = contractAsset.json as OperatorContractData;
      this.validateRuntimeGate(
        graph,
        contract,
        this.dualContract,
        specAsset.json as OperatorSpecData,
        anchorsAsset.json as OperatorAnchorsData,
        approvalAsset.json as OperatorApprovalData,
      );

      await Promise.all(ROOM_ORDER.map(async roomId => {
        const room = this.config.rooms[roomId];
        const frame = await this.loadSpriteFrame(`${room.asset}/spriteFrame`);
        this.roomFrames.set(roomId, frame);
      }));

      const texture = await this.loadTexture(APPROVED_OPERATOR_ATLAS_CONTRACT.assetPath);
      texture.setFilters(Texture2D.Filter.NEAREST, Texture2D.Filter.NEAREST);
      texture.setMipFilter(Texture2D.Filter.NONE);
      texture.setWrapMode(Texture2D.WrapMode.CLAMP_TO_EDGE, Texture2D.WrapMode.CLAMP_TO_EDGE);
      this.operatorFrames = this.sliceOperatorTexture(texture);
      this.applyOperatorFrame();

      this.assetsReady = true;
      this.switchRoom(this.config.defaultRoom);
      this.gateLabel.string = `A ${APPROVED_OPERATOR_ATLAS_CONTRACT.approvalStatus} V2.1 · 8×12 / 18fps / 1× · B WAITING_Q_BRIDGE_AND_USER_APPROVAL`;
    } catch (error) {
      console.error('[PresidentOfficeR2Lab] load failed', error);
      this.publishQaState({ ready: false, roomId: null, gate: ART_GATE, threeDGate: THREE_D_GATE, viewport: [VIEWPORT_WIDTH, VIEWPORT_HEIGHT], cameraMode: 'follow', error: String(error) });
      this.statusLabel.color = COLORS.amber;
      this.statusLabel.string = `场景加载失败：${String(error)}`;
    }
  }

  private validateRuntimeGate(
    graph: { rooms?: Record<string, unknown> },
    contract: OperatorContractData,
    dualContract: DualVersionContractData,
    spec: OperatorSpecData,
    anchors: OperatorAnchorsData,
    approval: OperatorApprovalData,
  ): void {
    if (!graph.rooms || Object.keys(graph.rooms).length !== ROOM_ORDER.length) {
      throw new Error('room graph R2 must contain exactly six rooms');
    }
    const expectedDirections = [...APPROVED_OPERATOR_ATLAS_CONTRACT.directionOrder];
    const expectedCell: [number, number] = [APPROVED_OPERATOR_ATLAS_CONTRACT.cellWidth, APPROVED_OPERATOR_ATLAS_CONTRACT.cellHeight];
    const expectedFoot: [number, number] = [APPROVED_OPERATOR_ATLAS_CONTRACT.footPoint[0], APPROVED_OPERATOR_ATLAS_CONTRACT.footPoint[1]];
    if (contract.status !== ART_GATE || contract.assetPath !== APPROVED_OPERATOR_ATLAS_CONTRACT.assetPath) {
      throw new Error('operator atlas must use the frozen ART_APPROVED V2.1 asset path');
    }
    if (
      JSON.stringify(contract.cellSize) !== JSON.stringify(expectedCell)
      || JSON.stringify(contract.directionOrder) !== JSON.stringify(expectedDirections)
      || JSON.stringify(contract.footAnchor) !== JSON.stringify(expectedFoot)
      || contract.framesPerDirection !== APPROVED_OPERATOR_ATLAS_CONTRACT.framesPerDirection
      || contract.fps !== APPROVED_OPERATOR_ATLAS_CONTRACT.fps
      || contract.runtimeScale !== APPROVED_OPERATOR_ATLAS_CONTRACT.runtimeScale
      || contract.preserveWalkFrameOnDirectionChange !== true
      || contract.filter !== 'nearest'
      || contract.pixelSnap !== true
    ) {
      throw new Error('operator JSON contract does not match the approved atlas runtime specification');
    }
    if (
      dualContract.status !== 'SCENE_DUAL_VERSION_NOT_READY'
      || dualContract.switchKey !== 'V'
      || dualContract.shared?.collisionShape !== 'foot_circle'
      || dualContract.shared.collisionRadius !== this.config.probeRadius
      || dualContract.shared.mixedLayersAllowed !== false
      || JSON.stringify(dualContract.shared.directionOrder) !== JSON.stringify(expectedDirections)
      || dualContract.versions?.A_ART?.status !== ART_GATE
      || dualContract.versions.A_ART.assetPath !== APPROVED_OPERATOR_ATLAS_CONTRACT.assetPath
      || dualContract.versions.A_ART.framesPerDirection !== APPROVED_OPERATOR_ATLAS_CONTRACT.framesPerDirection
      || dualContract.versions.A_ART.runtimeScale !== 1
      || dualContract.versions.A_ART.containsForearmsHandsRifle !== false
      || dualContract.versions?.B_Q_BRIDGE?.status !== 'WAITING_Q_BRIDGE_PIPELINE_CANDIDATE_READY_AND_USER_APPROVED_Q_MASTER'
      || dualContract.versions.B_Q_BRIDGE.assetPath !== null
      || dualContract.versions.B_Q_BRIDGE.specPath !== null
      || dualContract.versions.B_Q_BRIDGE.approvalManifestPath !== null
      || dualContract.versions.B_Q_BRIDGE.framesPerDirection !== null
      || dualContract.versions.B_Q_BRIDGE.containsCompleteBodyArmsHandsRifle !== true
      || dualContract.versions.B_Q_BRIDGE.prerequisites?.qBridgePipelineCandidateReady !== false
      || dualContract.versions.B_Q_BRIDGE.prerequisites.userApprovedQMaster !== false
      || dualContract.runtimeRestrictions?.aAndBShareFrames !== false
      || dualContract.runtimeRestrictions.aAndBShareLayers !== false
      || dualContract.runtimeRestrictions.bMayMasqueradeAsArtApproved !== false
      || dualContract.runtimeRestrictions.singleDirection3DProofAllowed !== false
      || dualContract.runtimeRestrictions.threeD128ProofAllowed !== false
      || dualContract.runtimeRestrictions.rawThreeDDirectDownsampleAllowed !== false
    ) {
      throw new Error('dual-version gate must keep A active and B locked until Q Bridge is ready and the user approves the Q master');
    }
    if (
      JSON.stringify(spec.cell) !== JSON.stringify(expectedCell)
      || JSON.stringify(spec.directions) !== JSON.stringify(expectedDirections)
      || spec.framesPerDirection !== APPROVED_OPERATOR_ATLAS_CONTRACT.framesPerDirection
      || spec.fps !== APPROVED_OPERATOR_ATLAS_CONTRACT.fps
      || JSON.stringify(spec.footPoint) !== JSON.stringify(expectedFoot)
      || spec.characterPreviewScale !== APPROVED_OPERATOR_ATLAS_CONTRACT.sourcePreviewScale
      || spec.movementPixelSnap !== true
      || spec.bodySplit !== false
    ) {
      throw new Error('approved V2.1 spec mismatch');
    }
    if (
      anchors.schemaVersion !== '2.1'
      || JSON.stringify(anchors.directions) !== JSON.stringify(expectedDirections)
      || anchors.framesPerDirection !== APPROVED_OPERATOR_ATLAS_CONTRACT.framesPerDirection
      || JSON.stringify(anchors.footPoint) !== JSON.stringify(expectedFoot)
      || !anchors.coordinateSpace?.includes('128x128 integer pixels')
      || expectedDirections.some(direction => anchors.frames?.[direction]?.length !== APPROVED_OPERATOR_ATLAS_CONTRACT.framesPerDirection)
    ) {
      throw new Error('approved V2.1 elbow anchor contract mismatch');
    }
    if (
      approval.status !== ART_GATE
      || approval.approvedVersion !== APPROVED_OPERATOR_ATLAS_CONTRACT.approvedVersion
      || JSON.stringify(approval.runtimeContract?.cell) !== JSON.stringify(expectedCell)
      || JSON.stringify(approval.runtimeContract?.directions) !== JSON.stringify(expectedDirections)
      || approval.runtimeContract?.runtimeScale !== APPROVED_OPERATOR_ATLAS_CONTRACT.runtimeScale
      || approval.restrictions?.runtimeBody !== 'elbow_body_core_only'
      || approval.restrictions.fullbodySourceRuntimeAllowed !== false
      || approval.restrictions.attackArmsHandsWeaponsIncluded !== false
      || approval.restrictions.candidateOrRejectedAssetsAllowed !== false
      || approval.restrictions.threeD128ProofAllowed !== false
      || approval.restrictions.approvedPixelsFrozen !== true
    ) {
      throw new Error('PM ART_APPROVED manifest or runtime restrictions mismatch');
    }
    if (
      contract.threeDBranch?.status !== THREE_D_GATE
      || contract.threeDBranch.runtimeEntry !== null
      || contract.threeDBranch.formalPixelAsset !== false
      || contract.threeDBranch.proof128IsFormalPixelAsset !== false
      || contract.threeDBranch.mixWithPixelAtlas !== false
    ) {
      throw new Error('3D V2 must remain an unloaded TECH_PROOF_ONLY branch');
    }
  }

  private loadJson(path: string): Promise<JsonAsset> {
    return new Promise((resolve, reject) => {
      resources.load(path, JsonAsset, (error, asset) => error ? reject(error) : resolve(asset));
    });
  }

  private loadSpriteFrame(path: string): Promise<SpriteFrame> {
    return new Promise((resolve, reject) => {
      resources.load(path, SpriteFrame, (error, asset) => error ? reject(error) : resolve(asset));
    });
  }

  private loadTexture(path: string): Promise<Texture2D> {
    return new Promise((resolve, reject) => {
      resources.load(`${path}/texture`, Texture2D, (error, asset) => error || !asset ? reject(error ?? new Error(`Missing texture: ${path}`)) : resolve(asset));
    });
  }

  private sliceOperatorTexture(texture: Texture2D): SpriteFrame[][] {
    const { cellWidth, cellHeight, framesPerDirection, directionCount } = APPROVED_OPERATOR_ATLAS_CONTRACT;
    if (texture.width !== cellWidth * framesPerDirection || texture.height !== cellHeight * directionCount) {
      throw new Error(`approved operator atlas size mismatch: ${texture.width}x${texture.height}`);
    }
    const rows: SpriteFrame[][] = [];
    for (let row = 0; row < directionCount; row += 1) {
      const frames: SpriteFrame[] = [];
      for (let column = 0; column < framesPerDirection; column += 1) {
        const frame = new SpriteFrame();
        frame.reset({
          texture,
          rect: new Rect(column * cellWidth, row * cellHeight, cellWidth, cellHeight),
          originalSize: new Size(cellWidth, cellHeight),
          offset: Vec2.ZERO,
          isRotate: false,
        }, true);
        frame.packable = false;
        frames.push(frame);
      }
      rows.push(frames);
    }
    return rows;
  }

  private applyOperatorFrame(): void {
    const frame = this.operatorFrames[this.animationClock.frameRow()]?.[this.animationClock.frameColumn()];
    if (frame) this.operatorSprite.spriteFrame = frame;
  }

  private publishCurrentQaState(): void {
    this.publishQaState({
      ready: this.assetsReady,
      roomId: this.currentRoomId ?? null,
      gate: ART_GATE,
      threeDGate: THREE_D_GATE,
      viewport: [VIEWPORT_WIDTH, VIEWPORT_HEIGHT],
      cameraMode: 'follow',
      position: [Math.round(this.logicalPosition.x), Math.round(this.logicalPosition.y)],
      hasDebugKeycard: this.hasDebugKeycard,
      collisionOverlay: this.showCollision,
      operatorAsset: APPROVED_OPERATOR_ATLAS_CONTRACT.assetPath,
      operatorVersion: APPROVED_OPERATOR_ATLAS_CONTRACT.approvedVersion,
      direction: this.animationClock.direction,
      directionName: APPROVED_OPERATOR_ATLAS_CONTRACT.directionOrder[this.animationClock.direction],
      walkFrame: this.animationClock.walkFrame,
      moving: this.operatorMoving,
      cell: [APPROVED_OPERATOR_ATLAS_CONTRACT.cellWidth, APPROVED_OPERATOR_ATLAS_CONTRACT.cellHeight],
      fps: APPROVED_OPERATOR_ATLAS_CONTRACT.fps,
      footAnchor: [APPROVED_OPERATOR_ATLAS_CONTRACT.footPoint[0], APPROVED_OPERATOR_ATLAS_CONTRACT.footPoint[1]],
      runtimeScale: APPROVED_OPERATOR_ATLAS_CONTRACT.runtimeScale,
      pixelSnap: APPROVED_OPERATOR_ATLAS_CONTRACT.pixelSnap,
      preserveWalkFrameOnDirectionChange: APPROVED_OPERATOR_ATLAS_CONTRACT.preserveWalkFrameOnDirectionChange,
      renderPosition: [Math.round(this.operatorNode.position.x), Math.round(this.operatorNode.position.y)],
      operatorMode: 'A_ART',
      dualVersionGate: this.dualContract?.status ?? 'SCENE_DUAL_VERSION_NOT_READY',
      bVersionStatus: this.dualContract?.versions?.B_Q_BRIDGE?.status ?? 'WAITING_Q_BRIDGE_PIPELINE_CANDIDATE_READY_AND_USER_APPROVED_Q_MASTER',
      collisionShape: 'foot_circle',
      collisionRadius: this.config?.probeRadius,
    });
  }

  private publishQaState(state: {
    ready: boolean;
    roomId: RoomId | null;
    gate: string;
    threeDGate: string;
    viewport: [number, number];
    cameraMode: 'follow';
    position?: [number, number];
    hasDebugKeycard?: boolean;
    collisionOverlay?: boolean;
    operatorAsset?: string;
    operatorVersion?: string;
    direction?: number;
    directionName?: string;
    walkFrame?: number;
    moving?: boolean;
    cell?: [number, number];
    fps?: number;
    footAnchor?: [number, number];
    runtimeScale?: number;
    pixelSnap?: boolean;
    preserveWalkFrameOnDirectionChange?: boolean;
    renderPosition?: [number, number];
    operatorMode?: 'A_ART';
    dualVersionGate?: string;
    bVersionStatus?: string;
    collisionShape?: 'foot_circle';
    collisionRadius?: number;
    error?: string;
  }): void {
    (globalThis as unknown as { __PRESIDENT_OFFICE_R2_QA__?: typeof state }).__PRESIDENT_OFFICE_R2_QA__ = state;
  }
}
