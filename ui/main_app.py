"""
主应用模块 - 优化启动性能，修复生成过程卡顿与状态同步问题，增强日志监控，优化渲染顺序
"""
import time

import streamlit as st
# 1. 导入必要的配置（注：st.set_page_config 已移至外部主入口 main.py）
from config.settings import PAGE_CONFIG, CUSTOM_CSS, setup_logger, NOVEL_MODE_NAME, SCRIPT_MODE_NAME
from ui.components.novel_excel_mode import render_novel_excel_mode
from ui.components.script_generator import render_script_generation_mode
from ui.components.sidebar import render_sidebar
from utils.file_handler import FileHandler
from utils.state_manager import StateManager

# 获取应用层级的 logger
logger = setup_logger("XiaoShuoFenjing.App")


def init_app():
    """初始化应用基础配置"""

    # CSS 只在首次加载时注入一次
    if '_css_injected' not in st.session_state:
        st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
        st.session_state._css_injected = True

    # 初始化业务状态（仅在会话开始时执行一次）
    if 'app_initialized' not in st.session_state:
        logger.info("🎬 [System] AI小说分镜生成器 - 正在执行首次启动初始化...")
        StateManager.init()
        # 初始化状态记录
        st.session_state['_last_mode'] = None
        st.session_state.app_initialized = True
        logger.info("✅ [System] 基础状态初始化完成")


def render_header():
    """渲染品牌 Banner"""
    st.markdown(
        '<div class="hermes-banner">'
        '<p class="banner-title">'
        'AI小说分镜生成器'
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

    # ================= 调整渲染顺序 =================

    # 1. 优先渲染主区域顶部
    render_header()

    st.markdown('<p class="step-title" style="margin-bottom:10px;">选择工作模式</p>', unsafe_allow_html=True)

    current_mode = st.radio(
        "切换模式",
        [NOVEL_MODE_NAME,SCRIPT_MODE_NAME],
        label_visibility="collapsed",
        horizontal=True,
        key="app_mode_selector"
    )

    # --- 模式切换逻辑：清理上一个模式的残余状态，防止数据干扰 ---
    if st.session_state.get('_last_mode') != current_mode:
        last = st.session_state.get('_last_mode')
        if last is not None:
            logger.info(f"🔄 [Router] 模式切换动作触发: {last} -> {current_mode}")
            StateManager.reset_for_new_mode()
        st.session_state['_last_mode'] = current_mode

    st.divider()

    # 2. 接着渲染侧边栏
    provider, api_key, model_name = render_sidebar(llm_service)

    # 同步到 session_state 供全局快速访问
    if st.session_state.get('_provider') != provider:
        logger.info(f"⚙️ [Config] 模型服务商变更为: {provider}")
    st.session_state['_provider'] = provider
    st.session_state['_api_key'] = api_key

    # 3. 最后渲染主业务区域的详情内容
    try:
        render_start = time.time()
        if current_mode == NOVEL_MODE_NAME:
            # 记录进入详情，如果这里卡死，日志会停在这里
            logger.info("📂 [Render] 正在载入: 小说Excel模式组件")
            render_novel_excel_mode(llm_service, file_handler)
        else:
            logger.info("✍️ [Render] 正在载入: 剧本全流程模式组件")
            render_script_generation_mode(llm_service)

        render_duration = time.time() - render_start
        if render_duration > 0.5:  # 渲染超过0.5秒记录警告
            logger.warning(f"⏱️ [Performance] 组件渲染耗时较长: {render_duration:.2f}s")

    except Exception as e:
        logger.error(f"❌ [Fatal] 渲染层异常崩溃: {str(e)}", exc_info=True)
        st.error(f"⚠️ 业务组件运行异常。如果是生成过程中卡死，请点击下方重置。")
        st.info(f"错误详情: {str(e)}")

        if st.button("🔄 强制重置系统状态 (修复卡死)", key="force_reset_btn"):
            logger.warning("⚠️ [Action] 用户触发了强制重置按钮")
            StateManager.reset_for_new_mode()
            # 清理特定的生成标记
            keys_to_del = [
                'novel_gen_generation_started',
                'novel_gen_done',
                'novel_gen_progress',
                'novel_gen_progress_msg'
            ]
            for k in keys_to_del:
                if k in st.session_state:
                    del st.session_state[k]
            logger.info("♻️ [Action] 状态清理完成，正在重启应用...")
            st.rerun()

    # 记录整个 main 循环的结束
    total_duration = time.time() - start_time
    if total_duration > 1.0:
        logger.debug(f"🐢 [MainLoop] 本次渲染总耗时: {total_duration:.2f}s")


if __name__ == "__main__":
    main()
