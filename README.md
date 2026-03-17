# Minecraft Smoke Test Kit

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![README: 中文](https://img.shields.io/badge/README-%E4%B8%AD%E6%96%87-blue.svg)](./README.md)
[![README: English](https://img.shields.io/badge/README-English-blue.svg)](./README.en.md)

一个面向 Minecraft Mod 开发的可复用 smoke-test 工具包。

它的目标是让 AI agent 在执行 `runServer` / `runClient` 后，等待显式启动成功 marker，并在确认成功启动后自动结束进程，不再要求人工关闭客户端窗口或在服务端控制台输入 `stop`。

> English version: see [`README.en.md`](./README.en.md)

## 这个项目解决什么问题

在 Minecraft Mod 开发中，`./gradlew runServer` 和 `./gradlew runClient` 很适合做启动验证，但在 agent 驱动工作流里通常有几个痛点：

- 进程启动成功后会持续挂起
- 成功判定经常依赖脆弱的日志猜测
- 停机通常需要人工干预
- 不同项目、不同 loader 的启动信号并不一致

这个工具包通过一个简单契约把流程标准化：

1. 一个极小的 loader-specific helper 打印显式成功 marker。
2. 一个通用 Python orchestration 脚本监听这个 marker。
3. 一旦看到 marker，脚本就以受控方式结束进程。

## 工作原理

### 稳定层

这些文件原则上可以跨项目直接复用：

- `scripts/mc_smoke_test.py`
- `scripts/install_forge_smoke_test.py`
- `commands/claude/trellis/smoke-test.md`
- `commands/cursor/trellis-smoke-test.md`

### 适配层

这些文件依赖具体项目结构，应保持模板化：

- `loaders/forge/.../SmokeTestMarkers.java.template`
- `loaders/forge/.../ServerSmokeTestHooks.java.template`
- `loaders/forge/.../client/ClientSmokeTestHooks.java.template`

## 快速开始

### 1. 使用安装脚本

推荐直接运行安装脚本：

```bash
python3 ./scripts/install_forge_smoke_test.py \
  --target-project "/absolute/path/to/your-project" \
  --base-package "com.example.mymod" \
  --mod-class "MyMod"
```

该脚本会自动复制：

- `./.trellis/scripts/mc_smoke_test.py`
- `.claude/commands/trellis/smoke-test.md`
- `.cursor/commands/trellis-smoke-test.md`
- Forge smoke-test helper Java 文件

### 2. 手动复制 orchestration 脚本

将：

```text
scripts/mc_smoke_test.py
```

复制到目标项目，例如：

```text
./.trellis/scripts/mc_smoke_test.py
```

### 3. 手动复制命令模板

- Claude Code / Trellis:
  - `commands/claude/trellis/smoke-test.md`
- Cursor:
  - `commands/cursor/trellis-smoke-test.md`

### 4. 手动接入 Forge helper 模板

将 Forge helper 模板复制到目标项目，并替换：

- `__BASE_PACKAGE__`
- `__BASE_PACKAGE_PATH__`
- `__MOD_ID__`
- `__MOD_CLASS__`

推荐目标目录：

```text
src/main/java/<base-package>/smoketest/
src/main/java/<base-package>/smoketest/client/
```

### 5. 运行 smoke test

服务端：

```bash
python3 ./.trellis/scripts/mc_smoke_test.py --task runServer --side server
```

客户端：

```bash
python3 ./.trellis/scripts/mc_smoke_test.py --task runClient --side client
```

## Marker 协议

本项目使用统一显式 marker 协议：

- server: `[MC_SMOKE_OK] side=server`
- client: `[MC_SMOKE_OK] side=client`

规则：

- helper 只负责打印 marker
- helper 不负责主动退出 Minecraft
- 进程结束由 orchestration 层统一负责

## 仓库结构

```text
minecraft-smoke-test-kit/
├─ README.md
├─ README.en.md
├─ LICENSE
├─ .gitignore
├─ docs/
│  ├─ integration-guide.md
│  ├─ forge-setup.md
│  ├─ adaptation-guide.md
│  ├─ command-examples.md
│  └─ github-repo-blueprint.md
├─ scripts/
│  └─ mc_smoke_test.py
├─ commands/
│  ├─ claude/trellis/
│  │  └─ smoke-test.md
│  └─ cursor/
│     └─ trellis-smoke-test.md
├─ loaders/
│  └─ forge/
│     └─ src/main/java/__BASE_PACKAGE_PATH__/
│        └─ smoketest/
│           ├─ SmokeTestMarkers.java.template
│           ├─ ServerSmokeTestHooks.java.template
│           └─ client/
│              └─ ClientSmokeTestHooks.java.template
└─ examples/
   └─ forge-example-layout.md
```

## Forge 接入

参见：

- `docs/integration-guide.md`
- `docs/forge-setup.md`

## Claude / Cursor 命令集成

本项目提供并行命令模板，适配：

- Claude Code / Trellis
- Cursor

参见：

- `docs/command-examples.md`

## 适配其他 loader

推荐方式：

- 保持 Python orchestration 脚本不变
- 保持 marker 协议不变
- 保持命令参数命名不变
- 只替换 loader-specific helper 实现

这意味着未来支持 NeoForge / Fabric 时，优先新增 helper 模板，而不是重写 orchestration 层。

## 常见失败模式与排障

常见失败类型：

- Gradle build 失败
- 目录锁 / 世界锁冲突
- 未输出显式 marker
- loader 启动崩溃
- Windows 进程树结束行为差异

脚本会输出包含以下信息的 summary：

- task
- side
- marker
- stop strategy
- exit result
- last log lines

## 设计原则

- **KISS**：helper 只打印 marker
- **DRY**：进程控制统一放在一个 Python 脚本中
- **YAGNI**：先覆盖 `runServer` / `runClient`
- **SOLID**：orchestration 与 loader hook 解耦

## License

默认推荐使用 MIT。

如果你把它发布成独立 GitHub 仓库，请保留根级 `LICENSE` 文件。
