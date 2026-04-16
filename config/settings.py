"""
配置模块 - 集中管理所有配置
"""
import logging
import sys

# Streamlit 页面配置
PAGE_CONFIG = {
    "page_title": "ScriptMaster - AI 分镜工坊",
    "page_icon": "🎬",
    "layout": "wide"
}

# 上传文件的CSS样式
CUSTOM_CSS = """
<style>
/* ============================================================
   爱马仕橙主题 - Hermès Orange Theme
   ============================================================ */

.stApp {
    background: linear-gradient(180deg, #FFF9F0 0%, #FFF5E6 100%) !important;
    color: #4A4543 !important;
}

/* --- 侧边栏 --- */
[data-testid="stSidebar"] {
    min-width: 320px !important;
    max-width: 320px !important;
    width: 320px !important;
    flex: 0 0 320px !important;
    background: linear-gradient(180deg, #FFF5E6 0%, #FFEDD0 100%) !important;
    border-right: 2px solid #E8C87A !important;
}

/* 🌟 修复：强制固定侧边栏容器宽度 */
section[data-testid="stSidebar"] {
    min-width: 320px !important;
    max-width: 320px !important;
    width: 320px !important;
    flex: 0 0 320px !important;
}

/* 🌟 修复：确保侧边栏在展开/折叠状态下都保持固定宽度 */
[data-testid="stSidebar"][aria-expanded="true"] > div:first-child {
    width: 320px !important;
}

[data-testid="stSidebar"][aria-expanded="false"] > div:first-child {
    width: 320px !important;
    margin-left: -320px !important;
}

/* 🌟 修复：确保主内容区布局稳定，不受侧边栏影响 */
.main .block-container {
    max-width: 100% !important;
    width: 100% !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
}

/* 🌟 修复：强制主内容区自适应剩余空间 */
.main {
    flex: 1 !important;
    min-width: 0 !important;
}


/* --- 顶部品牌 Banner --- */
.hermes-banner {
    background: linear-gradient(135deg, #E3700D 0%, #C68A1E 100%);
    color: white;
    padding: 20px 28px;
    border-radius: 12px;
    margin-bottom: 18px;
    box-shadow: 0 4px 16px rgba(227,112,13,0.25);
    position: relative;
    overflow: hidden;
}
.hermes-banner::before {
    content: "";
    position: absolute;
    top: -50%;
    right: -10%;
    width: 200px;
    height: 200px;
    background: rgba(255,255,255,0.06);
    border-radius: 50%;
}
.hermes-banner .banner-title {
    font-size: 26px;
    font-weight: 700;
    letter-spacing: 1px;
    color: #fff;
    text-shadow: 0 1px 3px rgba(0,0,0,0.2);
    margin: 0;
}
.hermes-banner .banner-sub {
    font-size: 14px;
    color: rgba(255,255,255,0.88);
    margin-top: 4px;
}
.hermes-badge {
    display: inline-block;
    background: rgba(255,255,255,0.2);
    border: 1px solid rgba(255,255,255,0.35);
    border-radius: 20px;
    padding: 2px 10px;
    font-size: 11px;
    color: rgba(255,255,255,0.95);
    margin-left: 10px;
    vertical-align: middle;
}

/* --- Streamlit 默认蓝色按钮 → 爱马仕橙 --- */
.stButton > button[kind="primary"],
.element-container .stButton > button {
    background-color: #E3700D !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 15px !important;
    padding: 8px 20px !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 2px 8px rgba(227,112,13,0.3) !important;
}
.stButton > button[kind="primary"]:hover,
.element-container .stButton > button:hover {
    background-color: #C65F00 !important;
    box-shadow: 0 4px 14px rgba(227,112,13,0.45) !important;
    transform: translateY(-1px);
}
.stButton > button[kind="primary"]:active,
.element-container .stButton > button:active {
    background-color: #B05200 !important;
    transform: translateY(0);
    box-shadow: 0 1px 4px rgba(227,112,13,0.3) !important;
}

/* 禁用状态的按钮 */
.stButton > button:disabled {
    background-color: #F5D9A8 !important;
    color: rgba(74,69,67,0.5) !important;
    box-shadow: none !important;
    cursor: not-allowed !important;
}

/* --- 次要按钮 --- */
.stButton > button:not([kind="primary"]) {
    background-color: #FFF5E6 !important;
    color: #C68A1E !important;
    border: 1.5px solid #E8C87A !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
}
.stButton > button:not([kind="primary"]):hover {
    background-color: #FFF0D0 !important;
    border-color: #E3700D !important;
    color: #C65F00 !important;
}

/* --- 进度条 → 橙色 --- */
.stProgress > div > div > div > div {
    background-color: #E3700D !important;
}

/* --- Radio 选择器 → 橙色 --- */
.stRadio > div > label:hover {
    color: #C65F00 !important;
}

/* --- Selectbox 下拉框 --- */
[data-testid="stSelectbox"] .stSelectbox {
    border-color: #E8C87A !important;
}
[data-testid="stSelectbox"] [data-baseweb="select"] {
    border-color: #E8C87A !important;
}
[data-testid="stSelectbox"] [data-baseweb="select"] > div {
    background-color: #FFF9F0 !important;
    border-color: #E8C87A !important;
}

/* --- Text Input 输入框 --- */
[data-testid="stTextInput"] input {
    border-color: #E8C87A !important;
    background-color: #FFFDF8 !important;
    border-radius: 8px !important;
}
[data-testid="stTextInput"] input:focus {
    border-color: #E3700D !important;
    box-shadow: 0 0 0 2px rgba(227,112,13,0.15) !important;
}


/* --- Tabs 标签页 --- */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: #FFF5E6;
    border-radius: 10px;
    padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 7px;
    font-weight: 600;
    color: #4A4543;
    transition: all 0.2s;
}
.stTabs [aria-selected="true"] {
    background-color: #E3700D !important;
    color: #FFFFFF !important;
    box-shadow: 0 2px 8px rgba(227,112,13,0.3);
}
.stTabs [data-baseweb="tab"]:hover:not([aria-selected="true"]) {
    background-color: #F5E8CC !important;
    color: #C65F00 !important;
}

/* --- Cards 卡片 --- */
.hermes-card {
    background: #FFFFFF;
    border: 1px solid #F0D9A0;
    border-left: 4px solid #E3700D;
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 14px;
    box-shadow: 0 2px 10px rgba(227,112,13,0.08);
}

/* --- Step 步骤卡片 --- */
.step-card {
    background: #FFFFFF;
    border: 1.5px solid #F0D9A0;
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 16px;
    box-shadow: 0 2px 12px rgba(198,138,30,0.1);
}
.step-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 14px;
}
.step-num {
    background: linear-gradient(135deg, #E3700D, #C68A1E);
    color: white;
    font-weight: 700;
    font-size: 14px;
    width: 28px;
    height: 28px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}
.step-title {
    font-size: 17px;
    font-weight: 700;
    color: #2C2A29;
}
.step-desc {
    font-size: 13px;
    color: #7A756F;
    margin-top: 2px;
}

/* --- 模式选择卡片 --- */
.mode-radio {
    background: #FFFDF8;
    border: 1.5px solid #E8C87A;
    border-radius: 10px;
    padding: 14px 18px;
}
.mode-radio:hover {
    border-color: #E3700D;
    background: #FFF9F0;
}


/* --- Divider 分隔线 → 橙色 --- */
hr {
    border: none;
    border-top: 1.5px solid #F0D9A0 !important;
}

/* --- Info / Success / Warning / Error 提示框 --- */
.stAlert {
    border-radius: 8px !important;
}
[data-testid="stAlert-success"] {
    background-color: #FFF9F0 !important;
    border-left: 4px solid #C68A1E !important;
}
[data-testid="stAlert-success"] .stAlert { border-left-color: #C68A1E; }
[data-testid="stAlert-error"] {
    background-color: #FFF0F0 !important;
    border-left: 4px solid #E74C3C !important;
}
[data-testid="stAlert-warning"] {
    background-color: #FFFBF0 !important;
    border-left: 4px solid #E8A020 !important;
}

/* --- File Uploader 文件上传 --- */
[data-testid="stFileUploaderDropzone"] {
    background: #FFFDF8;
    border: 2px dashed #E8C87A;
    border-radius: 12px;
}
[data-testid="stFileUploaderDropzone"]:hover {
    border-color: #E3700D;
    background: #FFF9F0;
}
/* 隐藏拖拽区英文提示（Drag and drop / 文件大小限制） */
[data-testid="stFileUploaderDropzoneInstructions"],
[data-testid="stFileUploaderDropzoneInstructions"] span,
[data-testid="stFileUploaderDropzoneInstructions"] label {
    display: none !important;
}
/* 隐藏上传区的 Browse files 按钮（限定在上传区容器内，不影响其他 secondary 按钮） */
[data-testid="stFileUploaderDropzone"] [data-testid="stBaseButton-secondary"],
[data-testid="stFileUploaderDropzone"] [data-testid="stBaseButton-secondary"] p,
[data-testid="stFileUploaderDropzone"] [data-testid="stBaseButton-secondary"] span {
    display: none !important;
}

/* --- Markdown 内容样式 --- */
.markdown-text {
    line-height: 1.8;
    color: #4A4543;
}

/* --- 下载按钮 --- */
.stDownloadButton > button {
    background-color: #C68A1E !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}
.stDownloadButton > button:hover {
    background-color: #B07810 !important;
}

/* --- Expander 折叠面板 --- */
.streamlit-expander {
    border: 1px solid #F0D9A0 !important;
    border-radius: 10px !important;
    background: #FFFDF8 !important;
}
.streamlit-expander > details > summary {
    font-weight: 600;
    color: #E3700D;
}

/* --- Dataframe 表格 --- */
[data-testid="stDataFrame"] {
    border: 1px solid #F0D9A0 !important;
    border-radius: 10px !important;
}
[data-testid="stDataFrame"] thead th {
    background: linear-gradient(135deg, #E3700D, #C68A1E) !important;
    color: white !important;
    font-weight: 600;
    border: none !important;
}
[data-testid="stDataFrame"] tbody tr:hover {
    background: #FFF9F0 !important;
}

/* --- 滚动条美化 --- */
::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}

::-webkit-scrollbar-thumb {
    background: #E8C87A;
    border-radius: 3px;
}

::-webkit-scrollbar-track {
    background: #FFF9F0;
}

/* --- 高亮选中文字 --- */
::-moz-selection {
    background: rgba(227,112,13,0.25);
    color: #2C2A29;
}

::selection {
    background: rgba(227,112,13,0.25);
    color: #2C2A29;
}
</style>

"""

# 全局网络超时配置 (单位: 秒)
# connect_timeout: 连接服务器超时时间
# read_timeout: 等待 AI 生成内容的超时时间
NETWORK_TIMEOUT = (60, 120)
# 模型配置
MODEL_OPTIONS = {
    "自定义三方Gemini": ["gemini-3.1-pro-preview"],
    "阿里云通义千问": ["qwen3-max", "qwen-plus", "qwen-turbo", "qwen3.5-flash", "deepseek-r1", "deepseek-v3"],
    "Google Gemini": ["gemini-3-flash-preview", "gemini-3-pro-preview", "gemini-3.1-pro-preview"],
    "Google Gemini (OpenAI兼容)": ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro"],
    "OpenAI (GPT)": ["gpt-4o", "gpt-4-turbo", "gpt-4o-mini", "gpt-3.5-turbo"],
    "Anthropic (Claude)": ["claude-3-5-sonnet-20240620", "claude-3-opus-20240229", "claude-3-haiku-20240307"],
    "OpenRouter": ["anthropic/claude-opus-4.6", "anthropic/claude-sonnet-4.6", "gpt-4o", "deepseek/deepseek-v3.2"]
}

# API基础URL
API_BASE_URLS = {
    "自定义三方Gemini": "https://aigateway.edgecloudapp.com/v1/5087eed27d04cd00349d210e10fe620e/gemini-redbird",
    "OpenRouter": "https://openrouter.ai/api/v1",
    "阿里云通义千问": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "Google Gemini (OpenAI 兼容)": "https://generativelanguage.googleapis.com/v1beta/openai/"
}

# 🌟 新增：模式名称常量，避免硬编码耦合
NOVEL_MODE_NAME = "小说智能分镜脚本模式 (动态集数)"
SCRIPT_MODE_NAME = "剧本创作模式"


def setup_logger(name: str = "ScriptMaster", level: int = logging.INFO) -> logging.Logger:
    """
    配置并返回logger实例

    Args:
        name: logger名称
        level: 日志级别

    Returns:
        Logger实例
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        logger.setLevel(level)

        # 创建控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)

        # 设置日志格式
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)

        # 添加处理器
        logger.addHandler(console_handler)

    return logger
