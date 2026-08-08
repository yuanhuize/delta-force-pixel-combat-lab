# 露娜八方向移动与武器分层试验台

这是一个独立的 Cocos Creator 3.8.8 原型工程，只用于验证露娜的八方向移动、快速转向、身体/双手/武器同步、开火反馈和前后显示层级，不扩展成完整游戏。

当前实现只使用 Cocos `Sprite`、PNG 图集和 TypeScript，不使用 `sp.Skeleton`，也不依赖 Spine 编辑器或 Spine Runtime。身体、武器、两只手、弹匣和枪口效果都是独立的刚性像素图层。

## 打开与运行

1. 用 Cocos Creator 3.8.8 打开本目录 `combat_lab`。
2. 打开 `assets/scenes/RigLab.scene`。
3. 点击编辑器顶部的预览按钮。

也可以通过命令行构建浏览器测试版：

```bash
'/Applications/Cocos/Creator/3.8.8/CocosCreator.app/Contents/MacOS/CocosCreator' \
  --project '/Users/yuanhuize/codex work/三角洲行动-像素版/combat_lab' \
  --build 'configPath=/Users/yuanhuize/codex work/三角洲行动-像素版/combat_lab/build-configs/web-desktop.json'
```

## 当前素材状态与拒收通知

- 当前运行脚本已回退到 Prototype 3，仅维持技术诊断，不是正式人物美术。
- 突击步枪：8 方向 × 瞄准/开火/恢复 3 相位，武器、双手、弹匣和枪口分别成层。
- 换弹：8 方向 × 7 帧。
- 已接入 Prototype 3：完整身体四帧闭环跑动、按走路帧变化的双前臂/手掌图层，以及正下方向约 36.87° 的枪械美术斜置。逻辑弹道仍保持严格正下。
- Prototype 4/5 因采用“保留上半身＋替换/生成下半身”方法，已标记为 `REJECTED_BAD_CASE` 并移出 `assets/resources`。
- 全项目永久规则见根目录 `ART_ASSET_GENERATION_STANDARD.md`，拒收登记见 `art_demos/_rejected/rejected_asset_registry.json`。

## 操作

- `WASD` / 方向键：八方向移动。
- 鼠标移动：更新瞄准方向。
- `Q`：在“移动方向决定朝向”和“鼠标决定朝向”之间切换。
- `0`：纯身体跑动；`1`：弓；`2`：突击步枪。
- 鼠标左键 / `Space`：攻击。
- `R`：步枪换弹。
- `T`：自动环绕检查八方向切换。

## 本阶段刻意保留的限制

- 不使用骨骼拉伸、IK 或网格变形，避免精细像素图出现长度变化和模糊。
- 不把临时跑动帧当成最终美术验收；本阶段先检查方向切换、尺寸、脚点和图层。
- 上下方向的枪身透视由美术帧直接表现，不在运行时缩放枪身。
- 新素材必须遵守 `assets/resources/luna/luna_rifle_run_v3_spec.json` 的方向顺序、手臂列索引和图层规格。

如果方向切换、图层或握枪协调仍不自然，只在这个试验台里修正，不把问题扩散进完整项目。
