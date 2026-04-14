"""
AI分镜生成器 - 主入口
模块化结构，便于维护和扩展
"""
import streamlit as st
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent
import sys
sys.path.insert(0, str(PROJECT_ROOT))

from ui.main_app import main

if __name__ == "__main__":
    main()
