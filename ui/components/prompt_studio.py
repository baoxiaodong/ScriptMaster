"""
提示词调优工坊 (Prompt Studio) - 动态变量终极版
"""
import difflib
import logging
import re

import streamlit as st
from core.prompt_manager import PromptManager, PromptKeys
from core.prompts import PromptTemplates
from st_tui_editor import st_tui_editor

logger = logging.getLogger("ScriptMaster.PromptStudio")

PROMPT_ASSET_MAP = {
    "🎬 导演全局人设": PromptKeys.SCRIPT_SYSTEM,
    "📚 小说大纲策略": PromptKeys.OUTLINE_TASK,
    "📚 小说分镜约束": PromptKeys.BATCH_SCRIPT_PROMPT,
    "🎭 剧本三幕式生成": PromptKeys.ACT_GEN_TASK,
    "🎭 剧本分镜约束": PromptKeys.SCRIPT_TASK_TEMPLATE
}


def get_elegant_diff_html(old_text: str, new_text: str) -> str:
    """莫兰迪色系 Diff 渲染 - 增加防呆清洗"""
    old_text = old_text.replace('\r\n', '\n').strip()
    new_text = new_text.replace('\r\n', '\n').strip()

    diff = list(difflib.ndiff(old_text.splitlines(keepends=True), new_text.splitlines(keepends=True)))
    html = "<div style='font-family: Consolas, monospace; font-size: 14.5px; line-height: 1.8; padding: 24px; background: #FFFDF8; border-radius: 16px; border: 1px solid #F0D9A0;'>"
    for line in diff:
        clean_line = line[2:].replace('<', '&lt;').replace('>', '&gt;')
        if line.startswith('+ '):
            html += f"<div style='background-color: #F0FDF4; color: #166534;'>+ {clean_line}</div>"
        elif line.startswith('- '):
            html += f"<div style='background-color: #FEF2F2; color: #991B1B; text-decoration: line-through;'>- {clean_line}</div>"
        elif not line.startswith('? '):
            html += f"<div style='color: #4A4543;'>&nbsp;&nbsp;{clean_line}</div>"
    html += "</div>"
    return html


def render_prompt_studio(llm_service):
    st.markdown("""
        <style>
            .studio-header { background: linear-gradient(135deg, #E3700D 0%, #C68A1E 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800; font-size: 28px; }
            .stTabs [data-baseweb="tab-list"] { background: #FFF5E6; border-radius: 30px; padding: 5px; border: 1px solid #F0D9A0; }
            .stTabs [data-baseweb="tab"] { border-radius: 25px !important; color: #A37F58; padding: 8px 25px; }
            .stTabs [aria-selected="true"] { background: #FFFFFF !important; color: #E3700D !important; font-weight: 600 !important; box-shadow: 0 2px 8px rgba(227,112,13,0.15) !important; }
            .luxury-tag { background: #FFFFFF; color: #E3700D; border: 1px solid #F0D9A0; padding: 5px 15px; border-radius: 20px; font-size: 13px; font-weight: 600; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='studio-header'>🎬 导演控台 (Prompt Studio)</div>", unsafe_allow_html=True)
    st.markdown("<p style='color: #8C827A; margin-bottom: 25px;'>在此精雕细琢每一集分镜的灵魂逻辑。</p>",
                unsafe_allow_html=True)

    main_col, side_col = st.columns([3.5, 1], gap="large")

    with side_col:
        with st.container(border=True):
            selected_asset = st.radio("📂 选择资产模块", list(PROMPT_ASSET_MAP.keys()))
            current_key = PROMPT_ASSET_MAP[selected_asset]

        official_prompt = getattr(PromptTemplates, current_key.name, "")
        user_prompt = PromptManager.get(current_key)

        session_key = f"active_editor_{current_key.name}"
        if session_key not in st.session_state:
            st.session_state[session_key] = user_prompt

        with st.container(border=True):
            if st.button("🚀 部署到生产环境", type="primary", use_container_width=True):
                PromptManager.update(current_key, st.session_state[session_key])
                logger.info(f"✅ [PromptStudio] 用户部署提示词资产: {selected_asset}")
                st.toast(f"✅ [{selected_asset}] 已更新并持久化！", icon="🚀")

            if st.button("🔄 还原官方配置", use_container_width=True):
                PromptManager.reset(current_key)
                st.session_state[session_key] = official_prompt
                logger.info(f"🔄 [PromptStudio] 用户还原官方配置: {selected_asset}")
                st.rerun()

    current_text = st.session_state[session_key]
    detected_vars = list(set(re.findall(r'\{([^}]+)\}', current_text)))

    with main_col:
        tabs = st.tabs(["✏️ 沉浸式创作 (Edit)", "🔍 差异比对 (Diff)", "🧪 实验室 (Playground)"])

        with tabs[0]:
            var_hint = ", ".join([f"{{{v}}}" for v in detected_vars]) if detected_vars else "无变量"
            st.markdown(
                f"<div style='margin-bottom:10px;'><span class='luxury-tag'>🪄 自动嗅探的变量槽：{var_hint}</span></div>",
                unsafe_allow_html=True)
            st.warning(
                "⚠️ **系统底层红线：** 您可以尽情修改文字规则和防呆约束，但**严禁凭空新增或修改带有 `{}` 的变量名**，否则会导致正式生成时系统彻底崩溃！")

            res = st_tui_editor(
                content=st.session_state[session_key],
                height="550px",
                initial_edit_type="wysiwyg",
                preview_style="tab",
                key=f"editor_vfinal_{current_key.name}"
            )

            # 手动同步检测
            if res and "markdown" in res:
                if res["markdown"] != st.session_state[session_key]:
                    st.session_state[session_key] = res["markdown"]
                    st.caption("✨ 草稿已同步（点击下方按钮确认刷新以更新 Diff）")

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔄 确认同步改动 (前往 Diff 或 实验室前请点击)", use_container_width=True):
                st.rerun()

        with tabs[1]:
            st.markdown(get_elegant_diff_html(official_prompt, st.session_state[session_key]), unsafe_allow_html=True)

        with tabs[2]:
            st.info("💡 实验室：已根据上方提取的变量，自动为你生成对应的测试输入框。")
            api_ready = st.session_state.get("api_validated", False)

            test_inputs = {}
            if detected_vars:
                st.markdown("**请为以下变量填入模拟数据进行测试：**")
                for var in detected_vars:
                    if var in ["content", "outline", "user_choice", "original_idea"]:
                        test_inputs[var] = st.text_area(f"{{{var}}} (长文本)", height=150, key=f"mock_{var}")
                    else:
                        test_inputs[var] = st.text_input(f"{{{var}}} (短参数)", value="1", key=f"mock_{var}")
            else:
                st.success("当前提示词无变量，可直接测试。")

            if not api_ready:
                st.warning("⚠️ 请先在侧边栏配置并验证 API Key，否则无法进行实时测试。")
                st.button("⚡ 实时跑一次测试", type="primary", disabled=True, use_container_width=True)
            else:
                if st.button("⚡ 实时跑一次测试", type="primary", use_container_width=True):
                    final_prompt = st.session_state[session_key]
                    for var, val in test_inputs.items():
                        final_prompt = final_prompt.replace(f"{{{var}}}", str(val))

                    logger.info(f"🧪 [PromptStudio] 用户启动实验室测试: {selected_asset}")

                    with st.status("AI 导演审稿中...", expanded=True) as status:
                        output = st.empty()
                        content_stream = ""

                        if current_key == PromptKeys.ACT_GEN_TASK:
                            sys_key = PromptKeys.ACT_GEN_SYSTEM
                        elif current_key == PromptKeys.OUTLINE_TASK:
                            sys_key = PromptKeys.OUTLINE_SYSTEM
                        else:
                            sys_key = PromptKeys.SCRIPT_SYSTEM

                        current_system_prompt = PromptManager.get(sys_key)

                        try:
                            for chunk in llm_service.generate_stream(current_system_prompt, final_prompt):
                                content_stream += chunk
                                output.markdown(content_stream)

                            status.update(label="✅ 测试完成", state="complete", expanded=False)
                            logger.info(f"✅ [PromptStudio] 实验室测试成功: {selected_asset} ({len(content_stream)}字)")

                        except Exception as e:
                            error_msg = str(e)[:200]
                            st.error(f"❌ API 测试失败：{error_msg}")
                            status.update(label=f"❌ 测试失败: {error_msg[:50]}...", state="error", expanded=True)
                            logger.error(f"❌ [PromptStudio] 实验室测试异常: {selected_asset} - {str(e)}", exc_info=True)
