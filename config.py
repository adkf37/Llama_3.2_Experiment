import yaml
from typing import Dict, Any
from pathlib import Path

class Config:
    """Configuration manager for the Llama RAG system."""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation (e.g., 'model.temperature')."""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value using dot notation."""
        keys = key.split('.')
        config_ref = self._config
        
        for k in keys[:-1]:
            if k not in config_ref:
                config_ref[k] = {}
            config_ref = config_ref[k]
        
        config_ref[keys[-1]] = value
    
    def save(self) -> None:
        """Save current configuration to file."""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(self._config, f, default_flow_style=False)
    
    @property
    def model_config(self) -> Dict[str, Any]:
        """Get model configuration section."""
        return self._config.get('model', {})
    
    @property
    def rag_config(self) -> Dict[str, Any]:
        """Get RAG configuration section."""
        return self._config.get('rag', {})
    
    @property
    def vectordb_config(self) -> Dict[str, Any]:
        """Get vector database configuration section."""
        return self._config.get('vectordb', {})
    
    @property
    def app_config(self) -> Dict[str, Any]:
        """Get application configuration section."""
        return self._config.get('app', {})

# Global config instance
config = Config()
