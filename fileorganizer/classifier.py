"""
文件分类器模块
负责根据文件类型和名称对文件进行分类
"""
import os
import re
import mimetypes
from pathlib import Path
from typing import Optional, Dict, List, Tuple

# 初始化MIME类型
mimetypes.init()

class FileClassifier:
    """文件分类器类"""
    
    def __init__(self):
        """初始化文件分类器"""
        # 文件类型到分类的映射
        self.type_categories = {
            # 视频文件
            'video': {
                'path': Path('视频'),
                'extensions': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v'],
                'mime_types': ['video/'],
                'subcategories': {
                    'movies': {
                        'path': Path('电影'),
                        'patterns': [
                            r'\(\d{4}\)',  # 带年份的电影，如 "电影名 (2023)"
                            r'\[\d{4}\]',  # 带年份的电影，如 "电影名 [2023]"
                            r'\d{4}\.',    # 带年份的电影，如 "电影名.2023."
                        ]
                    },
                    'tv_shows': {
                        'path': Path('电视剧'),
                        'patterns': [
                            r'S\d+E\d+',   # 如 "剧名 S01E01"
                            r'第\d+季',     # 如 "剧名 第1季"
                            r'第\d+集',     # 如 "剧名 第1集"
                        ]
                    },
                    'unknown': {
                        'path': Path('A待检查'),
                        'patterns': []
                    }
                }
            },
            
            # 音频文件
            'audio': {
                'path': Path('音乐'),
                'extensions': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a'],
                'mime_types': ['audio/'],
                'subcategories': {
                    'albums': {
                        'path': Path('专辑'),
                        'patterns': [
                            r'专辑',
                            r'album',
                            r'OST',
                        ]
                    },
                    'singles': {
                        'path': Path('单曲'),
                        'patterns': [
                            r'-',  # 歌曲名-歌手名
                            r'_',  # 歌曲名_歌手名
                        ]
                    },
                    'unknown': {
                        'path': Path('A待检查'),
                        'patterns': []
                    }
                }
            },
            
            # 文档文件
            'document': {
                'path': Path('文档'),
                'extensions': ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.md'],
                'mime_types': ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument', 'text/'],
                'subcategories': {
                    'papers': {
                        'path': Path('论文'),
                        'patterns': [
                            r'论文',
                            r'paper',
                            r'thesis',
                            r'dissertation',
                            r'research',
                        ]
                    },
                    'books': {
                        'path': Path('书籍'),
                        'patterns': [
                            r'book',
                            r'书',
                            r'小说',
                            r'manual',
                            r'guide',
                        ]
                    },
                    'reports': {
                        'path': Path('报告'),
                        'patterns': [
                            r'report',
                            r'报告',
                            r'总结',
                            r'分析',
                        ]
                    },
                    'unknown': {
                        'path': Path('A待检查'),
                        'patterns': []
                    }
                }
            },
            
            # 图片文件
            'image': {
                'path': Path('图片'),
                'extensions': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'],
                'mime_types': ['image/'],
                'subcategories': {
                    'photos': {
                        'path': Path('照片'),
                        'patterns': [
                            r'IMG_\d+',  # 相机照片常见格式
                            r'DSC\d+',   # 相机照片常见格式
                            r'DCIM',     # 相机照片常见格式
                            r'photo',
                            r'照片',
                        ]
                    },
                    'screenshots': {
                        'path': Path('截图'),
                        'patterns': [
                            r'screenshot',
                            r'截图',
                            r'屏幕截图',
                            r'Screen Shot',
                        ]
                    },
                    'unknown': {
                        'path': Path('A待检查'),
                        'patterns': []
                    }
                }
            },
            
            # 压缩文件
            'archive': {
                'path': Path('压缩文件'),
                'extensions': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'],
                'mime_types': ['application/zip', 'application/x-rar-compressed', 'application/x-7z-compressed', 'application/x-tar', 'application/gzip'],
                'subcategories': {
                    'unknown': {
                        'path': Path('A待检查'),
                        'patterns': []
                    }
                }
            },
            
            # 默认分类
            'unknown': {
                'path': Path('其他'),
                'extensions': [],
                'mime_types': [],
                'subcategories': {
                    'unknown': {
                        'path': Path('A待检查'),
                        'patterns': []
                    }
                }
            }
        }
    
    def classify_file(self, file_path: Path) -> Optional[Path]:
        """
        根据文件类型和名称对文件进行分类
        
        Args:
            file_path: 文件路径
            
        Returns:
            分类路径，如果无法分类则返回None
        """
        # 获取文件扩展名和MIME类型
        file_ext = file_path.suffix.lower()
        mime_type, _ = mimetypes.guess_type(str(file_path))
        
        # 确定主分类
        main_category = self._get_main_category(file_path, file_ext, mime_type)
        
        # 确定子分类
        sub_category = self._get_sub_category(file_path, main_category)
        
        # 构建完整分类路径
        if main_category and sub_category:
            return main_category['path'] / sub_category['path']
        
        return None
    
    def _get_main_category(self, file_path: Path, file_ext: str, mime_type: Optional[str]) -> Dict:
        """确定文件的主分类"""
        for category_name, category_info in self.type_categories.items():
            # 跳过默认分类
            if category_name == 'unknown':
                continue
            
            # 通过扩展名匹配
            if file_ext in category_info['extensions']:
                return category_info
            
            # 通过MIME类型匹配
            if mime_type:
                for mime_pattern in category_info['mime_types']:
                    if mime_type.startswith(mime_pattern):
                        return category_info
        
        # 如果没有匹配到，返回默认分类
        return self.type_categories['unknown']
    
    def _get_sub_category(self, file_path: Path, main_category: Dict) -> Dict:
        """确定文件的子分类"""
        file_name = file_path.name.lower()
        
        for sub_name, sub_info in main_category['subcategories'].items():
            # 跳过默认子分类
            if sub_name == 'unknown':
                continue
            
            # 通过模式匹配
            for pattern in sub_info['patterns']:
                if re.search(pattern, file_name, re.IGNORECASE):
                    return sub_info
        
        # 如果没有匹配到，返回默认子分类
        return main_category['subcategories']['unknown']