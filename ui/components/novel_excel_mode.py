"""
小说Excel分镜生成组件 - 纯净版
彻底移除所有 DEBUG 输出、结果统计和冗余 UI 元素
"""
import logging
import re
import time

import streamlit as st
from core.processor import NovelModeProcessor
from ui.components.error_renderer import show_inline_error
from ui.components.file_upload import render_file_uploader, render_data_preview, render_chapter_selector
from ui.components.results_display import render_results
# 🛡️ 新增：导入全局错误处理系统（从 utils 目录）
from utils.error_handler import error_handler
from utils.file_handler import FileHandler
from utils.state_manager import StateManager

logger = logging.getLogger("ScriptMaster.NovelMode")


def render_novel_excel_mode(llm_service, file_handler: FileHandler):
    """主渲染逻辑"""
    st.markdown("### 📚 小说分镜生成")

    # 初始化状态
    if 'novel_is_generating' not in st.session_state:
        st.session_state.novel_is_generating = False
    if 'novel_results' not in st.session_state:
        st.session_state.novel_results = {}

    try:
        uploaded_file = render_file_uploader()
        if uploaded_file is None:
            return

        df = file_handler.read_file(uploaded_file)
        if df is not None and not df.empty:
            # 未生成结果时显示预览和选择器
            if not st.session_state.novel_results:
                render_data_preview(df)
                selected_indices = render_chapter_selector(df)
                selected_df = df.iloc[selected_indices] if selected_indices else df
            else:
                selected_df = df

            st.divider()
            # 🌟 新增：集数配置输入框
            st.markdown("**⚙️ 生成配置**")
            col1, col2 = st.columns([3, 1])
            with col1:
                total_episodes = st.number_input(
                    "总集数",
                    min_value=10,
                    max_value=100,
                    value=st.session_state.get('total_episodes', 20),
                    step=5,
                    help="设置要生成的分镜总集数（系统将按每 3 集一批并行处理）"
                )
                st.session_state.total_episodes = total_episodes
            with col2:
                # 显示批次信息
                batch_count = (total_episodes + 2) // 3
                st.markdown(
                    f"""
                           <div style="background-color: #e8f4fd; padding: 10px; border-radius: 5px; text-align: center;">
                               <p style="margin: 0; font-size: 14px;">
                                   📦 分 <b>{batch_count} 次</b> 生成<br>
                                   <span style="color: #666; font-size: 12px;">每次同时处理 3 集 | 共{total_episodes}集</span>
                               </p>
                           </div>
                           """,
                    unsafe_allow_html=True
                )
            # 按钮逻辑
            api_ready = st.session_state.get("api_validated", False)
            if not st.session_state.novel_results:
                if not api_ready:
                    st.warning("⚠️ 请在侧边栏验证 API 配置")
                    st.button("🚀 开始生成", disabled=True, use_container_width=True)
                else:
                    if st.button(f"🚀 开始生成 {total_episodes} 集分镜", type="primary", use_container_width=True,
                                 disabled=st.session_state.novel_is_generating):
                        st.session_state.novel_is_generating = True
                        _execute_generation_flow(llm_service, selected_df, total_episodes)
            else:
                if st.button("🗑️ 清除当前结果并重新开始", use_container_width=True):
                    st.session_state.novel_results = {}
                    st.rerun()

        # 渲染结果展示
        results = st.session_state.novel_results
        if results:
            sorted_results = _sort_and_clean_results(results)
            render_results(sorted_results)

            # 🌟 始终显示补全按钮，没有错误时灰化
            error_keys = []
            for k, v in sorted_results.items():
                if isinstance(v, str) and v.startswith("❌"):
                    error_keys.append(k)
                elif hasattr(v, 'empty') and v.empty:
                    error_keys.append(k)
                elif hasattr(v, '__len__') and len(v) < 20:
                    error_keys.append(k)

            retry_disabled = not error_keys or st.session_state.novel_is_generating
            retry_label = "🔄 补全缺失集数" if error_keys else "✅ 全部生成成功，无需补全"

            if st.button(retry_label, use_container_width=True, disabled=retry_disabled,
                         key=f"btn_retry_novel_{len(error_keys)}"):
                st.session_state.novel_is_generating = True
                _execute_retry_flow(llm_service, selected_df, error_keys, sorted_results)

    except Exception as e:
        # 🛡️ 使用全局错误处理器
        error_handler.handle_exception(
            exception=e,
            context="NovelExcelMode",
            show_page=True
        )


def _execute_generation_flow(llm_service, df, total_episodes: int = 20):
    """执行生成 - 支持动态集数配置"""
    processor = NovelModeProcessor(llm_service, total_episodes=total_episodes)
    estimated_minutes = f"{max(2, total_episodes // 10)}-{max(3, total_episodes // 8)}"
    progress_bar = st.progress(0,
                               text=f"🚀 正在调用 AI 大模型，准备生成 {total_episodes} 集分镜...（预计需要 {estimated_minutes} 分钟）")

    def update_progress_ui(msg: str, val: int):
        progress_bar.progress(min(val / 100, 1.0), text=f"⏳ 进度: {val}% | {msg}")

    try:
        results = processor.process(df, on_progress=update_progress_ui)
        st.session_state.novel_results = results
        StateManager.set_results(results)
        progress_bar.progress(1.0, text="✅ 生成完成")

    except Exception as e:
        # 🛡️ 使用内联错误提示
        show_inline_error(
            error_message=str(e),
            error_type="unknown",
            show_details=True
        )
        logger.error(f"❌ [Generation] 生成失败: {str(e)}", exc_info=True)
    finally:
        st.session_state.novel_is_generating = False
        time.sleep(0.5)
        st.rerun()


def _execute_retry_flow(llm_service, df, error_keys, existing_results):
    """补全逻辑"""
    total_episodes = st.session_state.get('total_episodes', 20)
    processor = NovelModeProcessor(llm_service, total_episodes=total_episodes)
    progress_bar = st.progress(0, text="🔄 正在重新调用 AI，补全失败集数...")

    try:
        # processor.process 已经内部合并了 existing_results，直接用它返回的结果
        results = processor.process(df, on_progress=lambda msg, val: progress_bar.progress(min(val / 100, 1.0),
                                                                                           text=f"⏳ 补全: {val}% | {msg}"),
                                    existing_results=existing_results)

        # 直接使用 processor 返回的合并结果，不再手动遍历更新
        st.session_state.novel_results = results

        # 统计实际补全成功的数量
        update_count = 0
        for k in error_keys:
            new_result = results.get(k)
            if new_result is not None:
                is_valid = not (isinstance(new_result, str) and new_result.startswith("❌"))
                is_not_empty = not (hasattr(new_result, 'empty') and new_result.empty)
                if is_valid and is_not_empty:
                    update_count += 1

        progress_bar.progress(1.0, text=f"✅ 补全完成，成功更新 {update_count}/{len(error_keys)} 集")
    except Exception as e:
        # 🛡️ 使用内联错误提示
        show_inline_error(
            error_message=str(e),
            error_type="unknown",
            show_details=True
        )
        logger.error(f"❌ [Retry] 补全失败: {str(e)}", exc_info=True)
    finally:
        st.session_state.novel_is_generating = False
        time.sleep(0.5)
        st.rerun()


def _sort_and_clean_results(results: dict) -> dict:
    """按集数数字排序"""
    try:
        def extract_num(key):
            match = re.search(r'\d+', str(key))
            return int(match.group()) if match else 0

        sorted_keys = sorted(results.keys(), key=extract_num)
        return {k: results[k] for k in sorted_keys}
    except:
        return results
