"""
AI分镜生成器 - 主入口
模块化结构，便于维护和扩展
"""
import sys
from pathlib import Path

import streamlit as st

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent

sys.path.insert(0, str(PROJECT_ROOT))
# 🚀 核心修复：将页面配置放在入口脚本的最前面
from config.settings import PAGE_CONFIG

st.set_page_config(**PAGE_CONFIG)

# 必须在 set_page_config 之后导入其他包含 st 命令的模块
from ui.main_app import main

if __name__ == "__main__":
    main()
