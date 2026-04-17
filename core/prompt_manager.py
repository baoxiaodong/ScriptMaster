import json
import os
from enum import Enum
from core.prompts import PromptTemplates


class PromptKeys(str, Enum):
    """定义所有提示词资产的唯一 ID 常量"""
    SCRIPT_SYSTEM = "SCRIPT_SYSTEM"
    OUTLINE_TASK = "OUTLINE_TASK"
    OUTLINE_SYSTEM = "OUTLINE_SYSTEM"
    BATCH_SCRIPT_PROMPT = "BATCH_SCRIPT_PROMPT"
    ACT_GEN_SYSTEM = "ACT_GEN_SYSTEM"
    ACT_GEN_TASK = "ACT_GEN_TASK"
    SCRIPT_TASK_TEMPLATE = "SCRIPT_TASK_TEMPLATE"


class PromptManager:
    CONFIG_FILE = "config/custom_prompts.json"

    @classmethod
    def get(cls, key: str) -> str:
        """使用常量 Key 获取提示词"""
        if os.path.exists(cls.CONFIG_FILE):
            try:
                with open(cls.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    custom_data = json.load(f)
                    if key in custom_data:
                        return custom_data[key]
            except:
                pass
        # 兜底：从原生 PromptTemplates 类中按属性名读取
        return getattr(PromptTemplates, key, "")

    @classmethod
    def update(cls, key: str, content: str):
        os.makedirs("config", exist_ok=True)
        data = cls.load_all()
        data[key] = content
        with open(cls.CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    @classmethod
    def load_all(cls):
        if os.path.exists(cls.CONFIG_FILE):
            with open(cls.CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    @classmethod
    def reset(cls, key: str):
        data = cls.load_all()
        if key in data:
            del data[key]
            with open(cls.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
