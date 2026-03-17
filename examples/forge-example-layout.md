# Forge Example Layout

```text
example-forge-project/
├─ .claude/
│  └─ commands/
│     └─ trellis/
│        └─ smoke-test.md
├─ .cursor/
│  └─ commands/
│     └─ trellis-smoke-test.md
├─ .trellis/
│  └─ scripts/
│     └─ mc_smoke_test.py
└─ src/
   └─ main/
      └─ java/
         └─ com/example/mymod/
            ├─ MyMod.java
            └─ smoketest/
               ├─ SmokeTestMarkers.java
               ├─ ServerSmokeTestHooks.java
               └─ client/
                  └─ ClientSmokeTestHooks.java
```

## 说明

- `MyMod.java` 保持主入口职责最小化
- `smoketest/` 作为聚焦包，只放 smoke-test helper
- Claude / Cursor 命令文档与 Python 脚本相互配合
- helper 输出 marker，脚本负责结束进程
