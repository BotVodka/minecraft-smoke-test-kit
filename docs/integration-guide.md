# Integration Guide

## 1. 全局 Claude 模式（推荐）

推荐优先使用全局 Claude 模式：

- 全局 command 作为唯一入口
- 中央脚本 `scripts/mc_smoke_test.py` 作为单一事实来源
- 项目内只安装必须参与编译的 helper

### 1.1 配置中央仓库根路径

在全局 Claude settings 中配置：

```json
{
  "env": {
    "MC_SMOKE_TEST_KIT_ROOT": "D:/projects/code/minecraft-smoke-test-kit"
  }
}
```

### 1.2 对已验证环境安装 Forge helper

当前唯一已验证环境：Forge 1.20.1。

推荐运行：

```bash
python3 ./scripts/install_forge_smoke_test.py \
  --target-project "/absolute/path/to/your-project" \
  --base-package "com.example.mymod" \
  --mod-class "MyMod" \
  --global-mode
```

这一路径只安装 helper Java 文件。

如目标文件已存在，可增加 `--force` 覆盖。

### 1.3 通过中央脚本运行

服务端：

```bash
python3 "D:/projects/code/minecraft-smoke-test-kit/scripts/mc_smoke_test.py" \
  --project-root "/absolute/path/to/your-project" \
  --task runServer \
  --side server \
  --bootstrap-helper
```

客户端：

```bash
python3 "D:/projects/code/minecraft-smoke-test-kit/scripts/mc_smoke_test.py" \
  --project-root "/absolute/path/to/your-project" \
  --task runClient \
  --side client \
  --bootstrap-helper
```

### 1.4 未知环境走预设 prompt 生成

如果目标环境不是当前已验证的 Forge 1.20.1：

- 不要直接套用现成 Forge helper 模板
- 先读取目标项目的实际 loader / lifecycle / logger 风格
- 再使用预设 prompt 生成最小 helper

参见：

- `docs/helper-generation-prompt.md`

## 2. 项目内复制模式（兼容旧方式）

如果你不使用全局 Claude command，也可以继续沿用项目内复制模式。

### 2.1 使用安装脚本

```bash
python3 ./scripts/install_forge_smoke_test.py \
  --target-project "/absolute/path/to/your-project" \
  --base-package "com.example.mymod" \
  --mod-class "MyMod"
```

安装脚本会自动复制脚本、命令模板与 Forge helper。

### 2.2 手动复制脚本

将 `scripts/mc_smoke_test.py` 复制到目标项目，例如：

```text
./.trellis/scripts/mc_smoke_test.py
```

### 2.3 接入命令模板

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

### 全局 Claude 模式

#### Dedicated server

```bash
python3 "D:/projects/code/minecraft-smoke-test-kit/scripts/mc_smoke_test.py" \
  --project-root "/absolute/path/to/project" \
  --task runServer \
  --side server \
  --bootstrap-helper
```

#### Client

```bash
python3 "D:/projects/code/minecraft-smoke-test-kit/scripts/mc_smoke_test.py" \
  --project-root "/absolute/path/to/project" \
  --task runClient \
  --side client \
  --bootstrap-helper
```

### 项目内复制模式

#### Dedicated server

```bash
python3 ./.trellis/scripts/mc_smoke_test.py --task runServer --side server
```

#### Client

```bash
python3 ./.trellis/scripts/mc_smoke_test.py --task runClient --side client
```

## 6. 推荐集成顺序

### 全局 Claude 模式

1. 配置 `MC_SMOKE_TEST_KIT_ROOT`
2. 安装 helper Java 文件
3. 通过中央脚本执行 smoke test
4. 先验证 server，再验证 client

### 项目内复制模式

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
