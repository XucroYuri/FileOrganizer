#!/usr/bin/env python3
"""
FileOrganizer 主程序入口
"""
import sys
import os
import argparse
import getpass
from pathlib import Path
from fileorganizer.core import FileOrganizer
from fileorganizer.config.llm_config import LLMConfig

def main():
    """主程序入口函数"""
    parser = argparse.ArgumentParser(description='FileOrganizer - 智能文件整理助手')
    parser.add_argument('source', help='源文件夹路径')
    parser.add_argument('destination', help='目标文件夹路径')
    parser.add_argument('--batch-size', type=int, default=100, help='每批处理的文件数量 (默认: 100)')
    parser.add_argument('--delay', type=float, default=1.0, help='批次间延迟时间(秒) (默认: 1.0)')
    parser.add_argument('--dry-run', action='store_true', help='模拟运行，不实际移动文件')
    parser.add_argument('--duplicate-action', choices=['keep-first', 'keep-newest', 'ask'], 
                        default='ask', help='重复文件处理方式 (默认: ask)')
    parser.add_argument('--llm-provider', choices=['deepseek'], default='deepseek', help='大语言模型服务提供商')
    parser.add_argument('--llm-api-key', help='LLM API密钥（推荐交互式输入）')
    parser.add_argument('--test-mode', action='store_true', help='启用测试模式（使用后自动清除配置）')
    parser.add_argument('--llm-model', default='deepseek-chat', help='大语言模型名称')
    parser.add_argument('--generate', choices=['directory', 'commands'], help='生成目录结构或分类指令')
    
    args = parser.parse_args()
    
    # 验证目录存在性
    source_path = Path(args.source)
    dest_path = Path(args.destination)
    
    if not source_path.exists():
        print(f"错误：源目录不存在 - {source_path}")
        sys.exit(1)
    if not dest_path.exists():
        print(f"正在创建目标目录: {dest_path}")
        dest_path.mkdir(parents=True, exist_ok=True)

    # 添加权限检查
    if not os.access(str(dest_path), os.W_OK):
        print(f"错误：没有写入权限 - {dest_path}")
        sys.exit(1)
    if not dest_path.exists():
        print(f"错误：目标目录不存在 - {dest_path}")
        sys.exit(1)

    # 添加LLM配置初始化
    llm_config = LLMConfig(
        provider=args.llm_provider,
        _api_key=args.llm_api_key or getpass.getpass('请输入API密钥: ') if not args.test_mode else 'sk-cefbdbc8fcfa4d05be9c8f480f602df6',
        model_name=args.llm_model
    )
    try:
        if args.test_mode:
            print("\033[33m测试模式：使用临时API密钥，配置不会保存\033[0m")
        else:
            llm_config.validate()
    except ValueError as e:
        print(f"LLM配置错误: {str(e)}")
        sys.exit(1)

    organizer = FileOrganizer(
        source_dir=args.source,
        dest_dir=args.destination,
        batch_size=args.batch_size,
        batch_delay=args.delay,
        dry_run=args.dry_run,
        duplicate_action=args.duplicate_action,
        llm_config=llm_config if args.generate else None
    )
    
    try:
        # 如果指定了--generate参数，则生成命令而不是运行整理流程
        if args.generate:
            # 先扫描文件
            all_files = organizer._scan_files()
            file_list = [str(f) for f in all_files]
            
            try:
                commands = organizer.llm_generator.generate_commands(file_list, args.generate)
                print("\n生成的系统命令：")
                for cmd in commands:
                    print(f"• {cmd}")
                    if not args.dry_run:
                        os.system(cmd)
            except Exception as e:
                print(f"LLM指令生成失败: {str(e)}")
                sys.exit(1)
        else:
            # 正常运行整理流程
            organizer.run()
    except KeyboardInterrupt:
        print("\n程序被用户中断。正在安全退出...")
        sys.exit(1)
    except Exception as e:
        print(f"\n发生错误: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()