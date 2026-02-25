"""
配置管理模块

从 .env 文件加载环境变量配置
"""
import os
from pathlib import Path
from typing import Optional


class Config:
    """配置管理类"""
    
    def __init__(self, env_file: str = ".env"):
        # 加载 .env 文件
        self._load_env_file(env_file)
        
        # LLM 配置
        self.llm_api_key: str = os.getenv("LLM_API_KEY", "")
        self.llm_model: str = os.getenv("LLM_MODEL", "deepseek/deepseek-chat")
        self.llm_base_url: str = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
        
        # 目录配置
        self.workspace_dir: str = os.getenv("WORKSPACE_DIR", "./workspace")
        self.memory_storage_path: str = os.getenv("MEMORY_STORAGE_PATH", "./workspace/memory")
        self.reports_dir: str = os.getenv("REPORTS_DIR", "./reports")
        
        # 验证配置
        self._validate()
    
    def _load_env_file(self, env_file: str) -> None:
        """加载 .env 文件"""
        env_path = Path(env_file)
        if not env_path.exists():
            # 尝试加载 .env.example
            example_path = Path(".env.example")
            if example_path.exists():
                print(f"警告：{env_file} 不存在，使用默认配置")
            return
        
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # 跳过注释和空行
                if not line or line.startswith("#"):
                    continue
                
                # 解析 KEY=VALUE
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # 只有环境变量不存在时才设置（允许系统环境变量覆盖）
                    if key not in os.environ:
                        os.environ[key] = value
    
    def _validate(self) -> None:
        """验证配置"""
        if not self.llm_api_key or self.llm_api_key.startswith("sk-your-"):
            print("警告：LLM_API_KEY 未配置或为默认值")
            print("请在 .env 文件中配置你的 API Key")
            print("或设置环境变量：export LLM_API_KEY=sk-xxx")
    
    @property
    def is_llm_configured(self) -> bool:
        """检查 LLM 是否已配置"""
        return bool(self.llm_api_key) and not self.llm_api_key.startswith("sk-your-")
    
    def to_dict(self) -> dict:
        """配置转为字典"""
        return {
            "llm": {
                "api_key": self.llm_api_key[:10] + "..." if self.llm_api_key else "",
                "model": self.llm_model,
                "base_url": self.llm_base_url,
            },
            "workspace": {
                "dir": self.workspace_dir,
                "memory": self.memory_storage_path,
                "reports": self.reports_dir,
            },
        }


# 全局配置实例
_default_config: Optional[Config] = None


def get_config() -> Config:
    """获取全局配置实例"""
    global _default_config
    if _default_config is None:
        _default_config = Config()
    return _default_config


def load_config(env_file: str = ".env") -> Config:
    """加载配置"""
    global _default_config
    _default_config = Config(env_file)
    return _default_config
