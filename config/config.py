import json
import logging
import re
import copy
from pathlib import Path
from typing import Any
import yaml

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None

logger = logging.getLogger('saka.config')

class BotConfig:

    def __init__(self, config_path: str | Path | None = None) -> None:
        current_dir = Path(__file__).resolve().parent
        
        self._config_dir = Path(config_path).resolve() if config_path else current_dir
        
        self._exclude_files = {"config.py", ".env.example"}
        self._exclude_dirs = {".git", ".venv", "__pycache__"}

        self._data: dict[str, Any] = {}

        if not self._config_dir.exists() or not self._config_dir.is_dir():
            logger.error(f"❌ Diretório de configuração não encontrado ou inválido: {self._config_dir}")
            return

        self._load_all_configs()

    def __getattr__(self, item: str) -> Any:
        if item in self._data:
            
            value = self._data[item]
            return copy.deepcopy(value) if isinstance(value, (dict, list, set)) else value
            
        raise AttributeError(f"Configuração '{item}' não existe ou falhou ao carregar.")

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return getattr(self, key)
        except AttributeError:
            return default

    def reload(self) -> None:
        logger.info("🔄 Recarregando configurações do bot...")
        self._data.clear()
        self._load_all_configs()

    def _sanitize_name(self, name: str) -> str:
        base_name = name.lower()
        base_name = re.sub(r'[\s\-]+', '_', base_name)
        base_name = re.sub(r'[^a-z0-9_]', '', base_name)

        if base_name and base_name[0].isdigit():
            base_name = f"config_{base_name}"

        return base_name

    def _generate_key(self, file_path: Path) -> str:
        rel_path = file_path.relative_to(self._config_dir)
        key_parts = [self._sanitize_name(part) for part in rel_path.parent.parts]
        key_parts.append(self._sanitize_name(file_path.stem))
        return "_".join(filter(None, key_parts))

    def _load_all_configs(self) -> None:
        supported_extensions = {'.txt', '.json', '.yaml', '.yml', '.toml'}

        for file_path in self._config_dir.rglob('*'):
            if not file_path.is_file():
                continue

            if any(part in self._exclude_dirs for part in file_path.parts):
                continue

            if file_path.name in self._exclude_files or file_path.suffix.lower() not in supported_extensions:
                continue

            key = self._generate_key(file_path)

            if not key:
                continue

            if key in self._data:
                logger.warning(f"⚠️ Conflito de chaves: A chave '{key}' já existe. '{file_path.name}' será ignorado.")
                continue

            self._process_file(file_path, key)

    def _process_file(self, file_path: Path, key: str) -> None:
        try:
            raw_content = file_path.read_text(encoding="utf-8").strip()
            if not raw_content:
                logger.warning(f"⚠️ Arquivo vazio ignorado: {file_path.relative_to(self._config_dir)}")
                return

            suffix = file_path.suffix.lower()
            
            if suffix == '.txt':
                self._data[key] = raw_content
            elif suffix == '.json':
                self._data[key] = json.loads(raw_content)
            elif suffix in ('.yaml', '.yml'):
                self._data[key] = yaml.safe_load(raw_content)
            elif suffix == '.toml':
                if tomllib is None:
                    logger.error(f"❌ Biblioteca 'tomli' ausente. Impossível ler {file_path.name}.")
                    return
                self._data[key] = tomllib.loads(raw_content)

            logger.debug(f"✅ Carregado: {file_path.relative_to(self._config_dir)} -> bot_config.{key}")

        except UnicodeDecodeError:
            logger.error(f"❌ Erro de codificação (UTF-8 inválido) no arquivo: {file_path}")
        except (json.JSONDecodeError, yaml.YAMLError) as e:
            logger.error(f"❌ Erro de sintaxe no arquivo {file_path}: {e}")
        except Exception as e:
            logger.error(f"❌ Erro crítico ao ler {file_path}: {e.__class__.__name__}: {e}")

    def get_all(self) -> dict[str, Any]:
        return copy.deepcopy(self._data)

bot_config = BotConfig()
