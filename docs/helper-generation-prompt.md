# Helper Generation Prompt Guide

## Purpose

当目标项目不属于当前已验证模板范围时，不要直接套用 Forge 1.20.1 helper 模板。

改为先读取目标项目的实际 loader、生命周期、logger 风格与主入口结构，再按本指南生成最小 smoke-test helper。

当前已验证模板范围只有：

- Forge 1.20.1

## Stable contract

无论目标环境是什么，生成出的 helper 都必须满足以下稳定契约：

- server marker: `[MC_SMOKE_OK] side=server`
- client marker: `[MC_SMOKE_OK] side=client`
- helper 只负责打印 marker
- helper 不负责退出进程
- server 和 client 分侧处理
- 尽量复用项目原有 logger 风格
- main mod entrypoint 保持精简

## Before generating

先检查：

1. 当前项目使用的 loader
2. Minecraft / loader 版本
3. 主 mod 入口类与基础 package
4. 项目已有 logger 风格
5. server 侧最早稳定成功时机
6. client 侧最早稳定成功时机

如果这些信息无法从代码中确认，不要猜路径、不要猜生命周期事件。

## Preset prompt template

```text
Create a minimal Minecraft smoke-test helper for this project.

Goal:
- Emit an explicit success marker for smoke-test orchestration.
- Do not exit the game/process from the helper.

Requirements:
- Inspect the current project first instead of assuming Forge 1.20.1 APIs.
- Add a focused smoke-test package that matches the existing project package layout.
- Add one server-side hook that logs exactly: [MC_SMOKE_OK] side=server
- Add one client-side hook that logs exactly: [MC_SMOKE_OK] side=client
- Reuse the existing project logger style.
- Prefer the earliest stable lifecycle point that proves successful startup.
- Keep the main mod entrypoint thin.
- Do not add unrelated abstractions.
- Do not add process-exit logic.

Deliverables:
1. Helper classes
2. Any minimal registration/event wiring required
3. The exact marker strings used
4. Which lifecycle event each side uses and why
5. Any assumptions that still need manual confirmation
```

## Good / Base / Bad

### Good

- 先读项目，再选 lifecycle hook
- helper 只打印 marker
- 生成结果与项目现有包结构、logger 风格一致

### Base

- 仍能生成最小 helper，但有少量待人工确认的 lifecycle 选择

### Bad

- 未检查项目就直接套用 Forge 1.20.1 模板
- 把退出逻辑放进 helper
- 修改过多非 smoke-test 相关代码
- 使用不一致的 marker 文本
