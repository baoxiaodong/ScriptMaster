"""
提示词调优工坊 (Prompt Studio) - Option B: 单屏纯净富文本版 (保姆级体验)
"""
import difflib
import streamlit as st
from st_tui_editor import st_tui_editor

# ================= 模拟的后台默认数据 (Mock Data) =================
MOCK_DEFAULTS = {
    "🎬 导演全局人设": "你是一个短剧导演，负责设计发布在 TikTok 上的剧情短片分镜。\n\n【核心约束】\n1. 每集包含 20-30 个镜头。\n2. 台词必须是纯正地道的英文，画面描述为中文。\n3. 画面节奏要极快，视觉冲击力强。",
    "📚 小说大纲策略": "请将下述【小说正文】浓缩成具有极强悬念感的分集大纲。\n\n要求：\n- 每一集结尾必须留下钩子（Cliffhanger）。\n- 重点突出矛盾冲突。",
    "📚 小说分镜约束": "请严格按照 CSV 格式输出分镜表。\n\n包含列：\n- 镜号\n- 场景\n- 画面内容\n- 台词与音效",
    "🎭 剧本三幕式生成": "根据以下短片创意，扩写为标准的好莱坞【三幕式】剧作结构。\n建置 -> 冲突 -> 解决。",
    "🎭 剧本分镜约束": "请将该剧本转化为短视频分镜...\n提示：重点刻画人物的微表情特写。"
}


def get_elegant_diff_html(old_text: str, new_text: str) -> str:
    """莫兰迪色系的 Diff 渲染，护眼且优雅"""
    diff = list(difflib.ndiff(old_text.splitlines(keepends=True), new_text.splitlines(keepends=True)))

    html = "<div style='font-family: \"SF Pro Text\", \"PingFang SC\", Consolas, monospace; font-size: 14.5px; line-height: 1.8; padding: 24px; background: #FFFDF8; border-radius: 16px; border: 1px solid #F0D9A0; box-shadow: inset 0 2px 10px rgba(198,138,30,0.03); max-height: 600px; overflow-y: auto;'>"
    for line in diff:
        clean_line = line[2:].replace('<', '&lt;').replace('>', '&gt;')
        if line.startswith('+ '):
            html += f"<div style='background-color: #F0FDF4; color: #166534; padding: 4px 12px; margin: 4px 0; border-radius: 6px; border-left: 4px solid #4ADE80;'>+ &nbsp;{clean_line}</div>"
        elif line.startswith('- '):
            html += f"<div style='background-color: #FEF2F2; color: #991B1B; text-decoration: line-through; text-decoration-color: rgba(153,27,27,0.4); padding: 4px 12px; margin: 4px 0; border-radius: 6px; border-left: 4px solid #F87171;'>- &nbsp;{clean_line}</div>"
        elif not line.startswith('? '):
            html += f"<div style='color: #4A4543; padding: 4px 12px; margin: 4px 0;'>&nbsp;&nbsp;&nbsp;{clean_line}</div>"
    html += "</div>"
    return html


def render_prompt_studio():
    # 注入 Hermes 高级定制 CSS
    st.markdown("""
        <style>
            .block-container { padding-top: 1.5rem !important; max-width: 1300px !important;}
            .studio-header { background: linear-gradient(135deg, #E3700D 0%, #C68A1E 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800; font-size: 28px; margin-bottom: 5px; letter-spacing: 1px; }
            .stTabs [data-baseweb="tab-list"] { background: #FFF5E6; border-radius: 30px; padding: 6px; gap: 8px; box-shadow: inset 0 2px 4px rgba(198,138,30,0.05); border: 1px solid #F0D9A0; margin-bottom: 20px;}
            .stTabs [data-baseweb="tab"] { border-radius: 24px !important; color: #A37F58; font-weight: 500; padding: 8px 24px; border: none !important; background: transparent !important; transition: all 0.3s ease;}
            .stTabs [data-baseweb="tab"]:hover { color: #E3700D; }
            .stTabs [aria-selected="true"] { background: #FFFFFF !important; color: #E3700D !important; font-weight: 600 !important; box-shadow: 0 2px 8px rgba(227,112,13,0.15) !important; }
            .luxury-tag { background: #FFFFFF; color: #C68A1E; border: 1px solid #F0D9A0; padding: 6px 16px; border-radius: 20px; font-size: 13px; font-weight: 600; margin-right: 10px; display: inline-block; box-shadow: 0 2px 6px rgba(198,138,30,0.08);}
            .luxury-tag-required { color: #E3700D; background: #FFF9F0; border-color: #E3700D; }
        </style>
    """, unsafe_allow_html=True)

    # 1. 极致优雅的页头
    st.markdown("<div class='studio-header'>🎬 导演控台 (Prompt Studio)</div>", unsafe_allow_html=True)
    st.markdown(
        "<p style='color: #8C827A; font-size: 15px; margin-bottom: 25px;'>在这里，用文字雕琢你的视听语言与分镜灵魂。</p>",
        unsafe_allow_html=True)

    # 2. 布局：左边主工作区，右边侧边操作栏
    main_col, side_col = st.columns([3.5, 1], gap="large")

    # ================= 先渲染右侧控制塔 =================
    with side_col:
        st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)

        # 模块切换卡片
        with st.container(border=True):
            st.markdown("**📂 资产库切换**")
            selected_asset = st.radio("选择要调优的模块：", list(MOCK_DEFAULTS.keys()), label_visibility="collapsed")

        # 获取该模块的模拟默认值
        official_prompt = MOCK_DEFAULTS[selected_asset]

        # 初始化当前模块的编辑状态
        text_area_key = f"mock_editor_{selected_asset}"
        if text_area_key not in st.session_state:
            st.session_state[text_area_key] = official_prompt

        st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

        # 保存操作卡片
        with st.container(border=True):
            st.markdown("**💾 部署更新**")
            st.caption("将当前提示词写入系统核心。")

            if st.button("🚀 覆写到全局引擎", type="primary", use_container_width=True):
                st.toast(f"✅ [{selected_asset}] 部署成功！(演示)", icon="🚀")

            if st.button("🔄 还原为官方配置", use_container_width=True):
                st.session_state[text_area_key] = official_prompt
                st.toast("✅ 已恢复出厂设置！", icon="🔄")
                st.rerun()

        st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

        # 历史快照卡片
        with st.container(border=True):
            st.markdown("**⏱️ 历史快照**")
            st.markdown("<span style='color:#E3700D; font-size: 13px;'>• 刚刚 - 演示手动保存</span>",
                        unsafe_allow_html=True)
            st.markdown("<span style='color:#A37F58; font-size: 13px;'>• 初始 - 官方默认版本</span>",
                        unsafe_allow_html=True)

    # ================= 再渲染左侧主工作区 =================
    with main_col:
        st.markdown("<br>", unsafe_allow_html=True)

        view_tabs = st.tabs(["📝 沉浸式创作台 (WYSIWYG)", "🔍 历史变更比对 (Diff Check)"])

        with view_tabs[0]:
            # 温馨且高级的变量提示墙
            st.markdown(f"""
                    <div style='margin-bottom: 12px; display: flex; align-items: center;'>
                        <span style='font-size: 14px; color: #A37F58; margin-right: 12px; font-weight: 500;'>📍 系统插槽：</span>
                        <span class='luxury-tag luxury-tag-required'>🪄 请勿删除大括号 {{}} 内的系统变量</span>
                    </div>
                """, unsafe_allow_html=True)

            # 🌟 核心升级：单屏沉浸式富文本编辑器
            editor_result = st_tui_editor(
                content=st.session_state[text_area_key],
                height="600px",
                initial_edit_type="wysiwyg",  # 👈 强制设定为所见即所得模式
                preview_style="tab",          # 👈 配合 wysiwyg，彻底关闭左右分屏
                theme="light",
                key=f"tui_{text_area_key}"
            )

            # 捕获编辑器内容 (底层依然会帮你保存为干净的 Markdown，喂给大模型毫无压力)
            if editor_result and "markdown" in editor_result:
                st.session_state[text_area_key] = editor_result["markdown"]

        with view_tabs[1]:
            st.markdown("<br>", unsafe_allow_html=True)
            current_text = st.session_state.get(text_area_key, "")

            if current_text.strip() == official_prompt.strip():
                st.info("💡 当前内容与底层官方版本完全一致，暂无变更。")
            else:
                st.markdown(get_elegant_diff_html(official_prompt, current_text), unsafe_allow_html=True)