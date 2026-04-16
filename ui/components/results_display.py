"""
结果显示组件模块
"""
import io
import os
import zipfile
from typing import Dict

import pandas as pd
import streamlit as st
from utils.file_handler import FileHandler


def render_results(results: Dict[str, pd.DataFrame]):
    """
    渲染生成结果
    
    Args:
        results: 结果字典 {标题: DataFrame或错误信息}
    """
    if not results:
        st.warning("⚠️ 没有生成结果")
        return

    st.markdown("### 📜 生成分镜脚本")

    # 清空结果按钮
    if st.button("🗑 清空结果", key="btn_clear_results"):
        from utils.state_manager import StateManager
        StateManager.set_results({})
        st.rerun()

    st.divider()

    # 分离成功和失败的结果
    success_results = {
        k: v for k, v in results.items()
        if isinstance(v, pd.DataFrame)
    }
    error_results = {
        k: v for k, v in results.items()
        if isinstance(v, str) and v.startswith("❌")
    }

    # 显示错误
    if error_results:
        st.error(f"❌ 以下 {len(error_results)} 集生成失败，请点击底部「补全缺失集数」按钮重试：")
        for title, error in error_results.items():
            st.warning(f"- **{title}**: {error[:100]}{'...' if len(error) > 100 else ''}")

    # 显示成功结果
    if success_results:
        _render_success_results(success_results)


def _render_success_results(results: Dict[str, pd.DataFrame]):
    """渲染成功的结果 - 改进版：快速导航 + 镜头统计"""

    # 计算镜头统计
    episode_stats = []
    for title, script_df in results.items():
        if isinstance(script_df, pd.DataFrame):
            shot_count = len(script_df)
            episode_stats.append((title, shot_count))

    total_shots = sum(s for _, s in episode_stats)
    total_episodes = len(episode_stats)

    # 显示统计信息
    st.markdown(f"📊 **总计：{total_episodes} 集，{total_shots} 个镜头**")

    # 新增：质量检查提示
    low_shot_episodes = [(title, count) for title, count in episode_stats if count < 20]
    if low_shot_episodes:
        st.warning(f"⚠️ 以下 {len(low_shot_episodes)} 集镜头数不足 20 个，建议点击底部「补全缺失集数」重试：")
        for title, count in low_shot_episodes:
            st.markdown(f"- **{title}**: {count} 个镜头")

    # 快速导航下拉框
    if len(results) > 1:
        episode_options = [title for title, _ in episode_stats]
        selected_episode = st.selectbox(
            "🔍 快速导航到指定集数：",
            options=episode_options,
            index=0,
            label_visibility="collapsed"
        )
    else:
        selected_episode = list(results.keys())[0] if results else None

    # 显示选中的集数
    if selected_episode and selected_episode in results:
        st.divider()
        _render_single_result(selected_episode, results[selected_episode])

        # 显示其他集数的摘要（可折叠）
        if len(results) > 1:
            with st.expander(f"📋 其他 {len(results) - 1} 集摘要（点击查看）"):
                for title, shot_count in episode_stats:
                    if title != selected_episode:
                        st.markdown(f"- **{title}**: {shot_count} 个镜头")

    # 批量下载
    if len(results) > 1:
        _render_batch_download(results)


def _render_single_result(title: str, df: pd.DataFrame):
    """渲染单个结果"""
    st.markdown(
        f"<div class='episode-header'>🎬 {title}</div>",
        unsafe_allow_html=True
    )

    # 显示表格
    st.dataframe(
        df,
        hide_index=True,
        column_config={
            "镜号": st.column_config.TextColumn("镜号", width="small"),
            "场景": st.column_config.TextColumn("场景", width="medium"),
            "画面内容 (Visual)": st.column_config.TextColumn("画面内容", width="large"),
            "台词 (Dialogue) & 音效 (SFX)": st.column_config.TextColumn("台词 & 音效", width="large"),
        }
    )

    # 下载按钮
    csv_data = FileHandler.export_to_csv(df)
    st.download_button(
        label=f"📥 下载 {title} CSV",
        data=csv_data,
        file_name=f"{title.replace(' ', '_')}_分镜.csv",
        mime='text/csv',
        width='stretch'
    )
def _render_batch_download(results: Dict[str, pd.DataFrame]):
        """渲染批量下载按钮"""
        st.divider()
        st.markdown("**📥 批量下载**")
        col1, col2 = st.columns(2)

        # 🌟 提取基础文件名（去除扩展名）
        uploaded_file_name = st.session_state.get('uploaded_file_name', '')
        if not uploaded_file_name:
            base_name = "分镜脚本"
        else:
            base_name = os.path.splitext(uploaded_file_name)[0]

        with col1:
            # Excel 批量下载
            excel_data = FileHandler.export_to_excel(results)
            st.download_button(
                label="📊 下载 Excel（多工作表）",
                data=excel_data,
                file_name=f"{base_name}_剧本分镜.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                width='stretch'
            )

        with col2:
            # ZIP 批量下载（每个集数一个 CSV 文件）
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for title, df in results.items():
                    if isinstance(df, pd.DataFrame) and not df.empty:
                        csv_data = df.to_csv(index=False).encode('utf-8-sig')
                        # 文件名清理
                        safe_title = title.replace('/', '_').replace('\\', '_').replace(':', '_')
                        zip_file.writestr(f"{safe_title}_分镜.csv", csv_data)

            zip_buffer.seek(0)
            st.download_button(
                label="📦 下载 ZIP（分集 CSV）",
                data=zip_buffer.getvalue(),
                file_name=f"{base_name}_分镜集数包.zip",
                mime="application/zip",
                width='stretch',
                key="btn_download_zip"
            )
