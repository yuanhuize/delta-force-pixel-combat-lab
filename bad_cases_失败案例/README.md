# 生成过程 Bad Case 档案

本目录保存生成过程中的失败版本，目的是复盘失败机制、改进验收方法，并为后续制作提供反例证据。所有内容均标记为 `REJECTED_BAD_CASE`，与游戏运行时资源隔离。

## 收录内容

| 档案 | 状态 | 主要问题 | 可借鉴内容 |
| --- | --- | --- | --- |
| `weilong_prototype_1/` | `REJECTED_BAD_CASE` | 锁定上半身身份后，独立生成并合成下半身动作 | 生成提示词、八方向生成源、构建脚本、QA 图/GIF、分层运行时输出 |
| `luna_prototype_4_5/` | `REJECTED_BAD_CASE` | V4 保留上半身并替换下半身；V5 又将上半身身份源与独立下半身动作合成 | V4/V5 生成源、合成脚本、方向动画 QA、规格和曾用运行时资源 |
| `luna_prototype_3_legacy_diagnostic/` | `REJECTED_BAD_CASE` | 旧运行诊断角色与武器分层已退出正式资源 | 曾用图集、规格和运行脚本 |
| `weilong_test02_candidate_rejected/` | `REJECTED_BAD_CASE` | 未获批准的 test02 全骨架候选曾残留运行时 | 候选图集、规格和 Cocos 元数据 |
| `weilong_3d_procedural_and_pixelization_bad_cases_威龙3D程序化与像素化失败案例/` | `REJECTED_BAD_CASE` | 写实/PBR 直缩、共享笼 Q 化、五姿势正弦跑步和上下半身分层四类失败 | 代表 PNG/GIF/JSON、脚本快照、源文件排除清单与哈希 |

详细登记见 `registry.json`。

## 允许用途

- 人工复盘失败原因和生成流程。
- 对比姿态、身份一致性、身体连接、步态和分层方式的问题。
- 审查提示词、脚本、规格和 QA 方法为何未能阻止错误结果。
- 为验收规则、检查清单和制作流程提供反例。

## 禁止用途

- 不得放回 `assets/` 或接入游戏运行时。
- 不得作为正式预览、角色身份基准或动作质量基准。
- 不得作为 img2img 输入、模型训练素材或后续生成的直接迭代底图。
- 不得因为文件完整或观感局部可用而移除 `REJECTED_BAD_CASE` 标记。

这些限制不影响其作为人工复盘材料的借鉴价值；它们用于说明“哪里错了、为什么错、如何避免再错”。
