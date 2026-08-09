# 更新日志

本文件记录 `combat_lab` 的用户可见变更。版本号遵循[语义化版本](https://semver.org/lang/zh-CN/)，并以 `package.json` 中的 `version` 字段为唯一版本来源。

## [Unreleased]

### Changed

- 将 ART_APPROVED 威龙 V2.1 在六房地图中的运行缩放从 2× 修正为 1×，保持 nearest、pixel-snap 与固定脚点。
- 角色碰撞明确为脚底半径 16px 圆形探针，不以 128×128 整张图集帧阻挡移动。
- 增加数据 BFS 与浏览器真实按键两层可达性 QA；外厅/主厅实际轨迹宽高覆盖均超过 93%，六房均经正常门路到达。
- 撤回原比例 3D 直接降采样的第二版本接入；双版本闸门改为等待 `Q_BRIDGE_PIPELINE_CANDIDATE_READY` 与用户批准 Q 版母版。

## [0.2.0] - 2026-08-09

### Added

- 正式接入总裁室 R2 六张分房地图和 `president_office_room_graph_r2.json`。
- 增加六房门切换、左侧刷卡门、外厅封闭下墙和显式碰撞/阻挡数据。
- 正式接入 `ART_APPROVED` 威龙 V2.1 肘部身体核心：128 cell、8 方向×12 帧、18fps、脚点 `[64,116]` 与 pixel-snap。
- 增加转向保持 `walkFrame` 的连续动画控制，以及角色在六房中的 WASD/方向键移动、碰撞与房门切换。
- 增加带正式资源 SHA-256、禁止引用、nearest 元数据检查的运行时闸门，以及六房/八方向 Web 烟雾测试和 GIF 证据。
- 归档威龙 Prototype 1（固定上半身＋独立下半身合成）与露娜 Prototype 4/5（保留上半身身份源＋独立下半身动作）的完整生成过程，并明确标记为仅供人工复盘的 `REJECTED_BAD_CASE`。
- 归档威龙 3D V1 写实/PBR 直缩、共享变形笼 Q 化、五关键姿势＋正弦摆腿、`weilong_pixel_actions_v2` 上下半身分层四组失败案例，附代表 PNG/GIF/JSON、脚本快照、源 `.blend` 哈希和禁止用途。
- 增加中英双语项目说明、GitHub 上传根目录和文件夹用途表。

### Changed

- 更新 PM 闸门：`WL_Tactical_Rifle_Run_V2` 仅标记为 `3D_APPROVED_TECH_PROOF_ONLY`，不作为正式像素素材或运行时主角色。
- Cocos 启动场景从露娜旧技术诊断页切换为 `PresidentOfficeR2.scene`。
- 威龙 test02 和露娜旧诊断素材退出 `assets/resources`，只在失败案例目录中隔离保留。
- `fullbody_source` 保持 QA/追溯用途，未进入 Cocos 正式运行时；攻击手臂、手和枪留待后续独立分层。
- 建立本地版本管理和 GitHub Release 发布规范。
- 将失败案例实体目录命名为 `bad_cases_失败案例/`，同时提供英文和中文标识。

### Known limitations / 已知限制

- 当前正式角色只有威龙 V2.1 肘部身体核心；攻击手臂、手、枪、攻击与换弹尚未批准和接入。
- `WL_Tactical_Rifle_Run_V2` 仅为独立 3D 技术证明，不是正式像素素材，也没有 Cocos 运行入口；第二版本等待 Q Bridge 与用户批准 Q 版母版。
- 3D V1 使用无枪托 C302 AirCannon，且不是正式战术步枪跑；它只以 `REJECTED_BAD_CASE / TECH_PROOF_ONLY` 证据形式归档。

## [0.1.0] - 2026-08-09

### Added

- 建立基于 Cocos Creator 3.8.8 的露娜八方向移动与武器分层试验台。
- 支持八方向移动、快速转向、瞄准、开火、换弹和显示层级验证。
- 提供 Web Desktop 构建配置和浏览器烟雾测试脚本。

[Unreleased]: https://github.com/yuanhuize/delta-force-pixel-combat-lab/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/yuanhuize/delta-force-pixel-combat-lab/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/yuanhuize/delta-force-pixel-combat-lab/releases/tag/v0.1.0
