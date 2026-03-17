# GitHub Open Source Repository Blueprint

下面是把当前成果整理成独立 GitHub 开源仓库时，推荐采用的结构。

## 推荐仓库名

- `minecraft-smoke-test-kit`
- `mc-gradle-smoke-test-kit`
- `minecraft-agent-smoke-test`

## 推荐目录树

```text
minecraft-smoke-test-kit/
├─ README.md
├─ LICENSE
├─ .gitignore
├─ docs/
│  ├─ integration-guide.md
│  ├─ forge-setup.md
│  ├─ adaptation-guide.md
│  └─ command-examples.md
├─ scripts/
│  └─ mc_smoke_test.py
├─ commands/
│  ├─ claude/trellis/
│  │  └─ smoke-test.md
│  └─ cursor/
│     └─ trellis-smoke-test.md
├─ templates/
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

## 关键文件职责

| 文件 | 作用 |
|---|---|
| `README.md` | 项目介绍、快速开始、核心设计说明 |
| `LICENSE` | 开源许可 |
| `docs/integration-guide.md` | 新项目如何落地 |
| `docs/forge-setup.md` | Forge 项目接入细节 |
| `docs/adaptation-guide.md` | NeoForge / Fabric 迁移说明 |
| `scripts/mc_smoke_test.py` | 自动化 smoke-test 核心脚本 |
| `commands/...` | Claude / Cursor 命令模板 |
| `templates/forge/...` | Forge helper 模板 |
| `examples/...` | 目录映射与示例说明 |

## README 建议章节

1. What problem this solves
2. How it works
3. Quick start
4. Marker protocol
5. Forge integration
6. Claude / Cursor command integration
7. Adaptation to other loaders
8. Failure modes and troubleshooting
9. Design principles
10. License

## 复制 / 模板化策略

### 适合直接复制

- `scripts/mc_smoke_test.py`
- `commands/claude/trellis/smoke-test.md`
- `commands/cursor/trellis-smoke-test.md`

### 适合模板化

- `templates/forge/**/*.java.template`

原因：Java helper 依赖具体项目的包名、主 mod 类名与 mod id。

## 发布建议

- 初版先支持 Forge
- README 明确写出：脚本与 marker 协议是稳定层，loader helper 是适配层
- 后续再按目录新增 `templates/neoforge/`、`templates/fabric/`
