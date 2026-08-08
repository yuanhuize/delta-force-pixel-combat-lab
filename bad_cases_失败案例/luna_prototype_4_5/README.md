# 露娜 Prototype 4/5：REJECTED_BAD_CASE

本目录完整保存露娜 V4/V5 的生成源、合成脚本、QA 动画、规格和曾用运行时资源。

拒收原因：

- V4 保留原上半身，同时替换或生成下半身，人物没有统一姿态解算。
- V5 在 V4 基础上，将保留的上半身身份源与独立生成的八方向下半身动作再次合成，进一步放大身体连接、比例和动作连续性问题。

可复盘重点：

- `authoring_and_qa/v4_leg_revision_sources/` 与 `v4_leg_revision_qa/`：V4 输入和方向循环结果。
- `authoring_and_qa/v5_8frame_sources/` 与 `v5_8frame_qa/`：V5 八方向八帧输入和 QA 结果。
- `authoring_and_qa/build_left_gait_v4.py` 与 `build_8dir_8f_v5.py`：合成流程实现，仅供审计。
- `former_runtime_resources/`：曾用运行时输出和场景设计副本，仅供追溯。

本档案禁止接入游戏、作为正式基准、用于模型训练、img2img 或后续生成底图。
