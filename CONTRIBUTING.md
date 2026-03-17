# Contributing

感谢你对 `minecraft-smoke-test-kit` 的关注。

## 贡献原则

请尽量遵循以下原则：

- KISS：优先最小可理解方案
- YAGNI：不要为尚未验证的 loader 场景过度设计
- DRY：不要复制已有 orchestration 逻辑
- 保持 helper 与 orchestration 解耦

## 推荐贡献方向

欢迎以下类型的贡献：

- NeoForge helper 模板
- Fabric helper 模板
- Windows / Linux / macOS 兼容性验证
- 文档改进
- failure regex 与日志诊断改进
- 示例项目接入说明

## 提交建议

### Issue

在提交改动前，建议先描述：

- 目标 loader / 平台
- 预期 smoke-test 行为
- marker 触发时机
- 失败场景与验证方式

### Pull Request

请在 PR 中尽量包含：

1. 改动目标
2. 设计理由
3. 涉及文件
4. 验证步骤
5. 是否影响 marker 协议或命令参数

## 设计边界

请尽量保持以下边界稳定：

- `scripts/mc_smoke_test.py` 作为统一 orchestration 层
- `[MC_SMOKE_OK] side=<side>` 作为统一 marker 协议
- helper 只负责打印 marker，不负责结束进程

## 文档语言

- `README.md` 使用中文作为默认首页
- `README.en.md` 作为英文备选说明
- 代码与命令示例保持原始技术标识，不做翻译
