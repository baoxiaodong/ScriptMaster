"""
剧本生成组件模块 - 已集成进度条、流式输出与默认《低画质人生》创意
"""
import io
import logging
import re

import pandas as pd
import streamlit as st
from core.prompts import PromptTemplates

logger = logging.getLogger("ScriptMaster.ScriptGenerator")


def export_outline_to_word(outline_text: str) -> bytes:
    """导出大纲为 Word 文档"""
    from docx import Document
    doc = Document()
    doc.add_heading('30集分集大纲', 0)
    doc.add_paragraph(outline_text)
    output = io.BytesIO()
    doc.save(output)
    output.seek(0)
    return output.getvalue()


def init_script_state():
    """初始化剧本生成相关的session state"""
    if 'generated_acts' not in st.session_state:
        st.session_state.generated_acts = None
    if 'selected_act' not in st.session_state:
        st.session_state.selected_act = None
    if 'outline' not in st.session_state:
        st.session_state.outline = None
    if 'scripts' not in st.session_state:
        st.session_state.scripts = {}


def extract_csv_from_text(text):
    """提取包含表头的 CSV 数据块"""
    if not text: return ""
    # 移除 Markdown 代码块标记
    text = re.sub(r'```csv\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    pattern = r"镜号,场景,画面内容 \(Visual\),台词 \(Dialogue\) & 音效 \(SFX\).*"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(0).strip()
    return text.strip()


def render_step_1_acts(llm_service):
    """第一步：核心创意与三幕式构架 (流式输出)"""
    try:
        st.markdown('<div class="step-header">第一步：核心创意与三幕式构架</div>', unsafe_allow_html=True)

        default_idea = """Resolution: Low《低画质人生》
2099年，视觉感知成为一种昂贵的订阅服务。富人享受着8K HDR的极致世界，而像凯这样的穷人只能活在"经济模式"里--一个模糊、像素化的144p噩梦。凯为了看清病危母亲的脸，在黑市购买了违禁芯片，结果发现"高清"世界里，统治者其实是食人怪物，而"低画质"只是为了掩盖真相的滤镜。"""

        original_idea = st.text_area("请输入原始创意：", value=default_idea, height=150)

        api_ready = st.session_state.get("api_validated", False)
        if not api_ready:
            st.warning("⚠️ 请在侧边栏验证 API 配置")
            st.button("🚀 开始创作三幕式", disabled=True, key="gen_act_btn_dis")
        else:
            if st.button("🚀 开始创作三幕式", type="primary", key="gen_act_btn",
                         disabled=st.session_state.get('script_is_generating', False)):
                st.session_state.script_is_generating = True
                full_response = ""
                prompt = PromptTemplates.ACT_GEN_TASK.format(original_idea=original_idea)
                placeholder = st.empty()

                with st.spinner("🤖 AI 编剧正在构思剧情，请稍候..."):
                    for chunk in llm_service.generate_stream("你是一个专业编剧，擅长爆款短剧设定。", prompt):
                        full_response += chunk
                        placeholder.markdown(full_response + "▌")

                placeholder.markdown(full_response)

                if full_response.startswith("❌"):
                    st.error("❌ 生成失败：请检查 API 配置和网络连接")
                    st.session_state.script_is_generating = False
                else:
                    st.session_state.generated_acts = full_response
                    st.success("✅ 三幕式构架生成完成！")
                    st.rerun()

        if st.session_state.generated_acts and not st.session_state.generated_acts.startswith("❌"):
            st.session_state.selected_act = st.text_area(
                "确认/修改三幕式构架：",
                value=st.session_state.generated_acts,
                height=200
            )
    except Exception as e:
        st.error(f"❌ 第一步加载异常: {str(e)[:60]}")
        logger.error(f"❌ [ScriptStep1] 渲染异常: {str(e)}", exc_info=True)
        st.session_state.script_is_generating = False


def render_step_2_outline(llm_service):
    """第二步：30集大纲扩展 (流式输出)"""
    try:
        if not st.session_state.get('selected_act') and not st.session_state.get('generated_acts'):
            return

        st.markdown('<div class="step-header">第二步：扩展 30 集连贯大纲</div>', unsafe_allow_html=True)

        api_ready = st.session_state.get("api_validated", False)
        if not api_ready:
            st.warning("⚠️ 请在侧边栏验证 API 配置")
            st.button("📈 生成 30 集大纲", disabled=True, key="gen_outline_btn_dis")
        else:
            if st.button("📈 生成 30 集大纲", type="primary", key="gen_outline_btn"):
                st.session_state.script_is_generating = True
                source_act = st.session_state.get('selected_act') or st.session_state.get('generated_acts')
                full_response = ""
                prompt = PromptTemplates.OUTLINE_TASK.format(user_choice=source_act)
                placeholder = st.empty()

                with st.spinner("📖 AI 正在扩展 30 集连贯大纲，请稍候..."):
                    for chunk in llm_service.generate_stream(PromptTemplates.OUTLINE_SYSTEM, prompt):
                        full_response += chunk
                        placeholder.markdown(full_response + "▌")

                placeholder.markdown(full_response)

                if full_response.startswith("❌"):
                    st.error("❌ 大纲生成失败：请检查 API 配置和网络连接")
                    st.session_state.script_is_generating = False
                else:
                    st.session_state.outline = full_response
                    st.success("✅ 30 集大纲生成完成！")
                    st.rerun()

        if st.session_state.outline and not st.session_state.outline.startswith("❌"):
            st.text_area("30集预览：", value=st.session_state.outline, height=250)
            word_bytes = export_outline_to_word(st.session_state.outline)
            st.download_button(
                label="📄 导出为 Word",
                data=word_bytes,
                file_name="30集分集大纲.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )
    except Exception as e:
        st.error(f"❌ 第二步加载异常: {str(e)[:60]}")
        logger.error(f"❌ [ScriptStep2] 渲染异常: {str(e)}", exc_info=True)
        st.session_state.script_is_generating = False




def render_step_3_scripts(llm_service):
    """第三步：分集分镜批量生成 (进度条 + 实时流式预览)"""
    try:
        if not st.session_state.outline:
            return

        st.markdown('<div class="step-header">第三步：批量生成详细分镜</div>', unsafe_allow_html=True)

        ep_range = st.slider("选择生成的集数范围：", 1, 30, (1, 3))

        api_ready = st.session_state.get("api_validated", False)
        if not api_ready:
            st.warning("⚠️ 请在侧边栏验证 API 配置")
            st.button("🔥 开始批量执行", disabled=True, key="execute_batch_dis")
        else:
            if st.button("🔥 开始批量执行", type="primary", key="execute_batch",
                         disabled=st.session_state.get('script_is_generating', False)):
                st.session_state.script_is_generating = True
                start_ep, end_ep = ep_range
                total = end_ep - start_ep + 1

                progress_bar = st.progress(0)
                status_text = st.empty()
                preview_header = st.empty()
                preview_content = st.empty()

                error_detected = False
                for i, ep_idx in enumerate(range(start_ep, end_ep + 1)):
                    progress_bar.progress(i / total)
                    status_text.info(f"正在处理：第 {ep_idx} 集 (进度: {i}/{total})")
                    preview_header.markdown(f"✍️ **正在书写第 {ep_idx} 集内容...**")

                    full_script = ""
                    prompt = PromptTemplates.BATCH_SCRIPT_PROMPT.format(
                        start_ep=ep_idx,
                        end_ep=ep_idx,
                        content=st.session_state.outline,
                        total_episodes=30
                    )

                    for chunk in llm_service.generate_stream(PromptTemplates.SCRIPT_SYSTEM, prompt):
                        full_script += chunk
                        preview_content.code(full_script, language="csv")

                        if chunk.startswith("❌"):
                            error_detected = True
                            status_text.error(f"❌ 第 {ep_idx} 集生成失败：请检查 API 配置")
                            preview_header.empty()
                            preview_content.empty()
                            break

                    if error_detected:
                        progress_bar.progress(0)
                        break

                    st.session_state.scripts[f"第{ep_idx}集"] = extract_csv_from_text(full_script)

                if not error_detected:
                    progress_bar.progress(1.0)
                    status_text.success("✅ 批量生成任务已完成！")
                    preview_header.empty()
                    preview_content.empty()

                st.session_state.script_is_generating = False
                st.rerun()
    except Exception as e:
        st.error(f"❌ 第三步加载异常: {str(e)[:60]}")
        logger.error(f"❌ [ScriptStep3] 渲染异常: {str(e)}", exc_info=True)
    finally:
        if st.session_state.get('script_is_generating', False):
            st.session_state.script_is_generating = False
            st.rerun()


def display_final_tables():
    """展示生成的脚本"""
    if not st.session_state.scripts:
        return

    st.divider()
    st.markdown("### 🎬 剧本库预览")

    sorted_keys = sorted(st.session_state.scripts.keys(), key=lambda x: int(re.findall(r'\d+', x)[0]))
    tabs = st.tabs(sorted_keys)

    for i, key in enumerate(sorted_keys):
        with tabs[i]:
            content = st.session_state.scripts[key]
            try:
                df = pd.read_csv(io.StringIO(content))
                st.dataframe(df, use_container_width=True, hide_index=True)
                csv_bytes = df.to_csv(index=False).encode('utf-8-sig')
                st.download_button(f"📥 下载{key}", csv_bytes, f"{key}.csv", "text/csv", key=f"btn_{key}")
            except:
                st.text_area("内容解析异常，请检查：", value=content, height=200)


def render_script_generation_mode(llm_service):
    """主入口"""
    st.markdown("""
        <style>
            .stTextArea textarea { color: #000000 !important; }
            .step-header { 
                padding: 10px; background: #f0f2f6; 
                border-left: 5px solid #FF4B4B; font-weight: bold; margin: 15px 0; 
            }
        </style>
    """, unsafe_allow_html=True)

    init_script_state()
    render_step_1_acts(llm_service)
    render_step_2_outline(llm_service)
    render_step_3_scripts(llm_service)
    display_final_tables()
