import {
  _decorator,
  Color,
  Component,
  EventKeyboard,
  EventMouse,
  Graphics,
  HorizontalTextAlignment,
  input,
  Input,
  KeyCode,
  Label,
  Node,
  Rect,
  resources,
  Size,
  Sprite,
  SpriteFrame,
  Texture2D,
  UITransform,
  Vec2,
  Vec3,
  VerticalTextAlignment,
} from 'cc';

const { ccclass } = _decorator;

type WeaponMode = 'body' | 'bow' | 'rifle';
type ActionState = 'idle' | 'bowAttack' | 'rifleFire' | 'reload';
type FrameGrid = SpriteFrame[][];

const CELL = 128;
const VISUAL_SCALE = 2;
const BODY_CENTER_FROM_FOOT = 52;
const WALK_FRAMES = 4;
const WALK_FPS = 11;
const MOVE_SPEED = 145;
const DEAD_ZONE = 0.15;
const HYSTERESIS = Math.PI / 30; // 6 degrees beyond a direction boundary.
const RIFLE_ACTION_PHASES = 3;

const DIR_NAMES = ['下/正面', '右下/右前', '右/右侧', '右上/右后', '上/背面', '左上/左后', '左/左侧', '左下/左前'];
const DIR_ANGLES = [
  -Math.PI / 2,
  -Math.PI / 4,
  0,
  Math.PI / 4,
  Math.PI / 2,
  Math.PI * 3 / 4,
  Math.PI,
  -Math.PI * 3 / 4,
];

const COLORS = {
  background: new Color(8, 14, 18, 255),
  panel: new Color(12, 25, 30, 255),
  grid: new Color(23, 42, 47, 170),
  border: new Color(52, 112, 110, 255),
  text: new Color(222, 239, 234, 255),
  muted: new Color(126, 184, 177, 255),
  cyan: new Color(61, 219, 205, 255),
  orange: new Color(241, 145, 74, 255),
  warning: new Color(255, 184, 78, 255),
};

const TEXTURES = {
  body: ['luna/luna_body_run_8dir_4f_v3', WALK_FRAMES, 8],
  bowWeapon: ['luna/luna_bow_weapon_8dir_5phase', 5, 8],
  bowTrigger: ['luna/luna_bow_trigger_8dir_5phase', 5, 8],
  bowSupport: ['luna/luna_bow_support_8dir_5phase', 5, 8],
  bowString: ['luna/luna_bow_string_8dir_5phase', 5, 8],
  bowProjectile: ['luna/luna_bow_projectile_8dir_5phase', 5, 8],
  rifleWeaponBack: ['luna/luna_rifle_weapon_back_8dir_3phase_v3', 3, 8],
  rifleWeaponFront: ['luna/luna_rifle_weapon_front_8dir_3phase_v3', 3, 8],
  rifleTriggerArmHand: ['luna/luna_rifle_trigger_arm_hand_8dir_4walk_3phase_v3', WALK_FRAMES * RIFLE_ACTION_PHASES, 8],
  rifleSupportArmHand: ['luna/luna_rifle_support_arm_hand_8dir_4walk_3phase_v3', WALK_FRAMES * RIFLE_ACTION_PHASES, 8],
  rifleMagazine: ['luna/luna_rifle_magazine_8dir_3phase_v3', 3, 8],
  rifleMuzzle: ['luna/luna_rifle_muzzle_8dir_3phase_v3', 3, 8],
  reloadWeapon: ['luna/luna_rifle_reload_weapon_8dir_7f', 7, 8],
  reloadWeaponBack: ['luna/luna_rifle_weapon_back_reload_8dir_7f_v2', 7, 8],
  reloadWeaponFront: ['luna/luna_rifle_weapon_front_reload_8dir_7f_v2', 7, 8],
  reloadTrigger: ['luna/luna_rifle_reload_trigger_8dir_7f', 7, 8],
  reloadSupport: ['luna/luna_rifle_reload_support_8dir_7f', 7, 8],
  reloadMagazine: ['luna/luna_rifle_reload_magazine_8dir_7f', 7, 8],
} as const;

@ccclass('LunaRigLab')
export class LunaRigLab extends Component {
  private canvasTransform!: UITransform;
  private lunaRoot!: Node;
  private visualRoot!: Node;
  private bodyNode!: Node;
  private weaponBackNode!: Node;
  private weaponNode!: Node;
  private stringNode!: Node;
  private triggerNode!: Node;
  private supportNode!: Node;
  private magazineNode!: Node;
  private projectileNode!: Node;
  private muzzleNode!: Node;

  private bodySprite!: Sprite;
  private weaponBackSprite!: Sprite;
  private weaponSprite!: Sprite;
  private stringSprite!: Sprite;
  private triggerSprite!: Sprite;
  private supportSprite!: Sprite;
  private magazineSprite!: Sprite;
  private projectileSprite!: Sprite;
  private muzzleSprite!: Sprite;

  private titleLabel!: Label;
  private statusLabel!: Label;
  private helpLabel!: Label;
  private noteLabel!: Label;

  private frames: Record<string, FrameGrid> = {};
  private pressed = new Set<KeyCode>();
  private logicalPosition = new Vec2(0, -30);
  private mouseAim = new Vec2(0, -1);
  private direction = 0;
  private walkClock = 0;
  private walkFrame = 0;
  private weaponMode: WeaponMode = 'rifle';
  private action: ActionState = 'idle';
  private actionTime = 0;
  private actionFrame = 0;
  private aimWithMouse = false;
  private autoRotate = false;
  private autoAngle = -Math.PI / 2;
  private assetsReady = false;

  start(): void {
    this.canvasTransform = this.node.getComponent(UITransform)!;
    this.createStage();
    this.bindInput();
    void this.loadAllAssets();
  }

  onDestroy(): void {
    input.off(Input.EventType.KEY_DOWN, this.onKeyDown, this);
    input.off(Input.EventType.KEY_UP, this.onKeyUp, this);
    input.off(Input.EventType.MOUSE_MOVE, this.onMouseMove, this);
    input.off(Input.EventType.MOUSE_DOWN, this.onMouseDown, this);
  }

  update(dt: number): void {
    if (!this.assetsReady) return;

    const movement = this.movementVector();
    const moving = movement.lengthSqr() > DEAD_ZONE * DEAD_ZONE;
    if (moving) {
      movement.normalize();
      this.logicalPosition.x += movement.x * MOVE_SPEED * dt;
      this.logicalPosition.y += movement.y * MOVE_SPEED * dt;
      this.logicalPosition.x = Math.max(-500, Math.min(500, this.logicalPosition.x));
      this.logicalPosition.y = Math.max(-220, Math.min(210, this.logicalPosition.y));
      if (!this.aimWithMouse && !this.autoRotate) {
        this.direction = this.resolveDirection(movement, this.direction);
      }
    }

    // Auto-rotate is also the hands-free art-review mode: it advances the
    // regenerated run cycle without translating the root across the screen.
    if (moving || this.autoRotate) {
      this.walkClock += dt;
      this.walkFrame = Math.floor(this.walkClock * WALK_FPS) % WALK_FRAMES;
    } else {
      this.walkFrame = 0;
      this.walkClock = 0;
    }

    if (this.autoRotate) {
      this.autoAngle += dt * 0.9;
      const autoAim = new Vec2(Math.cos(this.autoAngle), Math.sin(this.autoAngle));
      this.direction = this.resolveDirection(autoAim, this.direction);
    } else if (this.aimWithMouse) {
      this.direction = this.resolveDirection(this.mouseAim, this.direction);
    }

    this.advanceAction(dt);
    this.lunaRoot.setPosition(Math.round(this.logicalPosition.x), Math.round(this.logicalPosition.y), 0);
    this.applyFrame();
    this.updateStatus(moving);
  }

  private createStage(): void {
    const backgroundNode = new Node('PrototypeBackground');
    backgroundNode.layer = this.node.layer;
    backgroundNode.addComponent(UITransform).setContentSize(1280, 720);
    this.node.addChild(backgroundNode);
    const graphics = backgroundNode.addComponent(Graphics);
    graphics.fillColor = COLORS.background;
    graphics.fillRect(-640, -360, 1280, 720);
    graphics.strokeColor = COLORS.grid;
    graphics.lineWidth = 1;
    for (let x = -640; x <= 640; x += 32) {
      graphics.moveTo(x, -270);
      graphics.lineTo(x, 250);
    }
    for (let y = -270; y <= 250; y += 32) {
      graphics.moveTo(-620, y);
      graphics.lineTo(620, y);
    }
    graphics.stroke();
    graphics.fillColor = COLORS.panel;
    graphics.roundRect(-620, 262, 1240, 78, 8);
    graphics.fill();
    graphics.strokeColor = COLORS.border;
    graphics.roundRect(-620, 262, 1240, 78, 8);
    graphics.stroke();

    this.titleLabel = this.createLabel('Title', 0, 318, 20, COLORS.text, 1200);
    this.titleLabel.string = '露娜 · Legacy Prototype 3（仅技术诊断，不是正式美术）';
    this.statusLabel = this.createLabel('Status', 0, 282, 15, COLORS.cyan, 1200);
    this.statusLabel.string = '正在导入原生像素图层……';
    this.helpLabel = this.createLabel('Help', 0, -305, 14, COLORS.text, 1220);
    this.helpLabel.string = 'WASD/方向键：移动　鼠标：瞄准　Q：移动/鼠标朝向　0：纯跑动　1：弓　2：步枪　点击/Space：攻击　R：换弹　T：自动八方向';
    this.noteLabel = this.createLabel('Note', 0, -334, 12, COLORS.muted, 1220);
    this.noteLabel.string = 'Prototype 4/5 已 REJECTED · 当前仅保留旧版运行诊断 · 禁止作为美术基线';

    this.lunaRoot = new Node('LunaRoot');
    this.lunaRoot.layer = this.node.layer;
    this.lunaRoot.setPosition(0, -30, 0);
    this.node.addChild(this.lunaRoot);

    this.visualRoot = new Node('VisualRoot');
    this.visualRoot.layer = this.node.layer;
    this.visualRoot.setScale(VISUAL_SCALE, VISUAL_SCALE, 1);
    this.lunaRoot.addChild(this.visualRoot);

    const shadowNode = new Node('Shadow');
    shadowNode.layer = this.node.layer;
    this.visualRoot.addChild(shadowNode);
    const shadow = shadowNode.addComponent(Graphics);
    shadow.fillColor = new Color(3, 7, 9, 170);
    shadow.ellipse(0, -3, 25, 5);
    shadow.fill();

    [this.bodyNode, this.bodySprite] = this.createSpriteNode('Body');
    [this.weaponBackNode, this.weaponBackSprite] = this.createSpriteNode('WeaponStockBehindBody');
    [this.weaponNode, this.weaponSprite] = this.createSpriteNode('WeaponReceiverAndBarrel');
    [this.stringNode, this.stringSprite] = this.createSpriteNode('BowString');
    [this.triggerNode, this.triggerSprite] = this.createSpriteNode('TriggerOrStringHand');
    [this.supportNode, this.supportSprite] = this.createSpriteNode('SupportOrGripHand');
    [this.magazineNode, this.magazineSprite] = this.createSpriteNode('Magazine');
    [this.projectileNode, this.projectileSprite] = this.createSpriteNode('Arrow');
    [this.muzzleNode, this.muzzleSprite] = this.createSpriteNode('MuzzleFX');
  }

  private createSpriteNode(name: string): [Node, Sprite] {
    const node = new Node(name);
    node.layer = this.node.layer;
    node.setPosition(0, BODY_CENTER_FROM_FOOT, 0);
    const transform = node.addComponent(UITransform);
    transform.setContentSize(CELL, CELL);
    transform.setAnchorPoint(0.5, 0.5);
    const sprite = node.addComponent(Sprite);
    sprite.sizeMode = Sprite.SizeMode.CUSTOM;
    sprite.trim = false;
    this.visualRoot.addChild(node);
    return [node, sprite];
  }

  private createLabel(name: string, x: number, y: number, size: number, color: Color, width: number): Label {
    const node = new Node(name);
    node.layer = this.node.layer;
    node.setPosition(x, y, 0);
    const transform = node.addComponent(UITransform);
    transform.setContentSize(width, size + 12);
    const label = node.addComponent(Label);
    label.fontSize = size;
    label.lineHeight = size + 4;
    label.color = color;
    label.horizontalAlign = HorizontalTextAlignment.CENTER;
    label.verticalAlign = VerticalTextAlignment.CENTER;
    this.node.addChild(node);
    return label;
  }

  private bindInput(): void {
    input.on(Input.EventType.KEY_DOWN, this.onKeyDown, this);
    input.on(Input.EventType.KEY_UP, this.onKeyUp, this);
    input.on(Input.EventType.MOUSE_MOVE, this.onMouseMove, this);
    input.on(Input.EventType.MOUSE_DOWN, this.onMouseDown, this);
  }

  private onKeyDown(event: EventKeyboard): void {
    this.pressed.add(event.keyCode);
    if (event.keyCode === KeyCode.DIGIT_0) {
      this.weaponMode = 'body';
      this.cancelAction();
    } else if (event.keyCode === KeyCode.DIGIT_1) {
      this.weaponMode = 'bow';
      this.cancelAction();
    } else if (event.keyCode === KeyCode.DIGIT_2) {
      this.weaponMode = 'rifle';
      this.cancelAction();
    } else if (event.keyCode === KeyCode.KEY_Q) {
      this.aimWithMouse = !this.aimWithMouse;
      this.autoRotate = false;
    } else if (event.keyCode === KeyCode.KEY_T) {
      this.autoRotate = !this.autoRotate;
      this.autoAngle = DIR_ANGLES[this.direction];
    } else if (event.keyCode === KeyCode.SPACE) {
      this.attack();
    } else if (event.keyCode === KeyCode.KEY_R && this.weaponMode === 'rifle') {
      this.action = 'reload';
      this.actionTime = 0;
      this.actionFrame = 0;
    }
  }

  private onKeyUp(event: EventKeyboard): void {
    this.pressed.delete(event.keyCode);
  }

  private onMouseMove(event: EventMouse): void {
    const screen = event.getUILocation();
    const local = this.canvasTransform.convertToNodeSpaceAR(new Vec3(screen.x, screen.y, 0));
    const deltaX = local.x - this.logicalPosition.x;
    const deltaY = local.y - this.logicalPosition.y;
    const length = Math.hypot(deltaX, deltaY);
    if (length > 18) {
      this.mouseAim.set(deltaX / length, deltaY / length);
    }
  }

  private onMouseDown(): void {
    this.attack();
  }

  private movementVector(): Vec2 {
    let x = 0;
    let y = 0;
    if (this.pressed.has(KeyCode.KEY_A) || this.pressed.has(KeyCode.ARROW_LEFT)) x -= 1;
    if (this.pressed.has(KeyCode.KEY_D) || this.pressed.has(KeyCode.ARROW_RIGHT)) x += 1;
    if (this.pressed.has(KeyCode.KEY_S) || this.pressed.has(KeyCode.ARROW_DOWN)) y -= 1;
    if (this.pressed.has(KeyCode.KEY_W) || this.pressed.has(KeyCode.ARROW_UP)) y += 1;
    return new Vec2(x, y);
  }

  private attack(): void {
    if (!this.assetsReady || this.action === 'reload' || this.weaponMode === 'body') return;
    this.action = this.weaponMode === 'bow' ? 'bowAttack' : 'rifleFire';
    this.actionTime = 0;
    this.actionFrame = 0;
  }

  private cancelAction(): void {
    this.action = 'idle';
    this.actionTime = 0;
    this.actionFrame = 0;
  }

  private advanceAction(dt: number): void {
    if (this.action === 'idle') {
      this.actionFrame = 0;
      return;
    }
    this.actionTime += dt;
    if (this.action === 'bowAttack') {
      const ends = [0.08, 0.18, 0.29, 0.37, 0.49];
      this.actionFrame = ends.findIndex((value) => this.actionTime < value);
      if (this.actionFrame < 0) this.cancelAction();
    } else if (this.action === 'rifleFire') {
      if (this.actionTime < 0.06) this.actionFrame = 1;
      else if (this.actionTime < 0.17) this.actionFrame = 2;
      else this.cancelAction();
    } else if (this.action === 'reload') {
      this.actionFrame = Math.floor(this.actionTime / 0.13);
      if (this.actionFrame >= 7) this.cancelAction();
    }
  }

  private resolveDirection(vector: Vec2, current: number): number {
    if (vector.lengthSqr() < DEAD_ZONE * DEAD_ZONE) return current;
    const angle = Math.atan2(vector.y, vector.x);
    let best = current;
    let bestDistance = Number.POSITIVE_INFINITY;
    for (let index = 0; index < DIR_ANGLES.length; index += 1) {
      const distance = Math.abs(this.angleDelta(angle, DIR_ANGLES[index]));
      if (distance < bestDistance) {
        bestDistance = distance;
        best = index;
      }
    }
    if (best === current) return current;
    const currentDistance = Math.abs(this.angleDelta(angle, DIR_ANGLES[current]));
    return currentDistance > Math.PI / 8 + HYSTERESIS ? best : current;
  }

  private angleDelta(a: number, b: number): number {
    return Math.atan2(Math.sin(a - b), Math.cos(a - b));
  }

  private applyFrame(): void {
    this.bodySprite.spriteFrame = this.frames.body[this.direction][this.walkFrame];
    const rear = this.direction >= 3 && this.direction <= 5;
    this.applyLayering(rear);

    if (this.weaponMode === 'body') {
      this.weaponBackNode.active = false;
      this.weaponNode.active = false;
      this.triggerNode.active = false;
      this.supportNode.active = false;
      this.magazineNode.active = false;
      this.stringNode.active = false;
      this.projectileNode.active = false;
      this.muzzleNode.active = false;
      return;
    }

    if (this.weaponMode === 'bow') {
      const phase = this.action === 'bowAttack' ? this.actionFrame : 0;
      this.weaponSprite.spriteFrame = this.frames.bowWeapon[this.direction][phase];
      this.triggerSprite.spriteFrame = this.frames.bowTrigger[this.direction][phase];
      this.supportSprite.spriteFrame = this.frames.bowSupport[this.direction][phase];
      this.stringSprite.spriteFrame = this.frames.bowString[this.direction][phase];
      this.projectileSprite.spriteFrame = this.frames.bowProjectile[this.direction][phase];
      this.weaponNode.active = true;
      this.weaponBackNode.active = false;
      this.triggerNode.active = true;
      this.supportNode.active = true;
      this.stringNode.active = true;
      this.projectileNode.active = true;
      this.magazineNode.active = false;
      this.muzzleNode.active = false;
      return;
    }

    if (this.action === 'reload') {
      const phase = Math.min(6, this.actionFrame);
      this.weaponBackSprite.spriteFrame = this.frames.reloadWeaponBack[this.direction][phase];
      this.weaponSprite.spriteFrame = this.frames.reloadWeaponFront[this.direction][phase];
      this.triggerSprite.spriteFrame = this.frames.reloadTrigger[this.direction][phase];
      this.supportSprite.spriteFrame = this.frames.reloadSupport[this.direction][phase];
      this.magazineSprite.spriteFrame = this.frames.reloadMagazine[this.direction][phase];
      this.muzzleNode.active = false;
    } else {
      const phase = this.action === 'rifleFire' ? this.actionFrame : 0;
      const armPhase = this.walkFrame * RIFLE_ACTION_PHASES + phase;
      this.weaponBackSprite.spriteFrame = this.frames.rifleWeaponBack[this.direction][phase];
      this.weaponSprite.spriteFrame = this.frames.rifleWeaponFront[this.direction][phase];
      this.triggerSprite.spriteFrame = this.frames.rifleTriggerArmHand[this.direction][armPhase];
      this.supportSprite.spriteFrame = this.frames.rifleSupportArmHand[this.direction][armPhase];
      this.magazineSprite.spriteFrame = this.frames.rifleMagazine[this.direction][phase];
      this.muzzleSprite.spriteFrame = this.frames.rifleMuzzle[this.direction][phase];
      this.muzzleNode.active = phase === 1;
    }
    this.weaponBackNode.active = true;
    this.weaponNode.active = true;
    this.triggerNode.active = true;
    this.supportNode.active = true;
    this.magazineNode.active = true;
    this.stringNode.active = false;
    this.projectileNode.active = false;
  }

  private applyLayering(rear: boolean): void {
    const rifleRearOrder = [this.weaponBackNode, this.weaponNode, this.magazineNode, this.supportNode, this.bodyNode, this.triggerNode, this.stringNode, this.projectileNode, this.muzzleNode];
    const rifleFrontOrder = [this.weaponBackNode, this.bodyNode, this.triggerNode, this.supportNode, this.weaponNode, this.magazineNode, this.stringNode, this.projectileNode, this.muzzleNode];
    const bowRearOrder = [this.weaponBackNode, this.weaponNode, this.stringNode, this.magazineNode, this.supportNode, this.bodyNode, this.triggerNode, this.projectileNode, this.muzzleNode];
    const bowFrontOrder = [this.weaponBackNode, this.bodyNode, this.stringNode, this.weaponNode, this.magazineNode, this.triggerNode, this.supportNode, this.projectileNode, this.muzzleNode];
    const rearOrder = this.weaponMode === 'rifle' ? rifleRearOrder : bowRearOrder;
    const frontOrder = this.weaponMode === 'rifle' ? rifleFrontOrder : bowFrontOrder;
    const order = rear ? rearOrder : frontOrder;
    order.forEach((node, index) => node.setSiblingIndex(index + 1)); // Keep shadow at index 0.
  }

  private updateStatus(moving: boolean): void {
    const mode = this.weaponMode === 'body' ? '纯跑动' : this.weaponMode === 'bow' ? '弓箭' : '突击步枪';
    const facingMode = this.autoRotate ? '自动八方向' : this.aimWithMouse ? '鼠标瞄准' : '移动方向';
    const action = this.action === 'idle' ? moving ? '移动' : '待机' : this.action;
    this.statusLabel.string = `方向 ${this.direction + 1}/8：${DIR_NAMES[this.direction]}　｜　武器：${mode}　｜　状态：${action}　｜　朝向来源：${facingMode}`;
    this.statusLabel.color = this.action === 'reload' ? COLORS.warning : this.weaponMode === 'bow' ? COLORS.orange : COLORS.cyan;
  }

  private async loadAllAssets(): Promise<void> {
    try {
      const entries = Object.entries(TEXTURES);
      await Promise.all(entries.map(async ([key, descriptor]) => {
        const [path, columns, rows] = descriptor;
        const texture = await this.loadTexture(path);
        texture.setFilters(Texture2D.Filter.NEAREST, Texture2D.Filter.NEAREST);
        texture.setMipFilter(Texture2D.Filter.NONE);
        texture.setWrapMode(Texture2D.WrapMode.CLAMP_TO_EDGE, Texture2D.WrapMode.CLAMP_TO_EDGE);
        this.frames[key] = this.sliceTexture(texture, columns, rows);
      }));
      this.assetsReady = true;
      this.applyFrame();
      this.statusLabel.string = '资源加载完成：WASD开始八方向移动';
    } catch (error) {
      this.statusLabel.string = `资源加载失败：${String(error)}`;
      this.statusLabel.color = COLORS.warning;
      console.error(error);
    }
  }

  private loadTexture(path: string): Promise<Texture2D> {
    return new Promise((resolve, reject) => {
      // Cocos imports every PNG as an ImageAsset plus a Texture2D sub-asset.
      // Loading the bare PNG path as Texture2D fails in a built resources bundle;
      // use the explicit sub-asset path so editor preview and web builds agree.
      resources.load(`${path}/texture`, Texture2D, (error, texture) => {
        if (error || !texture) reject(error ?? new Error(`Missing texture: ${path}`));
        else resolve(texture);
      });
    });
  }

  private sliceTexture(texture: Texture2D, columns: number, rows: number): FrameGrid {
    if (texture.width !== columns * CELL || texture.height !== rows * CELL) {
      throw new Error(`图集尺寸错误：${texture.name} = ${texture.width}×${texture.height}，预期 ${columns * CELL}×${rows * CELL}`);
    }
    const grid: FrameGrid = [];
    for (let row = 0; row < rows; row += 1) {
      const frames: SpriteFrame[] = [];
      for (let column = 0; column < columns; column += 1) {
        const frame = new SpriteFrame();
        frame.reset({
          texture,
          // SpriteFrame atlas rects use the image's top-left row order. Keeping
          // row === direction is what makes body/weapon/hands share one index.
          rect: new Rect(column * CELL, row * CELL, CELL, CELL),
          originalSize: new Size(CELL, CELL),
          offset: Vec2.ZERO,
          isRotate: false,
        }, true);
        frame.packable = false;
        frames.push(frame);
      }
      grid.push(frames);
    }
    return grid;
  }
}
