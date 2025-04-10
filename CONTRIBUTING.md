# 贡献指南

欢迎参与FileOrganizer项目！请遵循以下规范：

## 问题报告
- 使用Issue模板提交问题
- 包含Python版本、操作系统等环境信息
- 提供可复现的示例步骤

## 代码贡献
1. Fork仓库并创建特性分支
2. 遵循PEP8代码规范
3. 提交前运行单元测试：`pytest tests/`
4. 使用语义化的提交信息

## Pull Request
- 关联相关Issue编号
- 包含测试用例和文档更新
- 通过GitHub Actions的CI检查

## 代码风格
- 使用Black代码格式化
- 类型注解强制要求
- 函数/方法需包含Google风格docstring

## 开发环境
```bash
pip install -e .[dev]
pre-commit install
```