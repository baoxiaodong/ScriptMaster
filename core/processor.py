import concurrent.futures
import logging
import re
import time
from threading import Lock
from typing import Callable, Dict, Optional

import pandas as pd
from core.llm_service import LLMService
from core.parser import ScriptParser
from core.prompts import PromptTemplates

logger = logging.getLogger("ScriptMaster.Processor")


class NovelModeProcessor:
    """小说模式处理器 - 支持安全截断、并发容错与固定集数"""

    def __init__(self, llm_service: LLMService, total_episodes: int = 20):
        self.llm_service = llm_service
        self.results_lock = Lock()
        self.parser = ScriptParser()
        self.total_episodes = total_episodes
        self.system_prompt = PromptTemplates.SCRIPT_SYSTEM
        self.user_template = PromptTemplates.BATCH_SCRIPT_PROMPT

    def generate_outline(self, df: pd.DataFrame, on_progress: Optional[Callable] = None) -> str:
        """生成小说大纲功能 - 支持超长文本分段处理"""
        full_text = self._combine_chapters(df)
        text_length = len(full_text)
        logger.info(f"📝 文本长度: {text_length}")

        if on_progress:
            # 🌟 根据文本长度动态显示提示语
            if text_length > 50000:
                progress_text = f"🚀 正在生成{self.total_episodes}集分集大纲（小说长度{text_length:,}字，内容较长请耐心等待）..."
            else:
                progress_text = f"🚀 正在生成{self.total_episodes}集分集大纲..."
            on_progress(progress_text, 0)

        try:
            # 🌟 超长文本分段处理阈值
            MAX_CHUNK_SIZE = 30000
            if text_length <= MAX_CHUNK_SIZE:
                # 文本不长，直接生成
                logger.info("📝 文本长度正常，直接生成")
                return self._generate_outline_from_text(full_text, on_progress)
            else:
                # 超长文本，分段处理
                chunk_count = text_length // MAX_CHUNK_SIZE + 1
                logger.info(f"📝 文本超长，分 {chunk_count} 段处理")
                return self._generate_outline_from_long_text(full_text, text_length, on_progress)
        except Exception as e:
            logger.error(f"❌ 大纲生成失败: {str(e)}", exc_info=True)
            raise

    def _generate_outline_from_text(self, text: str, on_progress: Optional[Callable] = None) -> str:
        """从文本生成大纲（单次调用）"""
        prompt = PromptTemplates.OUTLINE_TASK.format(
            total_episodes=self.total_episodes,
            user_choice=text
        )

        outline_text = self.llm_service.generate(
            PromptTemplates.OUTLINE_SYSTEM,
            prompt
        )

        logger.info(f"📝 API返回: {len(outline_text)} 字")

        if outline_text.startswith("❌"):
            raise Exception(outline_text)

        if on_progress:
            on_progress(f"✅ {self.total_episodes}集大纲生成完成", 100)

        return outline_text

    def _generate_outline_from_long_text(self, full_text: str, original_length: int,
                                         on_progress: Optional[Callable] = None) -> str:
        """从超长文本生成大纲（分段摘要合并策略 - 并行加速）"""
        import concurrent.futures
        from threading import Lock

        MAX_CHUNK_SIZE = 30000
        chunks = [full_text[i:i + MAX_CHUNK_SIZE] for i in range(0, len(full_text), MAX_CHUNK_SIZE)]
        total_chunks = len(chunks)

        # 🌟 计算总预计时间（并行处理，5个并发同时跑，每段约 40 秒）
        estimated_total_minutes = max(2, (total_chunks * 40 // 5 + 60) // 60)

        summaries = [None] * total_chunks
        progress_lock = Lock()
        completed = 0

        def _summarize_chunk(idx, chunk):
            """处理单个段落摘要"""
            logger.info(f"📝 处理第 {idx + 1}/{total_chunks} 段")

            summary_prompt = f"""请简要总结以下小说内容的主要情节、人物和关键事件（500字以内）：

    {chunk}

    总结："""

            summary = self.llm_service.generate(
                "你是一个专业的小说编辑，擅长提炼故事核心内容。",
                summary_prompt
            )
            return idx, f"【第{idx + 1}段摘要】\n{summary}"

        # 🌟 并行处理所有段落摘要（最多 5 个同时处理）
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_idx = {executor.submit(_summarize_chunk, idx, chunk): idx
                             for idx, chunk in enumerate(chunks)}

            for future in concurrent.futures.as_completed(future_to_idx):
                idx, summary = future.result()
                summaries[idx] = summary

                with progress_lock:
                    completed += 1
                    if on_progress:
                        progress_val = int((completed / total_chunks) * 60)
                        on_progress(
                            f"📝 正在分析大纲第 {completed}/{total_chunks} 段（小说{original_length:,}字，总预计{estimated_total_minutes}分钟）...",
                            progress_val)

        combined_summaries = "\n\n".join(summaries)
        logger.info(f"📝 摘要合并完成，长度: {len(combined_summaries)}")

        if on_progress:
            on_progress(f"📝 正在基于摘要生成完整大纲（总预计{estimated_total_minutes}分钟）...", 60)

        return self._generate_outline_from_text(combined_summaries, on_progress)

    def _combine_chapters(self, df: pd.DataFrame) -> str:
        """合并章节"""
        contents = []
        for row in df.itertuples(index=False):
            title = str(row[0]) if pd.notna(row[0]) else ""
            content = str(row[1]) if pd.notna(row[1]) else ""
            if content.strip():
                label = title if title else f"章节{len(contents) + 1}"
                contents.append(f"【{label}】\n{content}")

        return "\n\n".join(contents)

    def _split_batches(self, df: pd.DataFrame, start_ep: int, end_ep: int) -> Dict[str, pd.DataFrame]:
        """将 AI 生成的大表按集数拆分为字典"""
        results = {}
        if df.empty:
            return {f"第{i}集": pd.DataFrame() for i in range(start_ep, end_ep + 1)}

        current_ep = None  # 当前集 key
        ep_num = start_ep - 1  # 当前实际集号
        temp_rows = []
        prev_shot = 0  # 上一个镜头号，用于检测镜头重置

        for _, row in df.iterrows():
            val = str(row.get('镜号', '')).strip()

            # 优先识别明确的"第X集"标记行
            ep_match = re.search(r'第\s*(\d+)\s*集', val)
            if ep_match:
                if current_ep and temp_rows:
                    results[current_ep] = pd.DataFrame(temp_rows, columns=df.columns)
                ep_num = int(ep_match.group(1))
                current_ep = val
                temp_rows = []
                prev_shot = 0
                continue

            # 提取镜头号
            shot_match = re.search(r'\d+', val)
            if not shot_match:
                continue
            shot_num = int(shot_match.group(0))

            # 兜底分集：当镜头号重置到 ≤3 且已有数据时，自动创建新集
            # （AI 通常每个集从镜头1开始，不会从99直接跳到1）
            if shot_num <= 3 and temp_rows and shot_num < prev_shot:
                results[current_ep] = pd.DataFrame(temp_rows, columns=df.columns)
                ep_num += 1
                current_ep = f"第{ep_num}集"
                temp_rows = []
                prev_shot = 0

            # 首个镜头：自动创建第1集（处理 AI 忘记输出"第1集"标记行的情况）
            if not current_ep:
                current_ep = f"第{ep_num + 1}集"
                ep_num += 1

            temp_rows.append(row.tolist())
            prev_shot = shot_num

        # 保存最后一部分
        if current_ep and temp_rows:
            results[current_ep] = pd.DataFrame(temp_rows, columns=df.columns)

        # 确保数据完整性（当前批次所有集都要有 key）
        for i in range(start_ep, end_ep + 1):
            key = f"第{i}集"
            if key not in results:
                results[key] = pd.DataFrame(columns=df.columns)

        return results

    def process(self, df: pd.DataFrame = None, on_progress: Optional[Callable] = None,
                existing_results: Optional[Dict[str, pd.DataFrame]] = None,
                full_text: str = None) -> Dict[str, pd.DataFrame]:
        """并行处理入口 - 支持动态配置总集数、跳过已完成批次、以及直接传入文本"""
        import math

        # 🌟 兼容逻辑：如果有 full_text 就直接用，否则从 df 提取
        if full_text is None:
            full_text = self._combine_chapters(df)

        final_results = {}
        TOTAL_EPISODES = self.total_episodes
        EPISODES_PER_BATCH = 3
        total_batches_count = math.ceil(TOTAL_EPISODES / EPISODES_PER_BATCH)

        # 动态生成批次列表，确保最后一批不会超出总集数
        batches = []
        for i in range(total_batches_count):
            s = i * EPISODES_PER_BATCH + 1
            e = min(s + EPISODES_PER_BATCH - 1, TOTAL_EPISODES)

            # 🌟 智能跳过逻辑：如果传入了已有结果，且该批次所有集都已成功，则跳过
            if existing_results:
                all_exist = True
                for ep_num in range(s, e + 1):
                    key = f"第{ep_num}集"
                    res = existing_results.get(key)

                    # 检查是否有效（非报错、非空）
                    is_valid = res is not None and not (isinstance(res, str) and res.startswith("❌"))
                    if hasattr(res, 'empty') and res.empty:
                        is_valid = False

                    if not is_valid:
                        all_exist = False
                        break

                if all_exist:
                    continue  # 跳过该批次

            batches.append((s, e))

        # 如果所有批次都被跳过（理论上不应该发生，除非用户全补全了）
        if not batches:
            return existing_results if existing_results else {}

        completed = 0
        # 更新 total_batches 为实际需要跑的批次数量
        total_batches = len(batches)

        def _worker(start, end):
            # 🚀 新增：确认线程是否启动
            logger.info(f"\n▶️ [线程启动] 正在接单：开始处理第 {start}-{end} 集的内容...")
            # 梯度错峰启动 0.5 秒
            time.sleep((start // EPISODES_PER_BATCH) * 0.5)

            # 调用 prompts.py 中定义的模板，传入总集数
            prompt = self.user_template.format(
                start_ep=start,
                end_ep=end,
                content=full_text,
                total_episodes=TOTAL_EPISODES
            )

            max_retries = 2
            for attempt in range(max_retries + 1):
                try:
                    raw_text = self.llm_service.generate(self.system_prompt, prompt)
                    # 🚀 新增：打印AI原始返回内容的前200字符，方便调试
                    logger.info(f"🔍 [批次{start}-{end}] AI原始返回前200字符:\n{raw_text[:200]}")
                    logger.info(f"🔍 [批次{start}-{end}] 是否包含集数标记: {'第' in raw_text and '集' in raw_text}")
                    logger.info(f"🔍 [批次{start}-{end}] 是否包含CSV表头: {'镜号' in raw_text or 'Shot' in raw_text}")
                    if raw_text.startswith("❌"):
                        raise Exception(raw_text)

                    batch_df = self.parser.parse_csv(raw_text)
                    # 🚀 核心修复：如果解析出来是空表格，主动抛出异常，逼迫外层的 for attempt 触发重试
                    if batch_df.empty:
                        raise Exception("解析失败：AI 返回的内容为空或未包含有效的 CSV 格式，触发自动重试！")
                    return self._split_batches(batch_df, start, end)
                except Exception as e:
                    if attempt < max_retries:
                        time.sleep((attempt + 1) * 3)
                        continue
                    return {f"第{i}集": f"❌ Error: {str(e)}" for i in range(start, end + 1)}

        # 执行并行生成
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_to_batch = {executor.submit(_worker, s, e): (s, e) for s, e in batches}

            for future in concurrent.futures.as_completed(future_to_batch):
                s, e = future_to_batch[future]
                try:
                    res = future.result()
                    with self.results_lock:
                        final_results.update(res)
                    completed += 1
                    completed_episodes = min(completed * EPISODES_PER_BATCH, TOTAL_EPISODES)

                    if on_progress:
                        # 显示已完成的集数范围
                        on_progress(f"已完成 {completed_episodes}/{TOTAL_EPISODES} 集",
                                    int(completed / total_batches * 100))
                except Exception as e:
                    with self.results_lock:
                        for i in range(s, e + 1):
                            final_results[f"第{i}集"] = f"❌ Fatal: {str(e)}"

        # 合并已有结果和新结果
        if existing_results:
            existing_results.update(final_results)
            return existing_results

        return final_results
