"""
全局错误处理工具类 - 提供便捷的全局错误处理方法
"""
import logging
import traceback
from typing import Optional, Callable

import streamlit as st
from config.error_config import ErrorConfig
from ui.components.error_renderer import render_error_page

logger = logging.getLogger("ScriptMaster.ErrorHandler")


class GlobalErrorHandler:
    """
    全局错误处理器

    提供统一的错误拦截、分类和处理机制
    """

    @staticmethod
    def handle_exception(
            exception: Exception,
            context: str = "Unknown",
            show_page: bool = True,
            reset_callback: Optional[Callable] = None
    ):
        """
        统一处理异常

        Args:
            exception: 捕获的异常
            context: 错误发生的上下文描述
            show_page: 是否显示完整错误页面（False 则只显示简略提示）
            reset_callback: 重置回调函数
        """
        # 记录日志
        logger.error(f"❌ [{context}] 发生异常: {str(exception)}", exc_info=True)

        # 分类错误
        error_type = ErrorConfig.classify_error(exception)
        error_title, error_detail = ErrorConfig.get_friendly_message(exception)

        # 构建详细错误信息
        full_details = f"**错误类型:** {type(exception).__name__}\n\n"
        full_details += f"**详细描述:** {error_detail}\n\n"
        full_details += f"**技术信息:**\n\n{traceback.format_exc()[:800]}\n"

        if show_page:
            # 显示完整错误页面
            render_error_page(
                error_title=error_title,
                error_message=full_details,
                error_type=error_type,
                show_reset_button=True,
                reset_callback=reset_callback
            )
        else:
            # 显示简略提示
            from ui.components.error_renderer import show_inline_error
            show_inline_error(
                error_message=str(exception),
                error_type=error_type,
                show_details=True
            )

    @staticmethod
    def safe_execute(func: Callable, *args, error_context: str = "执行操作", **kwargs):
        """
        安全执行函数，自动捕获并处理异常

        Args:
            func: 要执行的函数
            *args: 函数参数
            error_context: 错误上下文描述
            **kwargs: 关键字参数

        Returns:
            函数执行结果，出错返回 None
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            GlobalErrorHandler.handle_exception(
                exception=e,
                context=error_context,
                show_page=False
            )
            return None

    @staticmethod
    def create_reset_handler(cleanup_keys: Optional[list] = None):
        """
        创建标准化的重置处理器

        Args:
            cleanup_keys: 需要清理的 session_state 键列表

        Returns:
            重置回调函数
        """

        def handler():
            from utils.state_manager import StateManager

            logger.warning("⚠️ [Action] 用户触发了错误重置")

            # 默认清理的键
            default_keys = [
                'novel_gen_generation_started',
                'novel_gen_done',
                'novel_gen_progress',
                'novel_gen_progress_msg',
                'script_gen_started',
                'script_gen_done',
                'uploaded_file',
                'parsed_content',
                'generation_error',
                'script_is_generating',
                'novel_is_generating'
            ]

            # 合并自定义清理键
            all_keys = list(set(default_keys + (cleanup_keys or [])))

            for key in all_keys:
                if key in st.session_state:
                    del st.session_state[key]

            StateManager.reset_for_new_mode()
            logger.info("♻️ [Action] 状态清理完成，正在重启应用...")
            st.rerun()

        return handler


# 创建全局实例，方便快速调用
error_handler = GlobalErrorHandler()
