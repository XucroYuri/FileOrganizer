# FileOrganizer - 智能文件整理助手

[![Python 3.6+](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 功能特点

- **智能文件分类**：根据文件类型和名称自动分类文件
- **重复文件检测**：通过哈希值检测完全相同的文件
- **安全批处理**：分批次处理文件，避免高并发操作对硬件造成损伤
- **自定义分类规则**：可扩展的分类规则系统
- **无法识别文件处理**：对无法自动分类的文件进行特殊标记和归档
- **LLM智能分类**：利用大语言模型生成目录结构或分类指令

## 安装

### 前提条件

- Python 3.6 或更高版本
- pip 包管理器

### 安装方法

#### 从源码安装

```bash
# 克隆仓库
git clone https://github.com/XucroYuri/FileOrganizer.git
cd FileOrganizer

# 安装依赖
pip install -e .
```

#### 使用pip安装

```bash
pip install fileorganizer
```

## 快速开始

### 基本用法

```bash
# 基本文件整理
fileorganizer /path/to/source /path/to/destination

# 模拟运行（不实际移动文件）
fileorganizer /path/to/source /path/to/destination --dry-run
```

### 使用LLM功能

```bash
# 使用LLM生成目录结构
fileorganizer /path/to/source /path/to/destination --generate directory --llm-provider deepseek

# 使用LLM生成分类命令
fileorganizer /path/to/source /path/to/destination --generate commands --llm-provider deepseek
```

## 命令行参数

| 参数 | 说明 |
|------|------|
| `source` | 源文件夹路径 |
| `destination` | 目标文件夹路径 |
| `--batch-size` | 每批处理的文件数量 (默认: 100) |
| `--delay` | 批次间延迟时间(秒) (默认: 1.0) |
| `--dry-run` | 模拟运行，不实际移动文件 |
| `--duplicate-action` | 重复文件处理方式 (keep-first/keep-newest/ask) |
| `--llm-provider` | 大语言模型服务提供商 (deepseek) |
| `--llm-api-key` | LLM API密钥（推荐交互式输入） |
| `--llm-model` | 大语言模型名称 (默认: deepseek-chat) |
| `--generate` | 生成目录结构或分类指令 (directory/commands) |
| `--test-mode` | 启用测试模式（使用后自动清除配置） |

## LLM功能说明

FileOrganizer支持使用大语言模型(LLM)来增强文件分类能力：

- **目录结构生成**：根据文件列表智能生成合适的目录结构
- **分类命令生成**：生成用于文件分类的系统命令

使用LLM功能需要配置API密钥，可通过环境变量`LLM_API_KEY`或命令行参数`--llm-api-key`设置。

## 贡献指南

欢迎参与FileOrganizer项目！请查看[贡献指南](CONTRIBUTING.md)了解详情。

### 开发环境设置

```bash
# 安装开发依赖
pip install -e .[dev]

# 安装pre-commit钩子
pre-commit install

# 运行测试
pytest tests/
```

## 许可证

本项目采用MIT许可证 - 详情请查看[LICENSE](LICENSE)文件。