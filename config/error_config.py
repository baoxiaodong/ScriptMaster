"""
全局错误处理配置 - 统一管理错误类型、样式和提示信息
便于维护和扩展
"""
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class ErrorTemplate:
    """错误模板数据类"""
    icon: str
    title: str
    suggestion: str
    color_primary: str = "#ff6b6b"
    color_background: str = "linear-gradient(135deg, #fff5f5 0%, #ffe5e5 100%)"
    color_border: str = "#ff6b6b"


class ErrorConfig:
    """
    全局错误配置中心

    职责：
    1. 定义所有错误类型的模板
    2. 提供错误分类规则
    3. 管理错误提示文案
    """

    # ==================== 错误模板库 ====================
    ERROR_TEMPLATES: Dict[str, ErrorTemplate] = {
        "api_error": ErrorTemplate(
            icon="🔌",
            title="AI 服务连接失败",
            suggestion="请检查您的 API Key 是否正确，或确认网络连接正常",
            color_primary="#ff6b6b"
        ),
        "file_error": ErrorTemplate(
            icon="📄",
            title="文件处理出错",
            suggestion="请确认文件格式正确且未损坏，文件大小不超过限制",
            color_primary="#ff9f43"
        ),
        "parse_error": ErrorTemplate(
            icon="📝",
            title="内容解析失败",
            suggestion="请检查文本格式是否符合要求，避免特殊字符干扰",
            color_primary="#ee5a24"
        ),
        "timeout": ErrorTemplate(
            icon="⏰",
            title="请求超时",
            suggestion="AI 服务响应时间过长，请稍后重试或选择更快的模型",
            color_primary="#feca57"
        ),
        "rate_limit": ErrorTemplate(
            icon="🚦",
            title="请求频率过高",
            suggestion="请稍等片刻再试，避免短时间内频繁请求",
            color_primary="#ff6348"
        ),
        "validation_error": ErrorTemplate(
            icon="⚠️",
            title="输入验证失败",
            suggestion="请检查输入内容是否符合要求，确保必填项已填写",
            color_primary="#ffa502"
        ),
        "unknown": ErrorTemplate(
            icon="⚠️",
            title="未知错误",
            suggestion="系统遇到意外问题，建议重置状态后重试",
            color_primary="#ff6b6b"
        )
    }

    # ==================== 错误关键词映射 ====================
    ERROR_KEYWORDS: Dict[str, List[str]] = {
        "api_error": [
            'api', 'api_key', 'authentication', 'unauthorized',
            'invalid key', 'forbidden', '401', '403'
        ],
        "timeout": [
            'timeout', 'timed out', 'deadline', 'connection timeout',
            'read timeout', 'request timeout'
        ],
        "rate_limit": [
            'rate limit', 'too many requests', '429', 'throttled',
            'quota exceeded', 'rate limited'
        ],
        "file_error": [
            'file', 'no such file', 'permission denied', 'encoding',
            'file not found', 'ioerror', 'unicode', 'decode'
        ],
        "parse_error": [
            'parse', 'json', 'format', 'invalid', 'syntax',
            'malformed', 'expected', 'unexpected token'
        ],
        "validation_error": [
            'validation', 'required', 'missing', 'empty',
            'invalid input', 'parameter error'
        ]
    }

    # ==================== 常见错误友好映射 ====================
    FRIENDLY_MESSAGES: Dict[str, tuple] = {
        # API 相关
        'api_key': ("API 密钥验证失败", "请检查侧边栏中的 API Key 是否正确填写"),
        'unauthorized': ("API 密钥验证失败", "您的 API Key 无效或已过期，请重新配置"),
        'authentication': ("身份验证失败", "请确认 API Key 和服务商配置正确"),

        # 网络相关
        'connection': ("网络连接问题", "无法连接到 AI 服务，请检查网络设置"),
        'network': ("网络连接异常", "请确认网络通畅后再试"),

        # 超时相关
        'timeout': ("请求超时", "AI 服务响应时间过长，请稍后重试"),
        'timed out': ("操作超时", "处理时间超过限制，请尝试减少单次处理量"),

        # 频率限制
        'rate limit': ("请求过于频繁", "请稍等片刻后再试"),
        'too many requests': ("请求频率超限", "系统限制了请求速度，请耐心等待"),
        '429': ("频率限制", "您已达到请求上限，请稍后重试"),

        # 文件相关
        'file not found': ("文件未找到", "上传的文件不存在或已被删除"),
        'no such file': ("文件路径错误", "请确认文件路径正确且文件存在"),
        'permission denied': ("权限不足", "没有权限访问该文件，请检查文件权限"),
        'encoding': ("编码错误", "文件格式编码不支持，请转换为 UTF-8 格式"),

        # 数据相关
        'json': ("数据格式错误", "返回的数据格式不正确，请联系技术支持"),
        'parse': ("解析失败", "无法解析返回的内容，请检查输入格式")
    }

    # ==================== CSS 样式配置 ====================
    CSS_STYLES = """
    <style>
    /* 🛡️ 全局错误提示容器样式 */
    .error-container {
        background: linear-gradient(135deg, #fff5f5 0%, #ffe5e5 100%);
        border-left: 5px solid #ff6b6b;
        border-radius: 12px;
        padding: 30px;
        margin: 20px 0;
        box-shadow: 0 4px 15px rgba(255, 107, 107, 0.2);
        text-align: center;
        animation: fadeIn 0.3s ease-in;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .error-icon {
        font-size: 48px;
        margin-bottom: 15px;
        animation: bounce 1s infinite;
    }
    
    @keyframes bounce {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-10px); }
    }
    
    .error-title {
        color: #d63031;
        font-size: 24px;
        font-weight: 700;
        margin: 10px 0;
    }
    
    .error-suggestion {
        color: #636e72;
        font-size: 16px;
        margin: 15px 0;
        padding: 12px 15px;
        background: rgba(255, 255, 255, 0.7);
        border-radius: 8px;
        border-left: 3px solid #74b9ff;
    }
    
    .error-details {
        margin-top: 20px;
        padding: 15px;
        background: #ffffff;
        border-radius: 8px;
        font-family: 'Courier New', monospace;
        font-size: 13px;
        color: #2d3436;
        max-height: 200px;
        overflow-y: auto;
        text-align: left;
        border: 1px solid #dfe6e9;
    }
    
    .error-details::-webkit-scrollbar {
        width: 8px;
    }
    
    .error-details::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 4px;
    }
    
    .error-details::-webkit-scrollbar-thumb {
        background: #ff6b6b;
        border-radius: 4px;
    }
    
    .error-details::-webkit-scrollbar-thumb:hover {
        background: #ee5a24;
    }
    </style>
    """

    @classmethod
    def get_template(cls, error_type: str) -> ErrorTemplate:
        """获取错误模板"""
        return cls.ERROR_TEMPLATES.get(error_type, cls.ERROR_TEMPLATES["unknown"])

    @classmethod
    def classify_error(cls, exception: Exception) -> str:
        """
        根据异常智能分类错误类型

        Args:
            exception: 捕获的异常对象

        Returns:
            错误类型字符串
        """
        error_str = str(exception).lower()
        exception_type = type(exception).__name__.lower()
        combined_text = f"{error_str} {exception_type}"

        # 遍历所有错误类型的关键词
        for error_type, keywords in cls.ERROR_KEYWORDS.items():
            if any(keyword in combined_text for keyword in keywords):
                return error_type

        return "unknown"

    @classmethod
    def get_friendly_message(cls, exception: Exception) -> tuple:
        """
        将技术异常转换为用户友好的消息

        Args:
            exception: 捕获的异常对象

        Returns:
            (简短标题, 详细说明) 元组
        """
        error_str = str(exception).lower()

        # 遍历友好消息映射
        for keyword, (title, detail) in cls.FRIENDLY_MESSAGES.items():
            if keyword in error_str:
                return (title, detail)

        # 默认返回
        exception_type = type(exception).__name__
        return (
            f"{exception_type} 错误",
            f"系统遇到了一个技术问题：{str(exception)[:200]}"
        )

    @classmethod
    def add_custom_template(cls, error_type: str, template: ErrorTemplate):
        """
        动态添加自定义错误模板

        Args:
            error_type: 错误类型标识
            template: 错误模板对象
        """
        cls.ERROR_TEMPLATES[error_type] = template

    @classmethod
    def add_custom_keywords(cls, error_type: str, keywords: List[str]):
        """
        为指定错误类型添加新的关键词

        Args:
            error_type: 错误类型标识
            keywords: 关键词列表
        """
        if error_type not in cls.ERROR_KEYWORDS:
            cls.ERROR_KEYWORDS[error_type] = []
        cls.ERROR_KEYWORDS[error_type].extend(keywords)