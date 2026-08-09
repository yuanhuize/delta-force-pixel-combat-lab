# 总裁室 R2 × 威龙 V2.1 场景集成 QA

## 最终闸门

- 场景自验：`SCENE_INTEGRATION_QA_PASS`
- 像素角色：`ART_APPROVED / V2.1`
- 3D 分支：`3D_APPROVED_TECH_PROOF_ONLY`，无运行入口，不与像素图集混合
- 运行内容：批准的肘部身体核心；无攻击手臂、手、枪、攻击或换弹层

## 冻结资源与哈希

| 文件 | SHA-256 |
|---|---|
| `weilong_body_core_run_8dir_12f_v2_1.png` | `aeed19fe787a7355f4a362fb9d1fb556702a9692562950fc0991c3d64bd7de0b` |
| `weilong_elbow_anchors_8dir_12f_v2_1.json` | `9a59fa24f0c32da775416eafe57fcf4bc0dfa344b607923c8cca644ad598416d` |
| `spec_v2_1.json` | `14ced3c8c6259fc7905d1f1bd0efdc40ca14bc1478c732ddeba5ac67a7785fd8` |

静态闸门同时检查 1536×1024 图集尺寸、128×128 cell、方向顺序、12 帧、18fps、脚点 `[64,116]`、2×整数缩放、pixel-snap、nearest/no-mip 纹理元数据及禁止资源清单。

## Cocos 入口

- 启动场景：`assets/scenes/PresidentOfficeR2.scene`
- 场景与角色控制：`assets/scripts/PresidentOfficeR2Lab.ts`
- 动画时钟：`assets/scripts/ApprovedOperatorAtlasContract.ts`
- 正式角色资源：`assets/resources/weilong_v2_1/`
- Web 构建：`build/web-desktop/index.html`
- 本机打开：`./run-lab.command`

## 2026-08-09 实跑结果

- 1280×720 canvas；960×540 局部跟随视窗；地图保持 1×。
- 六房全部 `ready=true`：西走廊、东走廊、外厅、主厅、左刷卡房、右影院。
- 八方向顺序与批准 spec 一致，所有方向均显示合法的 `walkFrame 0–11`。
- 12 帧动画以 18fps 连续推进；采样覆盖 10 个不同帧值。
- 方向由 Right 切换到 UpRight 时，`walkFrame` 为 `5 → 5`，证明未重置相位。
- 渲染位置始终为整数，运行缩放固定为 2×。
- 左刷卡门：无卡阻挡，QA 卡授权后通过。
- 右影院开放门洞：可返回主厅。
- 主厅—外厅中央门：可往返。
- 外厅下墙保持封闭；左边界碰撞通过。
- Chrome `pageerror=0`、`console.error=0`、`console.warning=0`。

证据：

- `artifacts/president_office_r2/smoke-result.json`
- `artifacts/president_office_r2/operator_8dir/`
- `artifacts/president_office_r2/weilong_v2_1_8dir_qa.gif`
- `artifacts/president_office_r2/cocos-web-desktop-build-2026-08-09.log`

## 构建说明

Cocos Creator 3.8.8 无头进程仍会在完成后返回退出码 36，并在缓存引擎阶段记录子进程 `SIGTERM`；同一日志最终明确到达 `build Task (web-desktop) Finished`。最终 `index.html` 与 `settings.json` 均存在，且该实际构建已由 Chrome 完整加载并通过上述 smoke，因此以产物完整性和浏览器实跑作为构建成功依据。

## 已知限制

- 本轮没有攻击手臂、手、枪、攻击或换弹；不得从 `fullbody_source` 偷回完整手臂。
- 3D V2 仅为独立技术对照资料，未在此 Cocos 主场景建立入口。
- QA 的数字键切房、K 键钥匙卡和 C 键碰撞层属于测试工具，不是正式玩法 UI。
