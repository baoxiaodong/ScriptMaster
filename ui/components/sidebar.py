# -*- coding: utf-8 -*-
"""
侧边栏组件模块
"""
import streamlit as st

from config.settings import MODEL_OPTIONS, API_BASE_URLS
from core.llm_service import LLMService


def render_sidebar(llm_service: LLMService):
    """
    渲染侧边栏
    """

    def reset_validation():
        st.session_state["api_validated"] = False
        # 🌟 清除验证结果
        if 'api_validation_result' in st.session_state:
            del st.session_state['api_validation_result']

    with st.sidebar:
        st.header("[AI] 模型配置")

        provider = st.selectbox(
            "选择模型厂商",
            list(MODEL_OPTIONS.keys()) + ["Mock (演示)"],
            on_change=reset_validation
        )

        api_key = ""
        model_name = ""
        base_url = ""

        if provider == "Mock (演示)":
            st.info("当前为演示模式，使用内置示例数据，不会消耗 API 额度")
            st.divider()
        else:
            # 初始化 session_state
            if "show_api_key" not in st.session_state:
                st.session_state.show_api_key = False

            provider_key = f"api_key_{provider}"
            if provider_key not in st.session_state:
                st.session_state[provider_key] = ""

            #  使用 expander 包裹配置项
            with st.expander("⚙️ API 详细配置", expanded=True):
                col_key, col_eye = st.columns([5, 1])
                with col_key:
                    api_key = st.text_input(
                        "API Key",
                        value=st.session_state[provider_key],
                        type="password" if not st.session_state.show_api_key else "default",
                        help="必填，API Key 安全存储不会上传",
                        placeholder="请输入 API Key",
                        label_visibility="collapsed",
                        key="api_key_input",
                        on_change=reset_validation
                    )
                    if api_key:
                        st.session_state[provider_key] = api_key
                        st.session_state.api_key_value = api_key
                with col_eye:
                    eye_icon = "👁️" if st.session_state.show_api_key else "🔒"
                    if st.button(eye_icon, key="btn_toggle_eye", help="显示/隐藏 API Key"):
                        st.session_state.show_api_key = not st.session_state.show_api_key
                        st.rerun()

                st.markdown(
                    '<style>'
                    'section[data-testid="stSidebar"] .stTextInput input[type="text"],'
                    'section[data-testid="stSidebar"] .stTextInput input[type="password"] {'
                    '    min-width: 320px;'
                    '}'
                    '</style>',
                    unsafe_allow_html=True
                )

                model_name = st.selectbox(
                    "选择模型",
                    MODEL_OPTIONS.get(provider, [""]),
                    on_change=reset_validation
                )

                if api_key:
                    # 🌟 修复1：验证提示持久化显示
                    if 'api_validation_result' in st.session_state:
                        result = st.session_state['api_validation_result']
                        if result.startswith("✅"):
                            st.success(result)
                        else:
                            st.error(result)

                    # 🌟 修复2：验证按钮状态管理
                    is_verifying = st.session_state.get('_verifying_api', False)

                    if st.button("🔍 验证 API Key", key="btn_verify_key", disabled=is_verifying, width='stretch'):
                        # 🌟 设置验证中状态
                        st.session_state['_verifying_api'] = True
                        st.session_state['api_validation_result'] = None  # 清除旧结果

                        with st.spinner(f"正在验证{model_name}，请稍候..."):
                            try:
                                result = llm_service.generate(
                                    "你是一个测试助手。",
                                    "请回复：OK"
                                )
                                if result.startswith("❌"):
                                    st.session_state['api_validation_result'] = "❌ API Key 验证失败：" + result[2:].strip()
                                    st.toast("❌ API Key 验证失败，请检查配置", icon="❌")
                                else:
                                    st.session_state['api_validation_result'] = "✅ API Key 验证通过！模型连接正常"
                                    st.session_state["api_validated"] = True
                                    st.session_state.api_key_value = api_key
                                    st.toast("✅ API Key 验证通过！", icon="✅")
                            except Exception as e:
                                st.session_state['api_validation_result'] = "❌ 连接异常：" + str(e)[:80]
                                st.toast("❌ 连接异常，请检查网络", icon="❌")
                            finally:
                                #  验证完成，清除验证中状态
                                st.session_state['_verifying_api'] = False
                                st.rerun()

            # 🚀 关键：在 expander 外部读取 base_url，确保它总是被定义
            base_url = API_BASE_URLS.get(provider, "")

        # 更新服务配置（🌟 优化：只在参数变化时才调用）
        current_config = (provider, api_key, model_name, base_url)
        if st.session_state.get('_last_llm_config') != current_config:
            llm_service.configure(provider, api_key, model_name, base_url)
            st.session_state._last_llm_config = current_config

        st.divider()
        with st.expander("📖 使用说明", expanded=False):
            st.markdown("""
            **📂 文件格式要求：**
            - 上传 Excel 时，请确保包含 **章节标题** 和 **内容列**
            - 第1列：章节标题
            - 第2列：章节内容
            
            **⚙️ 生成标准：**
            - 每集默认 ≥20 个镜头
            - 画面描述：中文
            - 台词 & 音效：英文
            """)

        return provider, api_key, model_name
