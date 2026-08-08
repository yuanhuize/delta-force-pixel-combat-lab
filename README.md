# 三角洲行动像素战斗试验台 / Delta Force Pixel Combat Lab

## 项目说明 / Project Overview

这是一个基于 Cocos Creator 3.8.8 制作的非正式像素战斗原型，用于验证角色八方向移动、快速转向、身体与武器分层、瞄准、开火、换弹及前后遮挡关系。本项目目前是技术与美术流程试验台，不是完整游戏，也不代表正式角色美术质量。

This is an unofficial Cocos Creator 3.8.8 pixel-combat prototype for validating eight-direction movement, character/weapon layering, aiming, firing, reloading, and front/back rendering order. It is a technical and art-pipeline lab rather than a complete game or final-art showcase.

- 项目中文名：`三角洲行动像素战斗试验台`
- Project name: `Delta Force Pixel Combat Lab`
- 当前版本 / Version: `0.1.0`
- 引擎 / Engine: `Cocos Creator 3.8.8`
- 当前运行角色 / Runtime character: `露娜 Prototype 3 / Luna Prototype 3`
- GitHub 仓库 / Repository: `delta-force-pixel-combat-lab（三角洲行动像素战斗试验台）`

## GitHub 上传根目录 / Repository Root

GitHub Desktop 应添加和上传以下目录：

`combat_lab（战斗试验台项目 / Combat Lab Project）`

不要把上一级“三角洲行动-像素版”工作区整体作为仓库上传。上一级目录包含其他实验工程、生成缓存和大型源素材，不属于本仓库版本范围。

## 文件夹说明 / Folder Guide

| 实际文件夹 / Folder | 中文名称 | English Name | GitHub 处理方式 | 用途 |
| --- | --- | --- | --- | --- |
| `.creator/` | Creator 项目元数据 | Creator Project Metadata | 上传 | Cocos Creator 项目识别信息 |
| `assets/` | 游戏运行资源 | Runtime Game Assets | 上传 | 场景、TypeScript 脚本和当前可运行像素资源 |
| `build-configs/` | 构建配置 | Build Configurations | 上传 | Web Desktop 可复现构建参数 |
| `build-templates/` | 构建页面模板 | Build Templates | 上传 | Web 构建使用的 HTML/CSS 模板 |
| `scripts/` | 工具与发布脚本 | Tooling and Release Scripts | 上传 | 烟雾测试和版本打包 |
| `settings/` | 项目设置 | Project Settings | 上传 | Cocos Creator 项目配置 |
| `bad_cases_失败案例/` | 生成失败案例档案 | Generated Bad Case Archive | 上传 | 威龙 V1、露娜 V4/V5 的完整生成过程与失败复盘资料 |
| `build/` | 本地构建输出 | Local Build Output | 不提交 | 本机生成，可打包后作为 GitHub Release 附件 |
| `library/`、`temp/`、`profiles/` | 编辑器缓存 | Editor Cache | 不提交 | Cocos Creator 自动生成，可重新创建 |
| `artifacts/` | 测试截图 | Test Artifacts | 不提交 | 本地烟雾测试输出 |
| `release/` | 发布附件 | Release Packages | 不提交源码 | ZIP 和 SHA-256 文件上传到 GitHub Releases |

Cocos Creator 要求的标准目录保持英文名称；中文名称和英文含义在上表中同时注明。可自由命名的失败案例目录采用双语实体名称 `bad_cases_失败案例/`。

## 打开与运行 / Open and Run

1. 用 Cocos Creator 3.8.8 打开 `combat_lab（战斗试验台项目）`。
2. 打开 `assets/scenes/RigLab.scene`。
3. 点击编辑器顶部的预览按钮。

也可以在项目根目录执行命令行构建：

```bash
COCOS_CREATOR='/Applications/Cocos/Creator/3.8.8/CocosCreator.app/Contents/MacOS/CocosCreator'
"$COCOS_CREATOR" --project "$(pwd)" --build "configPath=$(pwd)/build-configs/web-desktop.json"
```

## 当前素材状态 / Asset Status

- 当前运行脚本已回退到露娜 Prototype 3，仅维持技术诊断，不是正式人物美术。
- 突击步枪包含八方向瞄准、开火和恢复三相位，武器、双手、弹匣及枪口分别成层。
- 换弹包含八方向、七帧分层动作。
- Prototype 3 使用完整身体四帧闭环跑动，并按走路帧同步双前臂和手掌图层。
- 威龙 Prototype 1 与露娜 Prototype 4/5 已标记为 `REJECTED_BAD_CASE`，完整过程保存在 `bad_cases_失败案例/`，不会被 Cocos 运行时加载。
- 失败案例的允许和禁止用途见 `bad_cases_失败案例/README.md`，机器可读登记见 `bad_cases_失败案例/registry.json`。

## 操作 / Controls

- `WASD` / 方向键：八方向移动。
- 鼠标移动：更新瞄准方向。
- `Q`：切换“移动方向决定朝向”与“鼠标决定朝向”。
- `0`：纯身体跑动；`1`：弓；`2`：突击步枪。
- 鼠标左键 / `Space`：攻击。
- `R`：步枪换弹。
- `T`：自动环绕检查八方向切换。

## 当前限制 / Current Limitations

- 不使用骨骼拉伸、IK 或网格变形，避免精细像素图出现长度变化和模糊。
- 临时跑动帧不作为最终美术验收；当前阶段主要检查方向切换、尺寸、脚点和图层。
- 上下方向的枪身透视由美术帧直接表现，运行时不缩放枪身。
- 新素材必须遵守 `assets/resources/luna/luna_rifle_run_v3_spec.json` 的方向顺序、手臂列索引和图层规格。

完整版本发布步骤见 `RELEASE.md`，版本变更记录见 `CHANGELOG.md`。
