# ImageGen Prompt Record — 威龙 Prototype 1

> **REJECTED_BAD_CASE / 仅供失败取证。** 本提示记录采用了已拒收的露娜 Prototype 5 动作参考，并服务于上下半身分离生成流程。禁止执行、复制、改写或作为任何生图、img2img、训练与迭代输入；新威龙必须从完整人物、完整骨架的统一姿态解算重新开始。

执行模式：内置 imagegen；每个方向独立生成一张 `4×2` 八帧动作源，绿幕移除后由本地构建脚本统一身份、调色板、硬 alpha 和锚点。

## 输入角色

1. 对应方向的威龙·凌霄戍卫透明 3D/正交渲染：只锁定身份、服装、头盔、肩甲、胸甲、背具和朝向。
2. `operator_weilong_lingxiao_3dref_elbow_core_8dir_128.png`：锁定 Q 版比例、正式像素身份和肘部模块化切分。
3. 露娜 Prototype 5 对应方向的八帧动作参考：只提供 CONTACT/DOWN/PASS/UP 的左右脚循环和图集排布，禁止复制露娜身份或服装。

## 核心提示

```text
Create exactly one 4 columns × 2 rows sheet containing eight consecutive run-cycle frames of the same 威龙·凌霄戍卫 at one fixed direction.
Phase order: CONTACT_A, DOWN_A, PASS_A, UP_A / CONTACT_B, DOWN_B, PASS_B, UP_B.
Use a genuine alternating left/right-foot run cycle with distinct hip, thigh, knee, shin and foot poses; frame 7 must flow into frame 0; do not fake motion with whole-character translation.
Keep the helmet, chest or rear armour, feather-like shoulder armour, backpack/jet system, body scale and direction identical across frames.
Preserve shoulders, full upper arms and elbow caps. Omit forearms, wrists, gloves and hands below both elbows. Exactly two upper arms; no duplicated rear limbs; no weapon.
Use crisp hand-authored chibi pixel art and a perfectly flat #00ff00 background with no grid, text, shadows, gradients or texture.
Avoid Luna traits, generic astronaut design, identity drift, extra limbs, full hands, direction changes, duplicated frames, resizing between frames and cropped feet.
```

新 `weilong_3d_pipeline` 母图在生成完成后加入最高精度审计清单；其写实降采样图明确排除为正式像素源。最终输出通过 `weilong_identity_3d_vs_pixel_audit_v1.png` 与新母图逐方向核对。
