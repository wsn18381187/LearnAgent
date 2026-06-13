from dotenv import load_dotenv
from pathlib import Path
import json
import os
import sys

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


def set_config() -> None:
    items = list(config._cache.keys())

    def get_valid_opnum():
        while True:
            print(f"\033[90mCurrent configs below. 1~{len(items)} to choose, 0 to exit config set.\033[0m")
            for i, key in enumerate(items, 1):
                print(f"{i}:{key}")
            opnum = input("\033[34m>\033[0m ").strip()
            if opnum.isdigit() and 0 <= int(opnum) <= len(items):
                return int(opnum)
            else:
                print(f"\033[33m[Info] Please input a valid integer! 0 to exit config set.\033[0m")
    
    opnum = get_valid_opnum()
    
    while opnum != 0:
        item_num = opnum - 1
        print(f"\033[90mCurrent {items[item_num]}: {config.get(items[item_num])}. Input '0' to cancel edit.\033[0m")
        new_value = input(f"Input new {items[item_num]} \033[34m>\033[0m ").strip()
        if new_value != "0":
            config.set(items[item_num], new_value)
            print(f"\033[32mNew {items[item_num]}: {config.get(items[item_num])} set!\033[0m")
        opnum = get_valid_opnum()
    



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