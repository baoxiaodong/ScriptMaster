"""
主应用模块 - ScriptMaster 核心入口
"""
import time

import streamlit as st
# 1. 必须是整个脚本中第一个执行的 Streamlit 命令
from config.settings import PAGE_CONFIG, CUSTOM_CSS, setup_logger

try:
    st.set_page_config(**PAGE_CONFIG)
except Exception:
    pass

from ui.components.script_generator import render_script_generation_mode
from ui.components.sidebar import render_sidebar
from ui.components.novel_excel_mode import render_novel_excel_mode
from utils.file_handler import FileHandler
from utils.state_manager import StateManager
from config.settings import NOVEL_MODE_NAME, SCRIPT_MODE_NAME

# 🛡️ 导入全局错误处理工具
from utils.error_handler import error_handler

# 🌟 日志器配置
logger = setup_logger("ScriptMaster")


def init_app():
    """初始化应用基础配置"""
    # 注入全局 CSS
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    # 初始化业务状态（仅在会话开始时执行一次）
    if 'app_initialized' not in st.session_state:
        logger.info("🎬 [System] ScriptMaster~AI小说分镜工坊 - 正在启动...")
        StateManager.init()
        st.session_state['_last_mode'] = None
        st.session_state.app_initialized = True
        logger.info("✅ [System] 基础状态初始化完成")


def render_header():
    """渲染品牌 Banner"""
    st.markdown(
        '<div class="hermes-banner">'
        '<p class="banner-title">'
        'ScriptMaster~AI小说分镜工坊'
        '<span class="hermes-badge">Hermes Orange Theme</span>'
        '</p>'
        '<p class="banner-sub">'
        '小说一键生成专业分镜脚本 · 支持多模型 AI · 批量并行处理'
        '</p>'
        '</div>',
        unsafe_allow_html=True
    )


def main():
    """主程序入口"""
    start_time = time.time()

    # 执行基础初始化
    init_app()

    # 获取业务实例
    llm_service = StateManager.get_llm_service()
    file_handler = FileHandler()

    # A. 渲染侧边栏
    try:
        provider, api_key, model_name = render_sidebar(llm_service)
    except Exception as e:
        st.sidebar.error(f"⚠️ 侧边栏加载失败: {str(e)[:60]}")
        provider, api_key, model_name = "Mock (演示)", "", ""
        llm_service.configure(provider, api_key, model_name)
        logger.error(f"❌ [Sidebar] 侧边栏渲染异常: {str(e)}", exc_info=True)

    # 同步配置
    if st.session_state.get('_provider') != provider:
        logger.info(f"⚙️ [Config] 模型服务商变更为: {provider}")
    st.session_state['_provider'] = provider
    st.session_state['_api_key'] = api_key

    # B. 渲染主内容区
    render_header()

    st.markdown('<p class="step-title" style="margin-bottom:10px;">选择工作模式</p>', unsafe_allow_html=True)
    current_mode = st.radio(
        "切换模式",
        [NOVEL_MODE_NAME, SCRIPT_MODE_NAME],
        label_visibility="collapsed",
        horizontal=True,
        key="app_mode_selector"
    )

    if st.session_state.get('_last_mode') != current_mode:
        logger.info(f"🔄 [Router] 用户切换视图: {st.session_state.get('_last_mode')} -> {current_mode}")
        st.session_state['_last_mode'] = current_mode

    st.divider()

    # 渲染具体业务组件
    try:
        if current_mode == NOVEL_MODE_NAME:
            render_novel_excel_mode(llm_service, file_handler)
        else:
            render_script_generation_mode(llm_service)
    except Exception as e:
        error_handler.handle_exception(
            exception=e,
            context="MainApp-Render",
            show_page=True,
            reset_callback=error_handler.create_reset_handler()
        )

    # 记录性能
    total_duration = time.time() - start_time
    if total_duration > 1.0:
        logger.debug(f"🐢 [MainLoop] 本次渲染总耗时: {total_duration:.2f}s")


if __name__ == "__main__":
    main()
