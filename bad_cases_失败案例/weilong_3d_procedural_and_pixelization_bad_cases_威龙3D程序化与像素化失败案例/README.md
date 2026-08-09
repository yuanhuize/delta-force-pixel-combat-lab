# 威龙 3D、程序化与像素化失败案例 / Weilong 3D, Procedural and Pixelization Bad Cases

状态：`REJECTED_BAD_CASE`

本目录仅用于人工取证复盘（`forensic review only`）。其中的 PNG、GIF、JSON 和脚本快照用于说明失败机制，不是可运行资源，也不是可继续生产的候选版本。

## 全局禁令

- 禁止接入游戏或复制回 `assets/`。
- 禁止用于生图、img2img、模型训练或数据集。
- 禁止作为角色身份、动作、像素风格或后续迭代基线。
- 禁止因为某个局部看起来可用而移除 `REJECTED_BAD_CASE` 标记。

## 四组反例

| 目录（English / 中文） | 状态 | 失败原因 | 代表证据 |
| --- | --- | --- | --- |
| `01_pbr_direct_downscale_noise_写实高模直缩噪点/` | `REJECTED_BAD_CASE` | 写实成人比例、高频 PBR/材质细节直接缩到 128px 后变成随机噪点；V1 还使用无枪托 C302 AirCannon，画面不是正式战术步枪跑。 | 高分帧、128px 图集、GIF、JSON、V1 管线脚本快照 |
| `02_shared_cage_chibi_mud_共享变形笼Q化泥块/` | `REJECTED_BAD_CASE` | 用共享变形笼压缩整个人物比例，再用固定少色和邻域平均处理，导致体块过矮、装甲结构糊成泥块。 | 高分标定、128px 结果、4×预览、manifest、变形笼脚本快照 |
| `03_five_pose_sine_run_五姿势正弦跑步/` | `REJECTED_BAD_CASE` | `WL2D_run_forward_fullbody` / `weilong_q_run_v2` 只写入 5 个关键姿势，并用正弦/余弦驱动摆腿；没有真实脚底锁定、承重、蹬地和战术持枪跑动作设计。 | 12 帧图集、GIF、接触表、JSON、程序跑步脚本快照 |
| `04_upper_lower_split_上下半身分层/` | `REJECTED_BAD_CASE` | `weilong_pixel_actions_v2` 将独立生成的下半身与固定上半身再拼合，破坏完整人体动作、连接结构和一致的承重关系。 | 完整人物/分层对照、GIF、下半身图集、manifest、三个构建脚本快照 |

## 3D V1 与 V2 的边界

- 本目录中的 3D V1 是失败案例：无枪托 `Assault_C302_AirCannon_Outers_1u_UI_V1`、并非正式战术步枪跑，状态为 `REJECTED_BAD_CASE / TECH_PROOF_ONLY`。
- PM 批准的 `WL_Tactical_Rifle_Run_V2` 仅是独立的 `3D_APPROVED_TECH_PROOF_ONLY` 技术证明；它不是正式像素素材，也没有进入本目录或 Cocos 运行时。
- 原始 `weilong_fullbody_source_actions.blend` 体积约 562 MiB，不进入普通 Git push。其本地来源、字节数与 SHA-256 记录在 `evidence_registry.json`。

机器可读证据与禁止用途见 `evidence_registry.json`。
