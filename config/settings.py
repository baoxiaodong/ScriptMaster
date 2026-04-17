"""
配置模块
"""
import logging
import sys

# Streamlit页面配置
PAGE_CONFIG = {
    "page_title": "ScriptMaster~AI 分镜工坊",
    "page_icon": "🎬",
    "layout": "wide"
}

CUSTOM_CSS = """
<style>
/* --- 全局背景 & 文字 --- */
.stApp {
    background: linear-gradient(180deg, #FFF9F0 0%, #FFF5E6 100%);
}

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
}
.stButton > button:disabled {
    background-color: #F5D9A8 !important;
    color: rgba(74,69,67,0.5) !important;
    box-shadow: none !important;
}
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
.stProgress > div > div > div > div { background-color: #E3700D !important; }
.stRadio > div > label:hover { color: #C65F00 !important; }

[data-testid="stSelectbox"] .stSelectbox, [data-testid="stSelectbox"] [data-baseweb="select"] { border-color: #E8C87A !important; }
[data-testid="stSelectbox"] [data-baseweb="select"] > div { background-color: #FFF9F0 !important; border-color: #E8C87A !important; }

[data-testid="stTextInput"] input { border-color: #E8C87A !important; background-color: #FFFDF8 !important; border-radius: 8px !important; }
[data-testid="stTextInput"] input:focus { border-color: #E3700D !important; }

.stTabs [data-baseweb="tab-list"] { gap: 4px; background: #FFF5E6; border-radius: 10px; padding: 4px; }
.stTabs [data-baseweb="tab"] { border-radius: 7px; font-weight: 600; color: #4A4543; }
.stTabs [aria-selected="true"] { background-color: #E3700D !important; color: #FFFFFF !important; box-shadow: 0 2px 8px rgba(227,112,13,0.3); }

.step-card { background: #FFFFFF; border: 1.5px solid #F0D9A0; border-radius: 12px; padding: 20px 24px; margin-bottom: 16px; box-shadow: 0 2px 12px rgba(198,138,30,0.1); }
.step-title { font-size: 17px; font-weight: 700; color: #2C2A29; }
.step-desc { font-size: 13px; color: #7A756F; margin-top: 2px; }

[data-testid="stSidebar"] { background: linear-gradient(180deg, #FFF5E6 0%, #FFEDD0 100%) !important; border-right: 2px solid #E8C87A !important; }
[data-testid="stSidebar"] [data-testid="stHeader"] { background: transparent !important; }
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { color: #E3700D !important; }

hr { border: none; border-top: 1.5px solid #F0D9A0 !important; }

/* 恢复最初版本的文件上传框样式 */
[data-testid="stFileUploaderDropzone"] {
    background: #FFFDF8;
    border: 2px dashed #E8C87A;
    border-radius: 12px;
}
[data-testid="stFileUploaderDropzone"]:hover {
    border-color: #E3700D;
    background: #FFF9F0;
}
[data-testid="stFileUploaderDropzoneInstructions"],
[data-testid="stFileUploaderDropzoneInstructions"] span,
[data-testid="stFileUploaderDropzoneInstructions"] label {
    display: none !important;
}
[data-testid="stFileUploaderDropzone"] [data-testid="stBaseButton-secondary"],
[data-testid="stFileUploaderDropzone"] [data-testid="stBaseButton-secondary"] p,
[data-testid="stFileUploaderDropzone"] [data-testid="stBaseButton-secondary"] span {
    display: none !important;
}

.stDownloadButton > button { background-color: #C68A1E !important; color: white !important; }
.streamlit-expander { border: 1px solid #F0D9A0 !important; border-radius: 10px !important; background: #FFFDF8 !important; }
.streamlit-expander > details > summary { font-weight: 600; color: #E3700D; }
[data-testid="stDataFrame"] { border: 1px solid #F0D9A0 !important; border-radius: 10px !important; }
[data-testid="stDataFrame"] thead th { background: linear-gradient(135deg, #E3700D, #C68A1E) !important; color: white !important; font-weight: 600; border: none !important; }
</style>
"""
# 🌟 模式名称常量，避免硬编码耦合
NOVEL_MODE_NAME = "小说智能分镜脚本模式 (动态集数)"
SCRIPT_MODE_NAME = "剧本创作模式"
PROMPT_STUDIO_MODE_NAME = "🧠 提示词调优工坊"
# 全局网络超时配置 (单位: 秒)
# 🌟 新增：全局网络超时配置 (单位: 秒)
# connect_timeout: 连接服务器超时时间
# read_timeout: 等待 AI 生成内容的超时时间
NETWORK_TIMEOUT = (60, 120)
API_BASE_URLS = {
    "自定义三方Gemini": "https://aigateway.edgecloudapp.com/v1/5087eed27d04cd00349d210e10fe620e/gemini-redbird",
    "OpenRouter": "https://openrouter.ai/api/v1",
    "阿里云通义千问": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "Google Gemini (OpenAI 兼容)": "https://generativelanguage.googleapis.com/v1beta/openai/"
}
MODEL_OPTIONS = {
    "自定义三方Gemini": ["gemini-3.1-pro-preview"],
    "阿里云通义千问": ["qwen3-max", "qwen-plus", "qwen-turbo"],
    "Google Gemini": ["gemini-3-flash-preview", "gemini-3-pro-preview", "gemini-3.1-pro-preview"],
    "OpenAI (GPT)": ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]
}


def setup_logger(name: str = "XiaoShuoFenjing", level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(level)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    return logger
