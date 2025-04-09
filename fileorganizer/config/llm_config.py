import os
from dataclasses import dataclass
from cryptography.fernet import Fernet

@dataclass
class LLMConfig:
    """大语言模型配置类"""
    provider: str = 'deepseek'
    _api_key: str = os.getenv('LLM_API_KEY', '')
    model_name: str = 'deepseek-chat'
    temperature: float = 0.3
    max_tokens: int = 2000
    
    @property
    def api_key(self):
        """解密存储的API密钥"""
        if not hasattr(self, '_cipher') or not self._api_key:
            return self._api_key
        return self._cipher.decrypt(self._api_key.encode()).decode()
    
    @api_key.setter
    def api_key(self, value):
        """加密并存储API密钥"""
        if not hasattr(self, '_cipher'):
            key = os.getenv('FERNET_KEY')
            if not key:
                raise ValueError("未配置加密密钥，请通过环境变量FERNET_KEY设置")
            self._cipher = Fernet(key.encode())
        self._api_key = self._cipher.encrypt(value.encode()).decode()

    def validate(self):
        if not os.getenv('FERNET_KEY'):
            raise ValueError("未配置加密密钥，请通过环境变量FERNET_KEY设置")
        if not self._api_key:
            raise ValueError("未配置LLM API密钥，请通过环境变量LLM_API_KEY或命令行参数设置")
        if self.provider not in ['deepseek']:
            raise ValueError(f"不支持的LLM提供商: {self.provider}")