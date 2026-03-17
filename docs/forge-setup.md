# Forge Setup Guide

## Goal

将本模板接入一个 Forge 项目，使 `runServer` / `runClient` 在成功启动后自动结束。

## Step 1: 复制脚本

复制：

```text
scripts/mc_smoke_test.py
```

到目标项目，例如：

```text
./.trellis/scripts/mc_smoke_test.py
```

## Step 2: 复制 Forge helper 模板

将以下模板复制到目标项目：

- `SmokeTestMarkers.java.template`
- `ServerSmokeTestHooks.java.template`
- `ClientSmokeTestHooks.java.template`

建议映射到：

```text
src/main/java/<base-package>/smoketest/
src/main/java/<base-package>/smoketest/client/
```

## Step 3: 替换占位符

- `__BASE_PACKAGE__` → 例如 `com.example.mymod`
- `__BASE_PACKAGE_PATH__` → 例如 `com/example/mymod`
- `__MOD_CLASS__` → 例如 `MyMod`

## Step 4: 确认事件时机

当前 Forge helper 的默认策略：

- server: 在 `ServerStartedEvent` 打印 marker
- client: 在 `TitleScreen` 首次打开时打印 marker

这两个时机的目标都是：

- 足够早，避免无意义等待
- 足够稳定，避免尚未完成启动就误报成功

## Step 5: 运行 smoke test

### Server

```bash
python3 ./.trellis/scripts/mc_smoke_test.py --task runServer --side server
```

### Client

```bash
python3 ./.trellis/scripts/mc_smoke_test.py --task runClient --side client
```

## Step 6: 验证结果

成功时应看到：

- marker 被识别
- 进程被自动结束
- summary 输出 `Passed` 等价结果

## Notes

- helper 不应包含退出逻辑
- 主 mod entrypoint 应保持薄
- 若项目日志体系与当前模板不同，优先保留原项目 logger 风格
