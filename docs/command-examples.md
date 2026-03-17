# Command Examples

## Claude Code / Trellis

建议放置路径：

```text
.claude/commands/trellis/smoke-test.md
```

典型调用目标：

- `runServer`
- `runClient`

命令文档应表达：

- 要运行哪个 task
- 监听哪个 marker
- 使用哪个 stop strategy
- 最终输出什么 summary

## Cursor

建议放置路径：

```text
.cursor/commands/trellis-smoke-test.md
```

内容上应与 Claude 版本保持平行，避免两个入口行为漂移。

## 推荐输出格式

```markdown
## Smoke Test Result

- Task: <gradle-task>
- Side: <server|client>
- Marker: <marker>
- Stop Strategy: <strategy>
- Result: Passed | Failed

### Evidence
- <marker seen / failure signal / exit code>

### Notes
- <follow-up if helper is missing or needs adaptation>
```

## 推荐命令策略

- 项目内已有 smoke-test 能力时：直接调用脚本
- 项目内缺少 helper 时：先生成 helper，再运行 smoke-test
- 若项目已有自己的命令系统：保留参数协议，不强依赖当前目录结构
