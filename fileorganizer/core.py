"""
FileOrganizer 核心功能模块
"""
import os
import time
import shutil
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Set, Tuple
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from fileorganizer.classifier import FileClassifier
from fileorganizer.duplicates import DuplicateDetector
from fileorganizer.config.llm_config import LLMConfig
import json
import requests

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fileorganizer.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("FileOrganizer")

class FileOrganizer:
    """文件整理器主类"""
    
    def __init__(self, source_dir: str, dest_dir: str, batch_size: int = 100, 
                 batch_delay: float = 1.0, dry_run: bool = False,
                 duplicate_action: str = 'ask', llm_config=None):
        """
        初始化文件整理器
        
        Args:
            source_dir: 源文件夹路径
            dest_dir: 目标文件夹路径
            batch_size: 每批处理的文件数量
            batch_delay: 批次间延迟时间(秒)
            dry_run: 是否模拟运行(不实际移动文件)
            duplicate_action: 重复文件处理方式('keep-first', 'keep-newest', 'ask')
            llm_config: 大语言模型配置
        """
        # 转换路径并验证存在性
        self.source_dir = Path(source_dir).resolve()  # 恢复正确的路径解析
        self.dest_dir = Path(dest_dir).resolve()
    
        if not self.source_dir.exists():
            raise ValueError(f"源目录不存在: {self.source_dir}")
        if not self.dest_dir.exists() and not dry_run:  # dry_run时不强制目标目录存在
            raise ValueError(f"目标目录不存在: {self.dest_dir}")
        
        self.source_dir = Path(source_dir)
        self.dest_dir = Path(dest_dir)
        self.batch_size = batch_size
        self.batch_delay = batch_delay
        self.dry_run = dry_run
        self.duplicate_action = duplicate_action
        self.llm_config = llm_config
        
        # 初始化LLM指令生成器（如果提供了配置）
        self.llm_generator = LLMCommandGenerator(llm_config) if llm_config else None
        
        # 确保目标目录存在
        if not self.dry_run:
            os.makedirs(self.dest_dir, exist_ok=True)
        
        # 初始化分类器和重复检测器
        self.classifier = FileClassifier()
        self.duplicate_detector = DuplicateDetector()
        
        # 任务ID用于标记无法识别的文件
        self.task_id = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # 统计信息
        self.stats = {
            'total_files': 0,
            'processed_files': 0,
            'moved_files': 0,
            'duplicate_files': 0,
            'unrecognized_files': 0,
            'error_files': 0
        }
    
    def run(self):
        """运行文件整理流程"""
        logger.info(f"开始整理文件: 源目录 '{self.source_dir}' -> 目标目录 '{self.dest_dir}'")
        YELLOW = '\033[33m'
        GREEN = '\033[32m'
        RESET = '\033[0m'
        mode_str = f"{YELLOW}模拟运行{RESET}" if self.dry_run else f"{GREEN}实际运行{RESET}"
        logger.info(f"模式: {mode_str}")

        logger.info(f"目标目录: {self.dest_dir}")
        
        # 1. 扫描源目录下的所有文件
        all_files = self._scan_files()
        self.stats['total_files'] = len(all_files)
        logger.info(f"共发现 {self.stats['total_files']} 个文件")
        
        # 2. 检测重复文件
        duplicates = self._detect_duplicates(all_files)
        logger.info(f"发现 {len(duplicates)} 组重复文件")
        
        # 3. 处理重复文件，获取需要保留的文件
        files_to_keep = self._handle_duplicates(duplicates, all_files)
        
        # 4. 分批处理文件
        self._process_files_in_batches(files_to_keep)
        
        # 5. 输出统计信息
        if self.dry_run:
            logger.info("\033[33m注意：当前为模拟运行模式，未执行实际文件操作\033[0m")
        self._print_stats()
    
    def _scan_files(self) -> List[Path]:
        """扫描源目录下的所有文件"""
        logger.info("正在扫描文件...")
        all_files = []
        
        for root, _, files in os.walk(self.source_dir):
            for file in files:
                file_path = Path(root) / file
                if file_path.is_file():
                    all_files.append(file_path)
        
        return all_files
    
    def _detect_duplicates(self, files: List[Path]) -> Dict[str, List[Path]]:
        """检测重复文件"""
        logger.info("正在检测重复文件...")
        return self.duplicate_detector.find_duplicates(files)
    
    def _handle_duplicates(self, duplicates: Dict[str, List[Path]], all_files: List[Path]) -> Set[Path]:
        """处理重复文件，返回需要保留的文件集合"""
        files_to_keep = set(all_files)
        
        for hash_value, dup_files in duplicates.items():
            if len(dup_files) <= 1:
                continue
            
            self.stats['duplicate_files'] += len(dup_files) - 1
            
            # 根据策略选择要保留的文件
            if self.duplicate_action == 'keep-first':
                file_to_keep = dup_files[0]
            elif self.duplicate_action == 'keep-newest':
                file_to_keep = max(dup_files, key=lambda f: f.stat().st_mtime)
            else:  # 'ask'
                # 在MVP版本中简化为保留第一个文件
                file_to_keep = dup_files[0]
                logger.info(f"发现重复文件组: {[str(f) for f in dup_files]}")
                logger.info(f"自动保留: {file_to_keep}")
            
            # 从保留集合中移除不需要的文件
            for file in dup_files:
                if file != file_to_keep:
                    files_to_keep.remove(file)
        
        return files_to_keep
    
    def _process_files_in_batches(self, files: Set[Path]):
        """分批处理文件"""
        logger.info("开始分批处理文件...")
        
        # 将文件列表转换为列表并分批
        file_list = list(files)
        total_batches = (len(file_list) + self.batch_size - 1) // self.batch_size
        
        for batch_idx in range(total_batches):
            start_idx = batch_idx * self.batch_size
            end_idx = min(start_idx + self.batch_size, len(file_list))
            batch_files = file_list[start_idx:end_idx]
            
            logger.info(f"处理批次 {batch_idx + 1}/{total_batches} ({len(batch_files)} 个文件)")
            
            # 使用线程池处理当前批次的文件
            with ThreadPoolExecutor(max_workers=min(10, len(batch_files))) as executor:
                for file in batch_files:
                    executor.submit(self._process_single_file, file)
            
            self.stats['processed_files'] += len(batch_files)
            
            # 批次间延迟
            if batch_idx < total_batches - 1 and self.batch_delay > 0:
                logger.info(f"批次间休息 {self.batch_delay} 秒...")
                time.sleep(self.batch_delay)
    
    def _process_single_file(self, file_path: Path):
        """处理单个文件"""
        try:
            # 获取文件分类信息
            category_path = self.classifier.classify_file(file_path)
            
            # 如果无法识别，放入待检查目录
            if category_path is None:
                category_path = Path("待检查") / "A待检查"
                # 添加任务ID到文件名
                new_filename = f"{file_path.stem}_task{self.task_id}{file_path.suffix}"
                self.stats['unrecognized_files'] += 1
            else:
                new_filename = file_path.name
            
            # 构建目标路径
            dest_path = self.dest_dir / category_path
            full_dest_path = dest_path / new_filename
            
            if self.dry_run:
                logger.debug(f"[模拟] 将移动文件到: {full_dest_path}")
            else:
                logger.info(f"正在移动文件到: {full_dest_path}")
            
            # 确保目标目录存在
            if not self.dry_run:
                os.makedirs(dest_path, exist_ok=True)
            
            # 移动文件
            if not self.dry_run:
                # 处理目标文件已存在的情况
                if full_dest_path.exists():
                    # 在文件名后添加时间戳
                    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                    new_filename = f"{file_path.stem}_{timestamp}{file_path.suffix}"
                    full_dest_path = dest_path / new_filename
                
                shutil.move(str(file_path), str(full_dest_path))
                self.stats['moved_files'] += 1
            
            logger.debug(f"已处理: {file_path} -> {full_dest_path}")
            
        except Exception as e:
            logger.error(f"处理文件 {file_path} 时出错: {e}")
            self.stats['error_files'] += 1
    
    def _print_stats(self):
        """打印统计信息"""
        logger.info("\n" + "="*50)
        logger.info("文件整理完成! 统计信息:")
        logger.info(f"总文件数: {self.stats['total_files']}")
        logger.info(f"已处理文件: {self.stats['processed_files']}")
        logger.info(f"已移动文件: {self.stats['moved_files']}")
        logger.info(f"重复文件: {self.stats['duplicate_files']}")
        logger.info(f"无法识别的文件: {self.stats['unrecognized_files']}")
        logger.info(f"处理出错的文件: {self.stats['error_files']}")
        logger.info("="*50)


class LLMCommandGenerator:
    """大语言模型指令生成器"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.template_dir = Path(__file__).parent.parent / 'prompt_templates'

    def _load_template(self, template_name: str) -> dict:
        """加载提示词模板"""
        template_path = self.template_dir / f"{template_name}.json"
        with open(template_path, 'r') as f:
            return json.load(f)

    def generate_commands(self, file_list: list, mode: str) -> list:
        """生成系统命令"""
        template = self._load_template(f'generate_{mode}')
        
        response = requests.post(
            url='https://api.deepseek.com/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {self.config.api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'deepseek-chat',
                'messages': [
                    {'role': 'system', 'content': template['system_prompt']},
                    {'role': 'user', 'content': template['user_prompt'].format(file_list=file_list)}
                ],
                'temperature': self.config.temperature,
                'max_tokens': self.config.max_tokens
            }
        )
        
        try:
            return json.loads(response.json()['choices'][0]['message']['content'])['commands']
        except (KeyError, json.JSONDecodeError) as e:
            raise ValueError(f"LLM响应解析失败: {str(e)}")

        # LLM指令生成功能在CLI层处理，此处不再需要