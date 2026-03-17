# Integration Guide

## 1. 复制脚本

将 `scripts/mc_smoke_test.py` 复制到目标项目，例如：

```text
./.trellis/scripts/mc_smoke_test.py
```

## 2. 接入命令模板

按宿主工具复制命令文件：

- Claude Code / Trellis:
  - `.claude/commands/trellis/smoke-test.md`
- Cursor:
  - `.cursor/commands/trellis-smoke-test.md`

如果目标项目已有自己的命令命名体系，可只保留文案与参数约定。

## 3. 生成 Forge helper

将 `loaders/forge/` 下的 Java 模板复制到目标项目，并替换以下占位符：

- `__BASE_PACKAGE__`
- `__BASE_PACKAGE_PATH__`
- `__MOD_ID__`
- `__MOD_CLASS__`

建议最终落地目录：

```text
src/main/java/<base-package>/smoketest/
src/main/java/<base-package>/smoketest/client/
```

## 4. marker 协议

统一 marker：

- server: `[MC_SMOKE_OK] side=server`
- client: `[MC_SMOKE_OK] side=client`

约束：

- helper 只打印 marker
- helper 不负责退出 Minecraft
- orchestration 脚本负责结束进程

## 5. 运行方式

### Dedicated server

```bash
python3 ./.trellis/scripts/mc_smoke_test.py --task runServer --side server
```

### Client

```bash
python3 ./.trellis/scripts/mc_smoke_test.py --task runClient --side client
```

## 6. 推荐集成顺序

1. 先接入 Python 脚本
2. 再接入命令模板
3. 最后加入 Forge helper
4. 先验证 server，再验证 client

## 7. 可扩展点

后续若要扩展到 NeoForge / Fabric，建议保持不变的部分：

- Python orchestration 脚本
- marker 字符串协议
- 命令层参数命名

只替换各自 loader 的 helper 实现。
