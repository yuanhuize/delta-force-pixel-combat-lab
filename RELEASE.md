# 版本发布流程

本项目使用语义化版本，Git tag 和 GitHub Release 均采用 `vX.Y.Z` 格式，例如 `v0.1.0`。

## 版本来源

`package.json` 的 `version` 字段是唯一版本源。不要新增 `VERSION` 文件，也不要在构建配置中重复维护版本号。

版本含义：

- `PATCH`：修复问题，不改变既有操作或资源接口。
- `MINOR`：增加兼容的新功能、动作、武器或关卡能力。
- `MAJOR`：产生不兼容的存档、资源格式或操作方式变化。

## 发布前检查

1. 确认 Cocos Creator 版本为 `3.8.8`。
2. 确认工作区只包含本次版本需要的源码、资源和文档变更。
3. 更新 `package.json` 的 `version`，并把 `CHANGELOG.md` 中 `[Unreleased]` 的内容归入对应版本和发布日期。
4. 确认 tag 名与版本严格对应：`package.json` 为 `0.1.1` 时，tag 必须为 `v0.1.1`。
5. 执行 `npm run verify:runtime-gate`，确认六房、碰撞、角色哈希、nearest 元数据、禁止资源和独立 3D 闸门全部通过。
6. 使用项目内的 `build-configs/web-desktop.json` 重新构建，不复用旧版本产物。

## 构建 Web Desktop 版本

在 `combat_lab` 目录执行：

```bash
COCOS_CREATOR='/Applications/Cocos/Creator/3.8.8/CocosCreator.app/Contents/MacOS/CocosCreator'
"$COCOS_CREATOR" --project "$(pwd)" --build "configPath=$(pwd)/build-configs/web-desktop.json"
```

构建完成后必须确认以下文件存在：

```bash
test -f build/web-desktop/index.html
test -f build/web-desktop/src/settings.json
```

可用 `./run-lab.command` 在本机浏览器中检查六房局部跟随视窗、威龙八方向移动、房门和碰撞层。首次测试先执行 `npm install`，再执行：

```bash
node scripts/smoke-test.cjs
```

烟雾测试必须验证六房逐一到达、八方向映射、12 帧/18fps 动画、转向保持 `walkFrame`、2×整数缩放与 pixel-snap、左刷卡门锁定/解锁、右影院开放门洞、主厅—外厅中央门往返和外厅边界阻挡。测试结果必须显示 `SCENE_INTEGRATION_QA_PASS`、`ART_APPROVED`、`3D_APPROVED_TECH_PROOF_ONLY`，且 `errors`、`warnings` 均为空数组。

## 生成 Release 附件

源码仓不提交 `build/` 和 `release/`。确认构建通过后，在 `combat_lab` 目录执行：

```bash
npm run release:package
```

脚本从 `package.json` 读取版本号，检查 Web 构建是否完整，并拒绝覆盖同版本的既有附件。最终上传 `release/` 中的 Web 压缩包及对应的 `.sha256` 文件。

## 通过 GitHub Desktop 发布

首次建立仓库时：

1. 在 GitHub Desktop 中选择 `combat_lab`，按界面提示在此目录创建本地仓库。
2. 检查 Changes，确认 `library/`、`temp/`、`build/`、`profiles/`、`artifacts/`、`release/` 和 `.DS_Store` 没有进入提交。
3. 创建初始提交，再使用 **Publish repository** 创建远程仓库；发布前确认仓库名称、所属账号和可见性。

后续版本：

1. 提交版本号、更新日志及源码变更，提交说明建议为 `release: vX.Y.Z`。
2. 推送默认分支并确认 GitHub 上的提交完整。
3. 在该提交上创建 annotated tag `vX.Y.Z` 并推送。
4. 在 GitHub 上基于该 tag 创建 Release；标题使用 `vX.Y.Z`，正文采用 `CHANGELOG.md` 对应版本内容。
5. 上传 Web 压缩包和 SHA-256 文件；下载附件复核校验值后再正式发布。

## 回滚原则

- Release 附件错误但源码和 tag 正确时，替换附件并在说明中记录原因。
- tag 指向错误提交时，不复用已公开的版本号；修正后发布新的 PATCH 版本。
- 已公开版本不得静默改写源码历史或覆盖同名 tag。
