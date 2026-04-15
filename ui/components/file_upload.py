"""
文件上传组件模块
"""
import pandas as pd
import streamlit as st
import logging
from utils.file_handler import FileHandler

logger = logging.getLogger("ScriptMaster.FileUpload")
def validate_file_content(df: pd.DataFrame) -> tuple:
    try:
        if df.empty:
            return False, "文件内容为空"

        if len(df.columns) < 2:
            return False, f"文件列数不足（当前{len(df.columns)}列，至少需要2列）"

        try:
            if len(df) == 0:
                return False, "文件没有数据行"

            col1_name = df.columns[0]
            col2_name = df.columns[1]

            col1_data = df.iloc[:, 0]
            first_col_has_data = col1_data.notna().any()
            if not first_col_has_data:
                return False, f"第1列【{col1_name}】（章节标题）没有数据"

            col2_data = df.iloc[:, 1]
            second_col_has_data = col2_data.notna().any()
            if not second_col_has_data:
                return False, f"第2列【{col2_name}】（章节内容）没有数据"

            non_empty_content = col2_data.apply(
                lambda x: len(str(x).strip()) > 0 if pd.notna(x) else False
            )
            if not non_empty_content.any():
                return False, "所有章节内容都为空"

            valid_chapters = non_empty_content.sum()
            if valid_chapters == 0:
                return False, "没有找到有效的章节内容"

            return True, ""

        except Exception as e:
            return False, f"数据格式错误：{str(e)}"

    except Exception as e:
        return False, f"文件验证异常：{str(e)}"


def handle_file_upload_and_validation(file_handler: FileHandler):
    """
    处理文件上传和验证（由 novel_excel_mode 调用）

    Returns:
        DataFrame 或 None
    """
    uploaded_file = render_file_uploader()
    if uploaded_file is None:
        return None

    try:
        df = file_handler.read_file(uploaded_file)
        is_valid, error_msg = validate_file_content(df)
        if not is_valid:
            logger.warning(f"文件验证失败: {error_msg}")
            st.error(f"❌ 文件内容不符合要求：{error_msg}")
            st.warning(
                "**请参考使用说明：**\n\n"
                "• 文件至少需要2列数据\n"
                "• 第1列：章节标题（不能为空）\n"
                "• 第2列：章节内容（不能为空）\n"
                "• 确保文件格式正确且未损坏"
            )
            return None
        st.success(f"✅ 成功读取文件，共 {len(df)} 个章节")
        return df
    except Exception as e:
        logger.error(f"读取文件失败: {e}", exc_info=True)
        st.error(f"❌ 读取文件失败: {e}\n\n"
                 f"**可能原因：**\n"
                 f"• 文件格式损坏或不正确\n"
                 f"• 文件编码问题（CSV请使用UTF-8编码）\n"
                 f"• 文件内容为空")
        return None


def _hide_streamlit_file_uploader_text():
    """使用 CSS 隐藏 Streamlit 文件上传器的英文文本"""
    st.markdown("""
    <style>
    /* 隐藏文件上传器的默认英文提示 */
    [data-testid="stFileUploader"] button[kind="secondary"] span {
        visibility: hidden;
        position: relative;
    }
    [data-testid="stFileUploader"] button[kind="secondary"] span::after {
        content: "📁 选择文件";
        visibility: visible;
        position: absolute;
        left: 0;
        right: 0;
    }
    
    /* 隐藏拖拽提示文字 */
    [data-testid="stFileUploaderDropzoneInstructions"] {
        display: none !important;
    }
    
    /* 美化文件上传区域 */
    [data-testid="stFileUploader"] {
        border: 2px dashed #1976d2 !important;
        border-radius: 8px !important;
        padding: 20px !important;
        background-color: #f8f9fa !important;
    }
    
    [data-testid="stFileUploader"]:hover {
        border-color: #0d47a1 !important;
        background-color: #e3f2fd !important;
    }
    </style>
    """, unsafe_allow_html=True)


def render_file_uploader():
    """
    渲染文件上传组件

    Returns:
        上传的文件对象或None
    """
    # 注入 CSS 样式，将英文改为中文
    _hide_streamlit_file_uploader_text()

    # 添加中文使用说明卡片
    st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 20px; 
                    border-radius: 12px; 
                    color: white;
                    margin-bottom: 20px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <h3 style="margin-top: 0; margin-bottom: 15px;">📋 文件上传指南</h3>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                <div>
                    <p style="margin: 5px 0;"><strong>✅ 支持格式：</strong></p>
                    <ul style="margin: 5px 0; padding-left: 20px;">
                        <li>Excel (.xlsx, .xls)</li>
                        <li>CSV (.csv)</li>
                    </ul>
                </div>
                <div>
                    <p style="margin: 5px 0;"><strong>📝 格式要求：</strong></p>
                    <ul style="margin: 5px 0; padding-left: 20px;">
                        <li>第1列：章节标题</li>
                        <li>第2列：章节内容</li>
                        <li>CSV需UTF-8编码</li>
                    </ul>
                </div>
            </div>
            <p style="margin: 10px 0 0 0; font-size: 14px; opacity: 0.9;">
                💡 点击下方按钮选择文件，或将文件拖拽到虚线框内
            </p>
        </div>
        """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "选择小说文件",
        type=['xlsx', 'xls', 'csv'],
        key="novel_file_uploader",
        accept_multiple_files=False,
        label_visibility="collapsed"
    )

    # 文件类型二次校验
    if uploaded_file is not None:
        file_name = uploaded_file.name
        file_extension = file_name.split('.')[-1].lower()
        allowed_extensions = ['xlsx', 'xls', 'csv']

        if file_extension not in allowed_extensions:
            st.error("❌ 此文件格式不符合要求！")
            st.warning(
                "⚠️ **请参考使用说明：**\n\n"
                "• 仅支持上传 **.xlsx**、**.xls**、**.csv** 格式的文件\n"
                "• Excel文件：第1列为章节标题，第2列为章节内容\n"
                "• CSV文件：UTF-8编码，第1列为章节标题，第2列为章节内容\n"
                "• 请检查文件扩展名是否正确"
            )
            return None
        # 保存文件名到 session_state
        st.session_state.uploaded_file_name = file_name.rsplit('.', 1)[0]
        st.success(f"✅ 已选择文件: {file_name}")
        st.info("💡 下一步：设置总集数 → 点击「开始生成」")

    return uploaded_file


# ... existing code ...
def render_data_preview(df: pd.DataFrame):
    with st.expander("📄 数据预览", expanded=True):  # 数据预览改为默认展开
        preview_count = min(len(df), 5)
        st.info(f"共 {len(df)} 个章节，预览前 {preview_count} 个：")

        for idx in range(preview_count):
            row = df.iloc[idx]
            try:
                chapter_title = str(row.iloc[0]) if pd.notna(row.iloc[0]) else f"第{idx + 1}章"
                chapter_content = str(row.iloc[1]) if pd.notna(row.iloc[1]) else ""

                st.markdown(f"**{chapter_title}**")
                preview_text = chapter_content[:300] + "..." if len(chapter_content) > 300 else chapter_content
                st.text(preview_text)
                st.divider()
            except Exception as e:
                st.warning(f"预览第 {idx + 1} 行时出错：{e}")

        if len(df) > preview_count:
            st.caption(f"... 还有 {len(df) - preview_count} 个章节未预览")


# ... existing code ...


def render_chapter_selector(df: pd.DataFrame) -> list:
    """
    渲染章节选择器（支持全选、范围、手动三种模式）
    """
    st.markdown("**选择要处理的章节：**")

    # 构建章节列表
    chapters = []
    for idx in range(len(df)):
        try:
            title = str(df.iloc[idx, 0]) if pd.notna(df.iloc[idx, 0]) else f"第{idx + 1}章"
            content = str(df.iloc[idx, 1]) if pd.notna(df.iloc[idx, 1]) else ""
            chapters.append(f"📖 {title}（{len(content)}字）")
        except Exception:
            chapters.append(f"📖 第 {idx + 1} 章")

    total_chapters = len(chapters)
    all_indices = list(range(total_chapters))

    # 初始化 session_state
    if "chapter_select_mode" not in st.session_state:
        st.session_state.chapter_select_mode = "全选"
    if "selected_chapter_indices" not in st.session_state:
        st.session_state.selected_chapter_indices = all_indices.copy()
    if "range_start" not in st.session_state:
        st.session_state.range_start = 1
    if "range_end" not in st.session_state:
        st.session_state.range_end = total_chapters

    # 选择模式切换
    sel_col1, sel_col2 = st.columns([1, 4])
    with sel_col1:
        mode = st.radio(
            "选择模式",
            ["全选", "范围", "手动"],
            index=["全选", "范围", "手动"].index(st.session_state.chapter_select_mode),
            key="chapter_select_mode",
            label_visibility="collapsed"
        )

    with sel_col2:
        if mode == "全选":
            selected_indices = all_indices
            st.session_state.selected_chapter_indices = selected_indices
            st.success(f"✅ 已选全部 {total_chapters} 个章节")

        elif mode == "范围":
            r1, r2 = st.columns(2)
            with r1:
                start = st.number_input(
                    "起始章节",
                    1,
                    total_chapters,
                    min(st.session_state.range_start, total_chapters),
                    key="range_start_chapter"
                )
            with r2:
                end = st.number_input(
                    "结束章节",
                    1,
                    total_chapters,
                    min(st.session_state.range_end, total_chapters),
                    key="range_end_chapter"
                )

            # 确保 start <= end
            if start > end:
                start, end = end, start

            st.session_state.range_start = start
            st.session_state.range_end = end
            selected_indices = list(range(start - 1, end))
            st.session_state.selected_chapter_indices = selected_indices
            st.success(f"✅ 已选 {len(selected_indices)} 个章节（第 {start} 章 ~ 第 {end} 章）")


        elif mode == "手动":
            # 首次进入手动模式时初始化
            if not st.session_state.get("manual_chapters_initialized"):
                if not st.session_state.selected_chapter_indices:
                    st.session_state.selected_chapter_indices = all_indices.copy()
                st.session_state.manual_chapters_initialized = True

            # 分组显示：每6章为一组，用expanders折叠
            batch_size = 6
            total_groups = (total_chapters + batch_size - 1) // batch_size

            st.markdown("**点击按钮切换选中状态（6章/组）：**")

            for group_idx in range(total_groups):
                start_idx = group_idx * batch_size
                end_idx = min(start_idx + batch_size, total_chapters)
                group_indices = list(range(start_idx, end_idx))

                # 第一组默认展开，其余折叠
                default_expanded = (group_idx == 0)
                with st.expander(f"第 {group_idx + 1} 组（第 {start_idx + 1}-{end_idx} 章）", expanded=default_expanded):
                    cols = st.columns(min(batch_size, len(group_indices)))
                    for i, idx in enumerate(group_indices):
                        is_on = idx in st.session_state.selected_chapter_indices
                        with cols[i]:
                            label = "[✓]" if is_on else "[ ]"
                            chapter_num = idx + 1
                            if st.button(f"{label} {chapter_num}", key=f"chapter_toggle_{idx}", help=chapters[idx]):
                                if idx in st.session_state.selected_chapter_indices:
                                    st.session_state.selected_chapter_indices.remove(idx)
                                else:
                                    st.session_state.selected_chapter_indices.append(idx)
                                _rc = st.session_state.get("_chapter_rerun_count", 0)
                                st.session_state["_chapter_rerun_count"] = _rc + 1
                                if _rc < 10:
                                    st.rerun()

            selected_indices = st.session_state.selected_chapter_indices
            if selected_indices:
                st.markdown(f"**✅ 已选 {len(selected_indices)} 个章节**")
            else:
                st.markdown("**⚠️ 未选择任何章节**")

    # 全选 / 全不选按钮（仅在手动模式下显示）
    if mode == "手动":
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button("☑️ 全选", width='stretch', key="btn_select_all_chapters"):
                st.session_state.selected_chapter_indices = all_indices.copy()
                st.session_state["_chapter_rerun_count"] = 0
                st.rerun()
        with btn_col2:
            if st.button("🔲 全不选", width='stretch', key="btn_deselect_all_chapters"):
                st.session_state.selected_chapter_indices = []
                st.session_state["_chapter_rerun_count"] = 0
                st.rerun()

    # 返回选中的索引列表（排序后）
    return sorted(st.session_state.selected_chapter_indices)
