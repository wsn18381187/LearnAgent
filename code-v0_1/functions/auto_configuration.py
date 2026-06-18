from dotenv import load_dotenv
from pathlib import Path
import json
import os
import sys
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.shortcuts import choice
from prompt_toolkit.history import FileHistory
from prompt_toolkit import PromptSession

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

class HotConfig:
    def __init__(self, config_path:str=CONFIG_PATH):
        self.config_path = config_path
        self._cache = {}
        self._mtime = 0
    
    def _refresh_if_needed(self):
        current_mtime = Path(self.config_path).stat().st_mtime
        if current_mtime > self._mtime:
            with open(self.config_path, 'r') as f:
                self._cache = json.load(f)
            self._mtime = current_mtime

    def get(self, key:str, default=None):
        current_mtime = Path(self.config_path).stat().st_mtime
        if current_mtime > self._mtime:
            with open(self.config_path, 'r') as f:
                self._cache = json.load(f)
            self._mtime = current_mtime
        return self._cache.get(key, default)
    
    def set(self, key:str, value):
        self._refresh_if_needed()
        self._cache[key] = value
        with open(self.config_path, 'w') as f:
            json.dump(self._cache, f, indent=4, ensure_ascii=False)
        self._mtime = Path(self.config_path).stat().st_mtime

    def reload(self):
        self._mtime = 0
        self._refresh_if_needed()


config = HotConfig()

# --- prompt_toolkit 辅助 ---

_history_path = os.path.join(BASE_DIR, '.config_value_history')
_value_session = PromptSession(history=FileHistory(_history_path))


def _build_choice_options(config_keys: list) -> list:
    """构建 choice 选项列表，包含所有配置项 + 操作选项。"""
    options = []
    for key in config_keys:
        value = config.get(key)
        display_value = str(value) if value is not None else "(not set)"
        if len(display_value) > 50:
            display_value = display_value[:47] + "..."
        options.append((
            key,
            HTML(f'<ansicyan>{key}</ansicyan>  <ansigray>→ {display_value}</ansigray>')
        ))
    # add new config function temporary not open 
    #options.append(("__ADD_NEW__", HTML('<ansigray>────────  ✚ Add new key  ────────</ansigray>')))
    options.append(("__DONE__", HTML('<ansigreen>────────  ✓ Done / Exit  ────────</ansigreen>')))
    return options


def _prompt_new_value(key: str, current_value) -> str | None:
    """用 prompt_toolkit 输入新值，返回 None 表示取消。"""
    display_current = str(current_value) if current_value is not None else "(not set)"
    print(f"\033[90mCurrent [{key}]: {display_current}\033[0m")
    print(f"\033[90mPress input ':q' to cancel.\033[0m")
    try:
        new_value = _value_session.prompt(
            HTML(f'<ansicyan>New value for <b>{key}</b></ansicyan> <ansigray>></ansigray> '),
        )
        if new_value.strip() == ':q':
            return None
        return new_value
    except (KeyboardInterrupt, EOFError):
        return None


def validate_config() -> bool:
    required_keys = {
        "API_KEY": "",
        "BASE_URL": "",
        "WEAKER_MODEL_NAME": "",
        "STRONGER_MODEL_NAME": "",
    }
    missing = []
    for key, empty_value in required_keys.items():
        current_value = config.get(key)
        if current_value is None or current_value == empty_value:
            missing.append(key)
    if missing:
        print(f"\033[33m[Config Warning] The following required configs are not set:\033[0m")
        for key in missing:
            print(f"  - {key}")
        print(f"\033[33mPlease complete them before starting.\033[0m")
        return False
    return True

def get_config(config_name:str) -> str:
    return config.get(config_name, "config not found")

def show_current_config() -> None:
    base_url = config.get('BASE_URL')
    weaker_model_name = config.get('WEAKER_MODEL_NAME')
    weaker_extra_body = config.get('WEAKER_EXTRA_BODY')
    stronger_model_name = config.get('STRONGER_MODEL_NAME')
    stronger_extra_body = config.get('STRONGER_EXTRA_BODY')
    print(f"\033[90mBase URL ------------------- {base_url}\033[0m")
    print(f"\033[90mWeaker Model --------------- {weaker_model_name}\033[0m")
    if weaker_extra_body != None: 
        print(f"\033[90mWeaker Model Extra Body ---- {weaker_extra_body}\033[0m")
    print(f"\033[90mStronger Model ------------- {stronger_model_name}\033[0m")
    if stronger_extra_body != None:
        print(f"\033[90mStronger Model Extra Body -- {stronger_extra_body}\033[0m")
    print(f"\033[90mAuto Read Mode ------------- {config.get('AUTO_READ_MODE')}\033[0m")
    print(f"\033[90mAuto Edit Mode ------------- {config.get('AUTO_EDIT_MODE')}\033[0m")
    print(f"\033[90mAuto Execute Mode ---------- {config.get('AUTO_EXECUTE_MODE')}\033[0m")


def set_config() -> None:
    """使用 prompt_toolkit choice 优化后的配置设置交互。"""
    
    while True:
        config._refresh_if_needed()
        keys = list(config._cache.keys())
        options = _build_choice_options(keys)
        
        selected = choice(
            message=HTML(
                '<ansicyan>Config Settings</ansicyan>  '
                '<ansigray>(↑↓ to navigate, Enter to select)</ansigray>'
            ),
            options=options,
            default=keys[0] if keys else "__ADD_NEW__",
            bottom_toolbar=HTML(
                ' <ansigray>↑↓ Move</ansigray>  '
                '<ansigray>Enter Select</ansigray>  '
                '<ansigray>Ctrl+C Quit</ansigray>'
            ),
        )
        
        if selected == "__DONE__":
            print("\033[32mConfig updated. Exiting.\033[0m")
            break
        
        if selected == "__ADD_NEW__":
            print(f"\033[90mPress Ctrl+C or input ':q' to cancel.\033[0m")
            try: 
                new_key = _value_session.prompt(
                    HTML('<ansicyan>New key name</ansicyan> <ansigray>></ansigray> '),
                )
                if new_key.strip() == ':q' or not new_key.strip():
                    continue
                new_value = _prompt_new_value(new_key, None)
                if new_value is not None:
                    config.set(new_key.strip(), new_value)
                    print(f"\033[32m✓ [{new_key.strip()}] added!\033[0m")
            except (KeyboardInterrupt, EOFError):
                continue
            continue
        
        current_value = config.get(selected)
        new_value = _prompt_new_value(selected, current_value)
        if new_value is not None:
            config.set(selected, new_value)
            print(f"\033[32m✓ [{selected}] updated!\033[0m")
        else:
            print(f"\033[90m✗ [{selected}] cancelled, value unchanged.\033[0m")
    



def weaker_model_configuration() -> list:
    return [
        config.get('BASE_URL'), 
        config.get('API_KEY'), 
        config.get('WEAKER_MODEL_NAME'), 
        config.get('WEAKER_EXTRA_BODY')
    ]

def stronger_model_configuration() -> list:
    return [
        config.get('BASE_URL'), 
        config.get('API_KEY'), 
        config.get('STRONGER_MODEL_NAME'), 
        config.get('STRONGER_EXTRA_BODY')
    ]