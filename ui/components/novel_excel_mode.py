"""
小说Excel分镜生成组件
"""
import io
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
    if 'novel_outline' not in st.session_state:
        st.session_state.novel_outline = None
    try:
        uploaded_file = render_file_uploader()
        if uploaded_file is None:
            return

        df = file_handler.read_file(uploaded_file)
        if df is not None and not df.empty:
            # 未生成结果且未在生成中时显示预览和选择器
            if not st.session_state.novel_results and not st.session_state.novel_is_generating:
                render_data_preview(df)
                selected_indices = render_chapter_selector(df)
                selected_df = df.iloc[selected_indices] if selected_indices else df
            else:
                selected_df = df

            st.divider()

            if st.session_state.novel_is_generating:
                #  生成中：只显示警告，隐藏所有输入框和按钮
                st.warning("️ 生成过程中无法中断，如需停止请刷新浏览器页面")
            else:
                #  未生成：显示配置标题、输入框和按钮
                st.markdown("**⚙️ 生成配置**")

                #  显示两列配置
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
                    batch_count = (total_episodes + 2) // 3
                    st.markdown(
                        f"""
                                               <div style="background-color: #e8f4fd; padding: 10px; border-radius: 5px; text-align: center;">
                                                   <p style="margin: 0; font-size: 14px;">
                                                       分 <b>{batch_count} 次</b> 生成<br>
                                                       <span style="color: #666; font-size: 12px;">每次同时处理 3 集 | 共{total_episodes}集</span>
                                                   </p>
                                               </div>
                                               """,
                        unsafe_allow_html=True
                    )

                api_ready = st.session_state.get("api_validated", False)
                if not st.session_state.novel_results and not st.session_state.novel_outline:
                    if not api_ready:
                        st.warning("️ 请在侧边栏验证 API 配置")
                        st.button("🚀 开始生成", disabled=True)
                    else:
                        if st.button(f"🚀 开始生成 {total_episodes} 集内容", type="primary",
                                     width='stretch', disabled=st.session_state.novel_is_generating):
                            st.session_state.novel_is_generating = True
                            st.rerun()
                else:
                    if st.button("🗑️ 清除当前结果并重新开始",
                                 disabled=st.session_state.novel_is_generating,
                                 width='stretch'):
                        st.session_state.novel_results = {}
                        st.session_state.novel_outline = None
                        st.rerun()

            if 'selected_df' not in locals():
                selected_df = None
            if 'total_episodes' not in locals():
                total_episodes = 20

            #  检查状态并执行生成大纲逻辑
            if st.session_state.novel_is_generating and not st.session_state.novel_outline:
                if selected_df is not None:
                    _execute_generation_flow(llm_service, selected_df, total_episodes)

            # 🌟 新增：从大纲生成分镜逻辑
            elif st.session_state.novel_is_generating and st.session_state.novel_outline and not st.session_state.novel_results:
                if selected_df is not None:
                    _execute_scripts_generation(llm_service, selected_df, total_episodes)

            # 🌟 修复2: 检查状态并执行补全逻辑
            if st.session_state.novel_is_generating and st.session_state.novel_results:
                error_keys = []
                sorted_results = _sort_and_clean_results(st.session_state.novel_results)
                for k, v in sorted_results.items():
                    if isinstance(v, str) and v.startswith("❌"):
                        error_keys.append(k)
                    elif hasattr(v, 'empty') and v.empty:
                        error_keys.append(k)
                    elif hasattr(v, '__len__') and len(v) < 20:
                        error_keys.append(k)

                if error_keys and selected_df is not None:
                    _execute_retry_flow(llm_service, selected_df, error_keys, sorted_results)

            # 新增：大纲展示区域（只在大纲生成完成后、分镜生成前显示）
            if (selected_df is not None and
                st.session_state.novel_outline and
                not st.session_state.novel_results and
                not st.session_state.novel_is_generating):
                render_novel_outline_section(llm_service, selected_df, total_episodes)


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

                if st.button(retry_label, width='stretch', disabled=retry_disabled,
                             key=f"btn_retry_novel_{len(error_keys)}"):
                    st.session_state.novel_is_generating = True
                    st.rerun()

    except Exception as e:
        # 🛡️ 使用全局错误处理器
        error_handler.handle_exception(
            exception=e,
            context="NovelExcelMode",
            show_page=True
        )


def render_novel_outline_section(llm_service, df, total_episodes: int = 20):
    """渲染小说大纲展示区域（可编辑 + Word 导出 + 确认生成分镜）"""
    if not st.session_state.novel_outline:
        return

    st.divider()
    st.markdown("**📖 分集大纲预览**")

    base_name = st.session_state.get('uploaded_file_name', '小说')

    # 🌟 生成过程中，大纲区域默认折叠
    with st.expander("📋 点击编辑大纲", expanded=not st.session_state.novel_is_generating):
        # 🌟 可编辑的大纲文本框
        edited_outline = st.text_area(
            "大纲内容（可直接修改）：",
            value=st.session_state.novel_outline,
            height=400,
            label_visibility="collapsed",
            disabled=st.session_state.novel_is_generating
        )

        # 🌟 保存修改按钮（生成过程中不显示）
        if not st.session_state.novel_is_generating:
            if edited_outline != st.session_state.novel_outline:
                if st.button("💾 保存修改", width='stretch'):
                    st.session_state.novel_outline = edited_outline
                    st.success("✅ 大纲已保存")
                    st.rerun()

        # 🌟 Word 导出（始终显示，生成过程中禁用）
        try:
            from docx import Document
            from docx.shared import Pt
            from docx.enum.text import WD_ALIGN_PARAGRAPH

            doc = Document()

            # 标题样式
            title = doc.add_heading(f'{base_name}_分集大纲', 0)
            title.alignment = WD_ALIGN_PARAGRAPH.CENTER

            # 处理大纲内容，清理 markdown 符号
            outline_text = st.session_state.novel_outline
            # 移除 markdown 符号
            outline_text = outline_text.replace('###', '').replace('**', '').replace('*', '')
            # 移除多余的换行
            lines = [line.strip() for line in outline_text.split('\n') if line.strip()]
            clean_text = '\n'.join(lines)

            doc.add_paragraph(clean_text)

            output = io.BytesIO()
            doc.save(output)
            output.seek(0)

            st.download_button(
                label="📄 导出为 Word 文档",
                data=output.getvalue(),
                file_name=f"{base_name}_分集大纲.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                width='stretch',
                disabled=st.session_state.novel_is_generating  # 🌟 生成过程中禁用
            )
        except Exception as e:
            st.error(f"❌ Word 导出失败: {str(e)[:100]}")

        # 🌟 确认并生成分镜按钮（生成过程中隐藏）
        if not st.session_state.novel_is_generating:
            if st.button("🎬 确认大纲，开始生成分镜", type="primary", width='stretch'):
                st.session_state.novel_is_generating = True
                st.rerun()  # ✅ 立即刷新页面
    st.divider()

def _execute_generation_flow(llm_service, df, total_episodes: int = 20):
    """只生成大纲，生成分镜由用户确认后触发"""
    logger.info(f"🚀 开始生成 {total_episodes} 集大纲")

    processor = NovelModeProcessor(llm_service, total_episodes=total_episodes)
    # 🌟 修复: 动态计算预计时间范围（根据集数）
    if total_episodes <= 20:
        estimated_time = "1-2分钟"
    elif total_episodes <= 50:
        estimated_time = "2-3分钟"
    else:
        estimated_time = "3-5分钟"

    progress_bar = st.progress(0, text=f"🚀 准备生成 {total_episodes} 集大纲...")

    try:
        logger.info("📖 生成大纲中...")
        progress_bar.progress(5, text=f"📖 生成{total_episodes}集大纲（预计{estimated_time}）")

        with st.spinner():
            outline_text = processor.generate_outline(df, on_progress=lambda msg, val: progress_bar.progress(
                5 + int(val * 0.15),
                text=msg
            ))

        st.session_state.novel_outline = outline_text
        progress_bar.progress(1.0, text=f"✅ 大纲生成完成")
        logger.info(f"📖 大纲完成 ({len(outline_text)} 字)")
        st.session_state.novel_is_generating = False
        time.sleep(0.5)
    except Exception as e:
        logger.error(f"❌ 生成失败: {str(e)}", exc_info=True)
        show_inline_error(
            error_message=str(e),
            error_type="unknown",
            show_details=True
        )
    finally:
        logger.info("🔄 刷新页面")
        st.session_state.novel_is_generating = False
        time.sleep(0.5)
        st.rerun()


def _execute_scripts_generation(llm_service, df, total_episodes: int = 20):
    """基于现有大纲生成分镜（独立显示在外部）"""
    logger.info(f"🎬 开始生成 {total_episodes} 集分镜")

    processor = NovelModeProcessor(llm_service, total_episodes=total_episodes)
    estimated_minutes = f"{max(2, total_episodes // 10)}-{max(3, (total_episodes + 5) // 8)}"

    # 🌟 在外部显示进度条，不在大纲区域内
    st.divider()
    st.markdown("### 🎬 正在生成分镜脚本")

    progress_bar = st.progress(0, text=f"🚀 准备生成 {total_episodes} 集分镜...")

    try:
        logger.info("🎬 生成分镜中...")
        progress_bar.progress(5, text=f"🎬 生成{total_episodes}集分镜（预计{estimated_minutes}分钟）")

        results = processor.process(df, on_progress=lambda msg, val: progress_bar.progress(
            5 + int(val * 0.95),
            text=msg
        ))

        st.session_state.novel_results = results
        StateManager.set_results(results)
        progress_bar.progress(1.0, text="✅ 全部生成完成")
        logger.info(f"✅ 分镜完成，共 {len(results)} 集")
        st.session_state.novel_is_generating = False
        time.sleep(0.5)
    except Exception as e:
        logger.error(f"❌ 生成失败: {str(e)}", exc_info=True)
        show_inline_error(
            error_message=str(e),
            error_type="unknown",
            show_details=True
        )
    finally:
        logger.info("🔄 刷新页面")
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
