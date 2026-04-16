""" 状态管理模块 - 优化版 v2.0
优化内容：
1. 使用命名空间管理key，防止遗漏
2. 模式切换时重置LLMService
3. 增强清理能力
"""

import streamlit as st

from core.llm_service import LLMService


class StateManager:
    """状态管理器"""

    # 🌟 新增：命名空间定义
    NAMESPACES = {
        'novel_mode': ['novel_results', 'novel_outline', 'novel_is_generating', 'total_episodes',
                       'selected_chapter_indices', 'chapter_select_mode'],
        'script_mode': ['scripts', 'outline', 'generated_acts', 'selected_act', 'script_is_generating',
                        'script_total_episodes'],
        'common': ['generated_results', 'selected_chapters', '_last_mode']
    }

    @staticmethod
    def init():
        """初始化会话状态"""
        if 'llm_service' not in st.session_state:
            st.session_state.llm_service = LLMService()
        if 'generated_results' not in st.session_state:
            st.session_state.generated_results = {}
        if 'selected_chapters' not in st.session_state:
            st.session_state.selected_chapters = []
        # 🌟 新增：初始化命名空间标记
        if '_initialized_namespaces' not in st.session_state:
            st.session_state._initialized_namespaces = []

    @staticmethod
    def reset_for_new_mode():
        """
        清理所有业务数据，防止模式切换干扰
        🌟 改进：使用命名空间批量清理 + 重置服务
        """
        # 1. 清理已知命名空间的所有key
        all_keys_to_clear = []
        for namespace, keys in StateManager.NAMESPACES.items():
            all_keys_to_clear.extend(keys)

        # 2. 清理临时缓存（以特定前缀开头）
        temp_prefixes = ['_cached', '_temp', '_novel_', '_script_']

        all_session_keys = list(st.session_state.keys())
        keys_deleted = []

        for key in all_session_keys:
            should_delete = (
                    key in all_keys_to_clear or
                    any(key.startswith(prefix) for prefix in temp_prefixes)
            )

            if should_delete:
                del st.session_state[key]
                keys_deleted.append(key)

        if keys_deleted:
            import logging
            logging.getLogger("ScriptMaster.StateManager").info(f"清理状态键: {len(keys_deleted)} 个")

        # 🌟 新增：重置LLMService（防止配置不同步）
        if 'llm_service' in st.session_state:
            old_service = st.session_state.llm_service
            # 保留配置但清除缓存的客户端
            if hasattr(old_service, '_client_cache'):
                old_service._client_cache.clear()

        # 重置初始化标记
        st.session_state._initialized_namespaces = []

    @staticmethod
    def get_llm_service() -> LLMService:
        """获取LLM服务（确保配置最新）"""
        service = st.session_state.get('llm_service')
        if service is None:
            service = LLMService()
            st.session_state.llm_service = service
        return service

    @staticmethod
    def get_results() -> dict:
        """获取生成结果"""
        return st.session_state.get('generated_results', {})

    @staticmethod
    def set_results(results: dict):
        """设置生成结果"""
        st.session_state.generated_results = results

    @staticmethod
    def clear_results():
        """清空结果"""
        st.session_state.generated_results = {}

    # 🌟 新增：安全的键值操作方法
    @staticmethod
    def get(key: str, default=None):
        """安全获取状态值"""
        return st.session_state.get(key, default)

    @staticmethod
    def set(key: str, value):
        """安全设置状态值"""
        st.session_state[key] = value

    @staticmethod
    def delete(key: str):
        """安全删除状态键"""
        if key in st.session_state:
            del st.session_state[key]
