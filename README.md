# FileOrganizer - 智能文件整理助手

FileOrganizer是一个帮助用户整理大量混乱文件的工具，能够自动分类文件、检测重复文件，并安全地将文件移动到有组织的目录结构中。

## 功能特点

- **智能文件分类**：根据文件类型和名称自动分类文件
- **重复文件检测**：通过哈希值检测完全相同的文件
- **安全批处理**：分批次处理文件，避免高并发操作对硬件造成损伤
- **自定义分类规则**：可扩展的分类规则系统
- **无法识别文件处理**：对无法自动分类的文件进行特殊标记和归档

## 🚀 快速开始

### 安装
```bash
# 通过 pip 安装
pip install git+https://github.com/XucroYuri/FileOrganizer.git

# 或本地开发安装
git clone https://github.com/XucroYuri/FileOrganizer.git
cd FileOrganizer
pip install -e .
```