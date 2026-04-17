"""
提示词调优工坊 (Prompt Studio) - 动态变量终极版
"""
import difflib
import logging
import re

import streamlit as st
from core.prompt_manager import PromptManager, PromptKeys
from core.prompts import PromptTemplates
from streamlit_ace import st_ace

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
            # 🚀 部署按钮
            if st.button("🚀 部署到生产环境", type="primary", use_container_width=True):
                # 🛡️ 变量沙盒强校验：双向终极防线
                pattern = r'\{([a-zA-Z_]\w*)\}'
                official_vars = set(re.findall(pattern, official_prompt))
                draft_vars = set(re.findall(pattern, st.session_state[session_key]))

                missing_vars = official_vars - draft_vars
                illegal_vars = draft_vars - official_vars

                if missing_vars or illegal_vars:
                    st.session_state["deploy_error"] = {
                        "missing": missing_vars,
                        "illegal": illegal_vars
                    }
                    st.rerun()
                else:
                    PromptManager.update(current_key, st.session_state[session_key])
                    logger.info(f"✅ [PromptStudio] 用户部署提示词资产: {selected_asset}")
                    st.session_state["show_deploy_success"] = True
                    st.rerun()

            if st.button("🔄 还原官方配置", use_container_width=True):
                PromptManager.reset(current_key)
                st.session_state[session_key] = official_prompt
                st.session_state[f"{session_key}_version"] = st.session_state.get(f"{session_key}_version", 0) + 1
                logger.info(f"🔄 [PromptStudio] 用户还原官方配置: {selected_asset}")
                st.session_state["show_restore_success"] = True
                st.rerun()

            # 👇 处理部署和还原后的状态提示
            if "deploy_error" in st.session_state:
                errors = st.session_state.pop("deploy_error")
                missing = errors.get("missing", set())
                illegal = errors.get("illegal", set())

                err_msg = "🚨 **部署被强行拦截！**\n\n"
                if missing:
                    err_msg += f"❌ **丢失系统必备变量**：`{', '.join(['{' + v + '}' for v in missing])}`\n"
                if illegal:
                    err_msg += f"⚠️ **存在非法/拼错变量**：`{', '.join(['{' + v + '}' for v in illegal])}`\n"

                err_msg += "\n**请修正这些 `{变量}` 后重试，否则正式生成时会导致系统彻底崩溃！**"
                st.error(err_msg, icon="🛑")

            if st.session_state.pop("show_deploy_success", False):
                st.success("✅ 部署成功！\n新的提示词规则已安全对全局业务生效。", icon="🎉")

            if st.session_state.pop("show_restore_success", False):
                st.info("🔄 已还原！\n当前模块已恢复为系统初始默认配置。", icon="✨")

            # 👇 纯净版的操作历史与审计日志
            st.divider()
            with st.expander("📜 操作历史与审计日志", expanded=False):
                history_records = PromptManager.get_history()

                if not history_records:
                    st.caption("暂无操作记录")
                else:
                    for record in history_records:
                        st.markdown(f"""
                                    <div style="font-size: 12.5px; margin-bottom: 12px; border-left: 2px solid #E8C87A; padding-left: 10px; margin-left: 4px;">
                                        <span style="color: #A37F58; font-size: 11px;">{record['time']}</span><br>
                                        <span style="color: #4A4543; font-weight: 600;">{record['action']}</span><br>
                                        <span style="color: #7A756F;">{record['details']}</span>
                                    </div>
                                    """, unsafe_allow_html=True)

                    if st.button("🗑️ 清空记录", use_container_width=True):
                        PromptManager.clear_history()
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

            # 🌟 官方默认配置参考面板
            with st.expander("👀 遗忘原版了？点击查看官方默认配置 (仅供参考、复制)"):
                st.code(official_prompt, language="markdown")

            editor_version = st.session_state.get(f"{session_key}_version", 0)

            # 使用 Ace 编辑器
            new_content = st_ace(
                value=st.session_state[session_key] or "",
                language='markdown',
                theme='chrome',
                key=f"ace_editor_{current_key.name}_{editor_version}",
                height=550,
                font_size=15,
                wrap=True,
                show_gutter=True,
                show_print_margin=False,
                auto_update=False,
            )

            if new_content and new_content != st.session_state[session_key]:
                st.session_state[session_key] = new_content
                st.toast("💾 草稿已捕获！", icon="✨")

            st.markdown("<br>", unsafe_allow_html=True)
            st.info(
                "💡 **操作提示**：在编辑器内按下 `Ctrl + Enter` (Mac 为 `Cmd + Enter`)，或者鼠标点击编辑器外部，即可自动保存草稿并刷新页面！")

        with tabs[1]:
            # 差异比对图例说明
            st.markdown("""
                <div style='margin-bottom: 15px; padding: 12px 18px; background: #FFFDF8; border: 1px solid #F0D9A0; border-radius: 8px; font-size: 14px; color: #4A4543;'>
                    <b style='color: #E3700D;'>💡 差异比对图例：</b><br>
                    <div style='margin-top: 8px;'>
                        <span style='background-color: #F0FDF4; color: #166534; padding: 2px 8px; border-radius: 4px; font-family: Consolas, monospace;'>+ 绿色行</span> 代表您 <b>新增或修改</b> 的自定义内容。<br>
                    </div>
                    <div style='margin-top: 6px;'>
                        <span style='background-color: #FEF2F2; color: #991B1B; text-decoration: line-through; padding: 2px 8px; border-radius: 4px; font-family: Consolas, monospace;'>- 红色行</span> 代表官方原版中被您 <b>删除或替换</b> 的旧内容。
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown(get_elegant_diff_html(official_prompt, st.session_state[session_key]), unsafe_allow_html=True)

        with tabs[2]:
            st.info("💡 实验室：⚔️ **A/B 双屏擂台！** 左侧运行官方原版，右侧运行你的当前草稿，直观对比优化效果。")
            api_ready = st.session_state.get("api_validated", False)

            test_inputs = {}
            official_vars = set(re.findall(r'\{([^}]+)\}', official_prompt))
            if official_vars:
                st.markdown("**请为以下变量填入模拟数据进行测试：**")
                for var in official_vars:
                    if var in ["content", "outline", "user_choice", "original_idea"]:
                        test_inputs[var] = st.text_area(f"{{{var}}} (长文本)", height=150, key=f"mock_{var}")
                    else:
                        test_inputs[var] = st.text_input(f"{{{var}}} (短参数)", value="1", key=f"mock_{var}")
            else:
                st.success("当前提示词无变量，可直接测试。")

            if not api_ready:
                st.warning("⚠️ 请先在侧边栏配置并验证 API Key，否则无法进行实时测试。")
                st.button("⚔️ 开启 A/B 擂台测试", type="primary", disabled=True, use_container_width=True)
            else:
                if st.button("⚔️ 开启 A/B 擂台测试", type="primary", use_container_width=True):
                    official_test_prompt = official_prompt
                    draft_test_prompt = st.session_state[session_key]

                    for var, val in test_inputs.items():
                        official_test_prompt = official_test_prompt.replace(f"{{{var}}}", str(val))
                        draft_test_prompt = draft_test_prompt.replace(f"{{{var}}}", str(val))

                    if current_key == PromptKeys.ACT_GEN_TASK:
                        sys_key = PromptKeys.ACT_GEN_SYSTEM
                    elif current_key == PromptKeys.OUTLINE_TASK:
                        sys_key = PromptKeys.OUTLINE_SYSTEM
                    else:
                        sys_key = PromptKeys.SCRIPT_SYSTEM
                    current_system_prompt = PromptManager.get(sys_key)

                    st.markdown("---")

                    ab_col1, ab_col2 = st.columns(2)
                    with ab_col1:
                        st.markdown("### 🏛️ 官方原版输出")
                        off_status = st.status("正在运行官方配置...", expanded=True)
                        off_output = st.empty()

                    with ab_col2:
                        st.markdown("### 🛠️ 当前调优版输出")
                        draft_status = st.status("等待官方版运行完毕...", expanded=True)
                        draft_output = st.empty()

                    try:
                        off_stream = ""
                        for chunk in llm_service.generate_stream(current_system_prompt, official_test_prompt):
                            off_stream += chunk
                            off_output.markdown(off_stream)
                        off_status.update(label="✅ 官方原版运行完毕", state="complete", expanded=False)

                        draft_status.update(label="🚀 正在运行调优配置...", state="running")
                        draft_stream = ""
                        for chunk in llm_service.generate_stream(current_system_prompt, draft_test_prompt):
                            draft_stream += chunk
                            draft_output.markdown(draft_stream)
                        draft_status.update(label="✅ 调优版运行完毕", state="complete", expanded=False)

                        st.balloons()

                    except Exception as e:
                        st.error(f"❌ A/B 测试执行失败：{str(e)[:200]}")
                        logger.error(f"❌ [PromptStudio] A/B 测试异常: {str(e)}", exc_info=True)
