# 威龙 Prototype 1 动作美术

版本：`weilong-prototype-1-eight-direction-eight-frame-run-rifle`

状态：`REJECTED_BAD_CASE`

本套素材采用“上半身身份锁定＋独立下半身动作合成”，违反
`ART_ASSET_GENERATION_STANDARD.md`。整套仅允许用于失败案例审计，禁止作为
游戏资源、正式预览、视觉/动作/训练参考、img2img 输入或后续迭代基线。

## 拒收状态

- 身体八方向八帧跑动：`REJECTED_BAD_CASE`。
- 突击步枪 AIM/FIRE/RECOVER 分层：`REJECTED_BAD_CASE`。
- 七帧换弹分层：`REJECTED_BAD_CASE`。
- Cocos 运行时绑定：禁止。

## 身份与技术基线

- 最高精度身份和几何来源：`../weilong_3d_pipeline/weilong_8dir_master_preview.png`、`../weilong_3d_pipeline/turnaround_master/` 和两份 packed Blender 母版。
- 正式像素身份基线：`../character_batch_v1/body_core_v4_3d_ref/atlas/operator_weilong_lingxiao_3dref_elbow_core_8dir_128.png`。
- `weilong_8dir_game_pixel_preview.png` 与 `weilong_8dir_game_128_atlas.png` 只参与轮廓审查，未直接进入正式像素美术。
- 露娜 Prototype 5 只提供 128px 格式、八方向顺序、八帧动作相位、枪械分层和 z-order 契约。

## 像素约束

- 单格 `128×128`，脚底锚点 `(64,116)`。
- 透明硬 alpha，仅 `0/255`。
- 全部正式图层共用一套不超过 32 色的固定调色板，无抖动。
- 最近邻缩放；无方向独立缩放、旋转插值或抗锯齿。
- 身体保留肩部、完整上臂和肘部；前臂、手腕、双手在独立手臂层。

## 重建禁令

归档脚本已设置执行阻断，不得重建或恢复本套成果。后续威龙必须从完整 3D 人物、
完整骨架或完整人物逐帧重绘重新开始，头—躯干—髋—膝—脚必须同姿态解算；
自然挂点分层也必须来自同骨架、同时间、同相机。
