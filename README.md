# 三角洲行动像素战斗试验台 / Delta Force Pixel Combat Lab

这是 Cocos Creator 3.8.8 的总裁室 R2 六房可运行场景。每个房间是独立小地图，960×540 跟随视窗只显示当前房间局部；正式接入 `ART_APPROVED` 威龙 V2.1 肘部身体核心，可在场景内八方向连续移动、切房并与门和障碍碰撞。

- 场景集成：`SCENE_INTEGRATION_READY`（浏览器验收：`SCENE_INTEGRATION_QA_PASS`）
- 场景版本：`President Office R2 / six-room`
- 像素角色：`ART_APPROVED / Weilong V2.1 elbow body core`
- 3D 分支：`3D_APPROVED_TECH_PROOF_ONLY`；当前不加载、不混入像素主角色

## 正式运行资源

- 六张 R2 分房背景：`assets/resources/president_office_r2/rooms/`
- 房间拓扑：`assets/resources/president_office_r2/data/president_office_room_graph_r2.json`
- 房门、出生点、边界与障碍碰撞：`assets/resources/president_office_r2/data/president_office_rooms_r2.json`
- 角色运行时契约：`assets/resources/president_office_r2/operator_contract/approved_operator_atlas_contract_r1.json`
- 威龙 V2.1 正式运行资源：`assets/resources/weilong_v2_1/`
- PM 批准与哈希清单：`assets/resources/weilong_v2_1/ART_APPROVAL_MANIFEST.json`
- Cocos 启动场景：`assets/scenes/PresidentOfficeR2.scene`
- 六房与角色控制：`assets/scripts/PresidentOfficeR2Lab.ts`
- 动画时钟契约：`assets/scripts/ApprovedOperatorAtlasContract.ts`

运行时只加载 `weilong_body_core_run_8dir_12f_v2_1.png`、肘部挂点 JSON 和 V2.1 spec。`fullbody_source`、旧候选、拒收资产及 3D 128 proof 均未进入正式资源目录。

碰撞数据由 Blender/视频证据和锁定拓扑独立编辑，运行时不读取 PNG 像素反推碰撞。左侧房门为刷卡门，右侧影院为开放门洞，总裁室外厅下边封闭无门。

## 项目与上传目录（English / 中文）

GitHub 仓库根目录就是 `combat_lab/`（Combat Lab / 战斗试验台项目），不要上传它外侧的 `art_demos/`、本地缓存或大型 Blender 源文件。

| 文件夹 | 中文名称 | 用途与上传规则 |
| --- | --- | --- |
| `assets/` | Cocos 正式资源与源码 | 上传；只允许场景实际使用的批准资源、场景和 TypeScript 脚本 |
| `assets/resources/president_office_r2/` | 总裁室 R2 六房资源 | 上传；地图、房间拓扑、门、碰撞和角色契约 |
| `assets/resources/weilong_v2_1/` | 威龙 V2.1 正式运行资源 | 上传；仅 `ART_APPROVED` 身体核心、肘点、spec 和批准清单 |
| `bad_cases_失败案例/` | Bad Cases / 失败案例档案 | 上传；与运行时隔离，只供人工取证复盘 |
| `docs/` | Documentation / 项目与 QA 文档 | 上传；场景验收、资源哈希和已知限制 |
| `scripts/` | Build & QA Scripts / 构建与质检脚本 | 上传；运行时闸门、浏览器 smoke 和发布打包 |
| `build-configs/` | Build Configurations / 构建配置 | 上传；Web Desktop 构建入口 |
| `build/` | Local Build / 本地构建产物 | 不提交源码仓；由 Cocos 重新生成 |
| `release/` | Release Attachments / 发布附件 | 不提交源码仓；ZIP 与 `.sha256` 上传到 GitHub Release |
| `library/`、`temp/`、`profiles/`、`artifacts/` | Cache & QA Output / 缓存与本地 QA 输出 | 不提交；均可由源码和脚本重建 |

## 打开与运行

1. 用 Cocos Creator 3.8.8 打开 `combat_lab`。
2. 打开 `assets/scenes/PresidentOfficeR2.scene`。
3. 点击预览，或使用 `build-configs/web-desktop.json` 构建 Web Desktop。

```bash
COCOS_CREATOR='/Applications/Cocos/Creator/3.8.8/CocosCreator.app/Contents/MacOS/CocosCreator'
"$COCOS_CREATOR" --project "$(pwd)" --build "configPath=$(pwd)/build-configs/web-desktop.json"
```

构建前执行 `npm run verify:runtime-gate`，检查六房资源、角色哈希、图集尺寸、nearest 元数据及禁止资源。构建后执行 `npm run test:smoke`，检查六房切换、八方向动画、转向相位、房门、碰撞以及浏览器零 error/warn。

## 操作

- `WASD` / 方向键：八方向移动威龙。
- `Shift`：快速移动。
- `E` / `Space`：交互房门。
- `K`：仅 QA 使用，授予/移除刷卡门钥匙卡。
- `C`：显示/隐藏独立碰撞层。
- `1–6`：QA 直达六个房间。
- `R`：回到当前房间出生点。

## 角色运行契约

- 方向：`Down, DownRight, Right, UpRight, Up, UpLeft, Left, DownLeft`
- 图集：128×128 cell，8 行×12 列，12 帧，18fps
- 脚点：`[64,116]`
- 显示：2×整数缩放、nearest、pixel-snap
- 变向：保留当前 `walkFrame`，不重置相位
- 内容：本轮只显示肘部身体核心；攻击手臂、手、枪、攻击和换弹尚未接入

## QA 证据

- 浏览器完整结果：`artifacts/president_office_r2/smoke-result.json`
- 八方向截图：`artifacts/president_office_r2/operator_8dir/`
- 八方向 GIF：`artifacts/president_office_r2/weilong_v2_1_8dir_qa.gif`
- Cocos 构建日志：`artifacts/president_office_r2/cocos-web-desktop-build-2026-08-09.log`
- 详细说明：`docs/SCENE_INTEGRATION_V2_1_QA.md`

## 禁止运行时素材

威龙 Prototype 1、威龙 test02、威龙 V1/V2 候选、露娜 Prototype 4/5、`fullbody_source` 和 3D 128 proof 不得位于正式运行资源目录或被场景加载。历史技术诊断件仅在 `bad_cases_失败案例/` 隔离保留。

失败案例包括用户要求保留的威龙 Prototype 1、露娜 Prototype 4/5，以及写实 PBR 直缩、共享变形笼 Q 化、五关键姿势＋正弦摆腿和上下半身分层合成四组威龙反例。所有条目均标记为 `REJECTED_BAD_CASE`、`forensic review only`，禁止游戏、生图、img2img、训练与迭代基线用途；详见 `bad_cases_失败案例/README.md` 和 `bad_cases_失败案例/registry.json`。

版本说明见 `CHANGELOG.md`，构建、校验和与 GitHub 发布流程见 `RELEASE.md`。
