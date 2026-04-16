""" 状态管理模块 - 优化版 v3.0
优化内容：
1. 完美补齐所有业务命名空间的 Key 映射
2. 彻底解决模式切换时的数据污染问题
"""

import streamlit as st

from core.llm_service import LLMService


class StateManager:
    """状态管理器"""

    # 🌟 修复：必须涵盖你在 novel 和 script 模块里定义的所有状态锁
    NAMESPACES = {
        'novel_mode': [
            'novel_results', 'novel_outline', 'novel_is_generating', 'total_episodes',
            'selected_chapter_indices', 'chapter_select_mode', 'novel_selected_df'
        ],
        'script_mode': [
            'scripts', 'outline', 'generated_acts', 'selected_act', 'script_is_generating',
            'script_total_episodes', 'selected_act_index'
        ],
        'common': ['generated_results', 'selected_chapters', '_last_mode', 'ui_clear_trigger']
    }

    @staticmethod
    def init():
        if 'llm_service' not in st.session_state:
            st.session_state.llm_service = LLMService()
        if 'generated_results' not in st.session_state:
            st.session_state.generated_results = {}
        if 'selected_chapters' not in st.session_state:
            st.session_state.selected_chapters = []
        if '_initialized_namespaces' not in st.session_state:
            st.session_state._initialized_namespaces = []

    @staticmethod
    def reset_for_new_mode():
        # 清理所有已知命名空间
        all_keys_to_clear = []
        for namespace, keys in StateManager.NAMESPACES.items():
            all_keys_to_clear.extend(keys)

        temp_prefixes = ['_cached', '_temp', '_novel_', '_script_']
        all_session_keys = list(st.session_state.keys())

        for key in all_session_keys:
            should_delete = (
                    key in all_keys_to_clear or
                    any(key.startswith(prefix) for prefix in temp_prefixes)
            )
            if should_delete:
                del st.session_state[key]

        # 重置LLMService缓存防止错乱
        if 'llm_service' in st.session_state:
            old_service = st.session_state.llm_service
            if hasattr(old_service, '_client_cache'):
                old_service._client_cache.clear()

        st.session_state._initialized_namespaces = []

    @staticmethod
    def get_llm_service() -> LLMService:
        service = st.session_state.get('llm_service')
        if service is None:
            service = LLMService()
            st.session_state.llm_service = service
        return service

    @staticmethod
    def get_results() -> dict:
        return st.session_state.get('generated_results', {})

    @staticmethod
    def set_results(results: dict):
        st.session_state.generated_results = results

    @staticmethod
    def clear_results():
        st.session_state.generated_results = {}

    @staticmethod
    def get(key: str, default=None):
        return st.session_state.get(key, default)

    @staticmethod
    def set(key: str, value):
        st.session_state[key] = value

    @staticmethod
    def delete(key: str):
        if key in st.session_state:
            del st.session_state[key]