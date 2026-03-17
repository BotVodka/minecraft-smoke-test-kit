# Adaptation Guide

## Stable contract

以下内容建议视为稳定层，不应因 loader 切换而频繁变化：

- Python orchestration 脚本接口
- marker 字符串协议
- `--task` / `--side` / `--marker` / `--stop-strategy` 参数命名

## Loader-specific layer

以下内容属于适配层：

- helper 所在包结构
- 生命周期事件选择
- loader 注解 / 事件订阅方式
- client 侧“启动成功”判定点

## 迁移到 NeoForge

建议复用：

- `scripts/mc_smoke_test.py`
- 命令模板
- marker 协议

只新增：

- `templates/neoforge/...` helper 模板

## 迁移到 Fabric

建议复用：

- `scripts/mc_smoke_test.py`
- 命令模板
- marker 协议

只新增：

- `templates/fabric/...` helper 模板

## 适配原则

1. 不要把退出逻辑塞进 helper
2. 不要让 orchestration 层感知过多 loader 细节
3. 优先选择“明确证明已成功启动”的最早稳定时机打印 marker
4. 如果没有显式 marker，再考虑日志回退匹配

## Good / Base / Bad

### Good

- helper 在稳定生命周期事件打印唯一 marker
- orchestration 脚本只做监听与停机

### Base

- server 仍可临时用 `Done (...)` 作为辅助 success regex

### Bad

- 用固定 sleep 时间代替显式成功信号
- helper 直接调用退出逻辑
- 不同 loader 使用不一致 marker 文本
