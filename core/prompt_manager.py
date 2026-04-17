import json
import os
import datetime
import logging
from enum import Enum
from core.prompts import PromptTemplates

logger = logging.getLogger("ScriptMaster.PromptManager")


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
    HISTORY_FILE = "config/prompt_history.json"  # 📜 新增：历史记录文件路径

    # ================= 📜 历史记录专区 =================
    @classmethod
    def log_action(cls, action: str, details: str):
        """记录关键操作到历史日志"""
        os.makedirs("config", exist_ok=True)
        history = cls.get_history()

        entry = {
            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "action": action,
            "details": details
        }
        history.insert(0, entry)  # 最新操作插在最前面
        history = history[:50]  # 限制最多保留 50 条，防止文件无限膨胀

        try:
            with open(cls.HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logger.error(f"写入历史记录失败: {e}")

    @classmethod
    def get_history(cls) -> list:
        """获取历史记录列表"""
        if os.path.exists(cls.HISTORY_FILE):
            try:
                with open(cls.HISTORY_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return []

    @classmethod
    def clear_history(cls):
        """清空历史记录"""
        if os.path.exists(cls.HISTORY_FILE):
            try:
                os.remove(cls.HISTORY_FILE)
            except:
                pass

    # ================= 核心业务逻辑 =================
    @classmethod
    def get(cls, key: str) -> str:
        """获取提示词"""
        key_str = key.value if isinstance(key, Enum) else str(key)

        if os.path.exists(cls.CONFIG_FILE):
            try:
                with open(cls.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    custom_data = json.load(f)
                    if key_str in custom_data:
                        return custom_data[key_str]
            except Exception:
                pass
        return getattr(PromptTemplates, key_str, "")

    @classmethod
    def load_all(cls) -> dict:
        """加载所有自定义提示词"""
        if os.path.exists(cls.CONFIG_FILE):
            try:
                with open(cls.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    @classmethod
    def update(cls, key: str, content: str):
        """保存自定义提示词"""
        key_str = key.value if isinstance(key, Enum) else str(key)
        os.makedirs("config", exist_ok=True)

        data = cls.load_all()
        data[key_str] = content

        with open(cls.CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        # 📝 核心改动：成功保存后记录日志
        cls.log_action("🚀 部署配置", f"更新了模块 [{key_str}]")

    @classmethod
    def reset(cls, key: str):
        """重置提示词为官方默认"""
        key_str = key.value if isinstance(key, Enum) else str(key)
        data = cls.load_all()

        if key_str in data:
            del data[key_str]
            with open(cls.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

            # 📝 核心改动：成功重置后记录日志
            cls.log_action("🔄 还原配置", f"将模块 [{key_str}] 恢复为系统默认")