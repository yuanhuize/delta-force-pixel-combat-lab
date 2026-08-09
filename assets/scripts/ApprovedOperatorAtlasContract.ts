export const APPROVED_OPERATOR_ATLAS_CONTRACT = Object.freeze({
  approvalStatus: 'ART_APPROVED',
  approvedVersion: 'V2.1',
  assetPath: 'weilong_v2_1/weilong_body_core_run_8dir_12f_v2_1',
  anchorsPath: 'weilong_v2_1/weilong_elbow_anchors_8dir_12f_v2_1',
  specPath: 'weilong_v2_1/spec_v2_1',
  approvalManifestPath: 'weilong_v2_1/ART_APPROVAL_MANIFEST',
  cellWidth: 128,
  cellHeight: 128,
  directionOrder: ['Down', 'DownRight', 'Right', 'UpRight', 'Up', 'UpLeft', 'Left', 'DownLeft'] as const,
  directionCount: 8,
  framesPerDirection: 12,
  fps: 18,
  footPoint: [64, 116] as const,
  sourcePreviewScale: 2,
  runtimeScale: 1,
  preserveWalkFrameOnDirectionChange: true,
  pixelSnap: true,
  allowedRuntimeScales: [1] as const,
});

/**
 * Animation clock for the frozen ART_APPROVED V2.1 atlas.
 * Direction changes intentionally do not reset walkFrame.
 */
export class ApprovedOperatorAnimationClock {
  readonly fps = APPROVED_OPERATOR_ATLAS_CONTRACT.fps;
  readonly frameCount = APPROVED_OPERATOR_ATLAS_CONTRACT.framesPerDirection;
  direction = 0;
  walkFrame = 0;
  private elapsed = 0;

  setDirection(direction: number): void {
    this.direction = ((direction % 8) + 8) % 8;
  }

  update(dt: number, moving: boolean): void {
    if (!moving) return;
    this.elapsed += dt;
    this.walkFrame = Math.floor(this.elapsed * this.fps) % this.frameCount;
  }

  frameColumn(): number {
    return this.walkFrame;
  }

  frameRow(): number {
    return this.direction;
  }

  static assertIntegerScale(scale: number): void {
    if (!Number.isInteger(scale) || !APPROVED_OPERATOR_ATLAS_CONTRACT.allowedRuntimeScales.includes(scale as 1)) {
      throw new Error(`Operator atlas scale must be an allowed integer; received ${scale}`);
    }
  }
}
