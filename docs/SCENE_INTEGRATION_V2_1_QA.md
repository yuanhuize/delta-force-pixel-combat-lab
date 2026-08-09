# 总裁室 R2 × 威龙 V2.1 场景集成 QA

## 当前闸门

- A 版场景自验：`A_SCALE1_SCENE_QA_PASS_B_Q_BRIDGE_LOCKED`
- A 版可达性：`A_SCALE1_FULL_REACHABILITY_PASS_B_Q_BRIDGE_LOCKED`
- 像素角色：`ART_APPROVED / V2.1`
- 双版本交付：`SCENE_DUAL_VERSION_NOT_READY`
- 第二版本：等待 `Q_BRIDGE_PIPELINE_CANDIDATE_READY` 与用户批准 Q 版母版

当前运行内容只有批准的肘部身体核心；无攻击手臂、手、枪、攻击或换弹层。原比例 3D 直接降采样已从正式 Cocos 资源撤出，不可作为第二版本。

## 冻结资源与哈希

| 文件 | SHA-256 |
|---|---|
| `weilong_body_core_run_8dir_12f_v2_1.png` | `aeed19fe787a7355f4a362fb9d1fb556702a9692562950fc0991c3d64bd7de0b` |
| `weilong_elbow_anchors_8dir_12f_v2_1.json` | `9a59fa24f0c32da775416eafe57fcf4bc0dfa344b607923c8cca644ad598416d` |
| `spec_v2_1.json` | `14ced3c8c6259fc7905d1f1bd0efdc40ca14bc1478c732ddeba5ac67a7785fd8` |

静态闸门检查 1536×1024 图集、128×128 cell、方向顺序、12 帧、18fps、脚点 `[64,116]`、运行时 1×、pixel-snap、nearest/no-mip 纹理元数据和禁止资源。来源 spec 中的 2×只作为上游预览比例记录，不再用于六房运行时。

## Cocos 入口

- 启动场景：`assets/scenes/PresidentOfficeR2.scene`
- 场景与角色控制：`assets/scripts/PresidentOfficeR2Lab.ts`
- 动画时钟：`assets/scripts/ApprovedOperatorAtlasContract.ts`
- 正式角色资源：`assets/resources/weilong_v2_1/`
- 双版本锁定契约：`assets/resources/president_office_r2/operator_contract/dual_version_runtime_contract_r1.json`
- Web 构建：`build/web-desktop/index.html`

## 2026-08-09 实跑结果

- 1280×720 canvas；960×540 局部跟随视窗；地图保持 1×。
- A 版运行缩放固定 1×，可见高度约 86–92px；nearest、pixel-snap、脚点 `[64,116]`。
- 八方向顺序与批准 spec 一致；12 帧动画以 18fps 连续推进。
- Right → UpRight 的 `walkFrame` 为 `5 → 5`，证明转向没有重置相位。
- 碰撞按脚底半径 16px 圆形探针判断，不使用整张 128 图集阻挡。
- 外厅真实轨迹：`x 67–1603`、`y 84–861`；宽覆盖 `96.79%`，高覆盖 `93.05%`。
- 主厅真实轨迹：`x 45–1619`、`y 46–882`；宽覆盖 `97.04%`，高覆盖 `94.46%`。
- 正常门路依次验证 D1、D1_BACK、D2、D2_BACK、D3、D4、D4_BACK、O1、O1_BACK，六房全部到达；未用 1–6 代替此可达性结论。
- 左刷卡门无卡阻挡、QA 卡授权后通过；右影院门洞和主厅—外厅中央门可往返。
- 浏览器 `pageerror=0`、`console.error=0`、`console.warning=0`。
- 按 V 只显示 Q Bridge／用户批准闸门提示，角色仍保持 `A_ART`。

证据：

- `artifacts/president_office_r2/smoke-result.json`
- `artifacts/president_office_r2/reachability-data-audit.json`
- `artifacts/president_office_r2/reachability-browser-result.json`
- `artifacts/president_office_r2/a_scale1_outside_full_reach.png`
- `artifacts/president_office_r2/a_scale1_main_full_reach.png`
- `artifacts/president_office_r2/iab_a_scale1_scene.png`
- `artifacts/president_office_r2/iab_q_bridge_gate_locked.png`

## 构建说明

Cocos Creator 3.8.8 日志最终到达 `build Task (web-desktop) Finished`。最终 `index.html` 与 `settings.json` 均存在，并由浏览器重新加载该构建完成实跑。

## 已知限制

- 本轮没有攻击手臂、手、枪、攻击或换弹；不得从 `fullbody_source` 偷回完整手臂。
- 第二版本尚未接入；必须先获得 Q Bridge 管线候选，再由用户批准 Q 版母版。
- QA 的数字键切房、K 键钥匙卡和 C 键碰撞层属于测试工具，不是正式玩法 UI。
