"""
全局错误页面渲染组件 - 负责展示友好的错误提示界面
"""
import streamlit as st
from typing import Optional, Callable

from config.error_config import ErrorConfig, ErrorTemplate


def render_error_page(
    error_title: Optional[str] = None,
    error_message: str = "",
    error_type: str = "unknown",
    show_reset_button: bool = True,
    show_home_button: bool = True,
    reset_callback: Optional[Callable] = None,
    home_callback: Optional[Callable] = None,
    custom_template: Optional[ErrorTemplate] = None
):
    """
    渲染友好的错误提示页面

    Args:
        error_title: 自定义错误标题（为空则使用模板默认标题）
        error_message: 错误详细信息
        error_type: 错误类型分类
        show_reset_button: 是否显示重置按钮
        show_home_button: 是否显示返回首页按钮
        reset_callback: 重置回调函数
        home_callback: 返回首页回调函数
        custom_template: 自定义错误模板（优先级高于 error_type）
    """

    # 注入 CSS 样式
    st.markdown(ErrorConfig.CSS_STYLES, unsafe_allow_html=True)

    # 获取错误模板
    template = custom_template or ErrorConfig.get_template(error_type)

    # 使用自定义标题或模板默认标题
    display_title = error_title or template.title

    # 渲染错误卡片
    st.markdown(f"""
    <div class="error-container">
        <div class="error-icon">{template.icon}</div>
        <h2 class="error-title">{display_title}</h2>
        <p class="error-suggestion">💡 {template.suggestion}</p>
        {'<div class="error-details">' + error_message + '</div>' if error_message else ''}
    </div>
    """, unsafe_allow_html=True)

    # 渲染操作按钮
    _render_action_buttons(
        show_reset=show_reset_button,
        show_home=show_home_button,
        reset_callback=reset_callback,
        home_callback=home_callback,
        error_type=error_type
    )


def _render_action_buttons(
    show_reset: bool,
    show_home: bool,
    reset_callback: Optional[Callable],
    home_callback: Optional[Callable],
    error_type: str
):
    """渲染操作按钮区域"""

    if not show_reset and not show_home:
        return

    # 计算列数
    cols_count = sum([show_reset, show_home])
    if cols_count == 0:
        return

    columns = st.columns(cols_count)
    col_index = 0

    # 重置按钮
    if show_reset:
        with columns[col_index]:
            if st.button("🔄 重置状态并重试", key=f"reset_{error_type}", use_container_width=True):
                if reset_callback:
                    reset_callback()
                else:
                    _default_reset_handler()
        col_index += 1

    # 首页按钮
    if show_home:
        with columns[col_index]:
            if st.button("🏠 返回首页", key=f"home_{error_type}", use_container_width=True):
                if home_callback:
                    home_callback()
                else:
                    _clear_and_rerun()


def _default_reset_handler():
    """默认的重置处理器"""
    from utils.state_manager import StateManager

    # 清理所有生成相关的状态
    keys_to_clear = [
        'novel_gen_generation_started',
        'novel_gen_done',
        'novel_gen_progress',
        'novel_gen_progress_msg',
        'script_gen_started',
        'script_gen_done',
        'uploaded_file',
        'parsed_content',
        'generation_error',
        'novel_is_generating',
        'script_is_generating'
    ]

    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

    StateManager.reset_for_new_mode()
    st.rerun()


def _clear_and_rerun():
    """清除状态并返回首页"""
    # 保留基础配置，只清理业务数据
    preserved_keys = ['_provider', '_api_key', 'app_initialized']
    keys_to_delete = [k for k in st.session_state.keys() if k not in preserved_keys]

    for key in keys_to_delete:
        del st.session_state[key]

    st.rerun()


def show_inline_error(
    error_message: str,
    error_type: str = "unknown",
    show_details: bool = False
):
    """
    在当前位置显示简化的错误提示（不跳转页面）
    """
    template = ErrorConfig.get_template(error_type)

    st.warning(f"{template.icon} **{template.title}**\n\n{template.suggestion}")

    if show_details and error_message:
        with st.expander("🔍 查看技术详情"):
            st.code(error_message, language="text")


def show_success_message(message: str, icon: str = "✅"):
    """
    显示成功消息（与错误页面风格一致）
    """
    st.success(f"{icon} {message}")


def show_warning_message(message: str, icon: str = "⚠️"):
    """
    显示警告消息
    """
    st.warning(f"{icon} {message}")