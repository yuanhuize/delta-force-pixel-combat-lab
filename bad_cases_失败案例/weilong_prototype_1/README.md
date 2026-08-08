# 威龙 Prototype 1：REJECTED_BAD_CASE

本目录完整保存威龙 V1 的生成源、构建脚本、提示词、QA 结果和曾用运行时资源。

拒收原因：制作流程锁定上半身身份，再独立生成并合成下半身动作，导致完整人物没有在同一姿态、骨架和时间点下统一解算。局部帧即使看似可用，也不能证明人物结构、身份和动作连续性成立。

可复盘重点：

- `authoring_and_qa/generated_sources/`：八方向生成源，可观察身体连接与身份漂移。
- `authoring_and_qa/qa/`：循环动画、换弹和身份对比，可检查当时 QA 未覆盖的问题。
- `authoring_and_qa/IMAGEGEN_PROMPTS_v1.md`：生成提示词记录。
- `authoring_and_qa/build_weilong_prototype_v1.py`：合成与打包实现；保留用于代码审计，不应再次执行生成正式资产。
- `former_runtime_resources/`：曾经接入运行时的输出，仅供追溯。

更详细的原始说明位于 `authoring_and_qa/README.md`。本档案禁止接入游戏、作为正式基准、用于模型训练、img2img 或后续生成底图。
