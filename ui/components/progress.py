"""
进度显示组件模块
"""
import streamlit as st
import time
from typing import Optional


class ProgressTracker:
    """进度追踪器（支持批次状态显示）"""

    def __init__(self):
        self.progress_bar = None
        self.status_text = None
        self._start_time: Optional[float] = None

    def init(self):
        """初始化进度条"""
        self.progress_bar = st.progress(0)
        self.status_text = st.empty()
        self._start_time = time.time()

    def update(self, current: int, total: int, title: str):
        """
        更新进度

        Args:
            current: 当前进度
            total: 总数
            title: 当前处理的标题
        """
        if total <= 0:
            return
        pct = min(current / total, 1.0)
        if self.progress_bar:
            self.progress_bar.progress(pct)

        # 计算预计剩余时间
        eta_str = ""
        if self._start_time and current > 0:
            elapsed = time.time() - self._start_time
            speed = current / elapsed  # 集/秒
            remaining = (total - current) / speed if speed > 0 else 0
            if remaining > 0:
                eta_str = f"  ⏱ 预计还需 {int(remaining)}s"

        if self.status_text:
            bar_filled = int(pct * 20)
            bar_empty = 20 - bar_filled
            bar_str = "█" * bar_filled + "░" * bar_empty
            self.status_text.markdown(
                f"**进度：** `[{bar_str}]` {int(pct * 100)}%  "
                f"({current}/{total} 集){eta_str}  \n"
                f"**状态：** {title}"
            )

    def complete(self, message: str = "生成完成！"):
        """完成进度"""
        if self.progress_bar:
            self.progress_bar.progress(1.0)
        elapsed = ""
        if self._start_time:
            t = time.time() - self._start_time
            elapsed = f"（耗时 {int(t)}s）"
        if self.status_text:
            self.status_text.markdown(f"✅ **{message}** {elapsed}")

    def clear(self):
        """清除进度显示"""
        if self.status_text:
            self.status_text.empty()
        if self.progress_bar:
            self.progress_bar.empty()


class BatchProgressTracker:
    """
    并行批次进度追踪器
    - 总进度条
    - 每批次状态卡片（实时显示运行中/完成/失败）
    """

    def __init__(self, total_batches: int, episodes_per_batch: int):
        self.total_batches = total_batches
        self.episodes_per_batch = episodes_per_batch
        self.total_episodes = total_batches * episodes_per_batch

        self._start_time: Optional[float] = None
        self._progress_bar = None
        self._summary_text = None
        self._batch_slots: list = []  # st.empty() per batch
        self._batch_states: list = []  # "waiting" | "running" | "done" | "failed"

    def init(self):
        """渲染初始 UI"""
        self._start_time = time.time()

        st.markdown("#### 并行生成进度")
        st.info("⏳ **正在并行生成 5 批次...** 每批 6 集，预计 15~40 秒完成")
        self._progress_bar = st.progress(0)
        self._summary_text = st.empty()
        self._summary_text.markdown("🔄 正在初始化...")

        # 批次状态卡片
        cols = st.columns(self.total_batches)
        for i, col in enumerate(cols):
            with col:
                slot = st.empty()
                self._batch_slots.append(slot)
                self._batch_states.append("waiting")
                start_ep = i * self.episodes_per_batch + 1
                end_ep = start_ep + self.episodes_per_batch - 1
                slot.markdown(
                    f"**批次 {i+1}**\n\n"
                    f"第{start_ep}~{end_ep}集\n\n"
                    f"⏳ 等待中"
                )

        self._refresh_summary()

    def set_batch_running(self, batch_idx: int):
        """标记某批次开始运行"""
        self._batch_states[batch_idx] = "running"
        self._render_batch(batch_idx)
        self._refresh_summary()

    def set_batch_done(self, batch_idx: int, shots: int = 0):
        """标记某批次完成"""
        self._batch_states[batch_idx] = "done"
        self._render_batch(batch_idx, shots=shots)
        self._refresh_progress()
        self._refresh_summary()

    def set_batch_failed(self, batch_idx: int, reason: str = ""):
        """标记某批次失败"""
        self._batch_states[batch_idx] = "failed"
        self._render_batch(batch_idx, reason=reason)
        self._refresh_progress()
        self._refresh_summary()

    def _render_batch(self, batch_idx: int, shots: int = 0, reason: str = ""):
        """重新渲染某批次卡片"""
        if batch_idx >= len(self._batch_slots):
            return
        slot = self._batch_slots[batch_idx]
        state = self._batch_states[batch_idx]
        start_ep = batch_idx * self.episodes_per_batch + 1
        end_ep = start_ep + self.episodes_per_batch - 1

        icons = {"waiting": "⏳", "running": "🔄", "done": "✅", "failed": "❌"}
        labels = {"waiting": "等待中", "running": "生成中...", "done": "完成", "failed": "失败"}
        
        icon = icons.get(state, "❓")
        label = labels.get(state, state)
        
        # 只有完成且有镜头数时才显示数字
        if state == "done" and shots > 0:
            label = f"完成 ({shots}镜)"
        elif state == "failed" and reason:
            label = f"失败: {reason[:20]}"

        slot.markdown(
            f"**批次 {batch_idx+1}**\n\n"
            f"第{start_ep}~{end_ep}集\n\n"
            f"{icon} {label}"
        )

    def _refresh_progress(self):
        """刷新总进度条"""
        done = sum(1 for s in self._batch_states if s in ("done", "failed"))
        pct = done / self.total_batches
        if self._progress_bar:
            self._progress_bar.progress(pct)

    def _refresh_summary(self):
        """刷新摘要文字"""
        done = sum(1 for s in self._batch_states if s == "done")
        running = sum(1 for s in self._batch_states if s == "running")
        failed = sum(1 for s in self._batch_states if s == "failed")
        waiting = sum(1 for s in self._batch_states if s == "waiting")

        eta_str = ""
        if self._start_time and done > 0:
            elapsed = time.time() - self._start_time
            speed = done / elapsed
            remaining_batches = self.total_batches - done - failed
            if speed > 0 and remaining_batches > 0:
                eta = remaining_batches / speed
                eta_str = f"  ⏱ 预计还需 {int(eta)}s"

        parts = []
        if running > 0:
            parts.append(f"🔄 运行中 {running}")
        if done > 0:
            parts.append(f"✅ 完成 {done}")
        if failed > 0:
            parts.append(f"❌ 失败 {failed}")
        if waiting > 0:
            parts.append(f"⏳ 等待 {waiting}")

        summary = "  |  ".join(parts) + eta_str
        if self._summary_text:
            self._summary_text.markdown(summary)

    def elapsed(self) -> float:
        """返回已消耗的秒数（供外部调用）"""
        if self._start_time:
            return time.time() - self._start_time
        return 0.0

    def complete(self):
        """全部完成"""
        if self._progress_bar:
            self._progress_bar.progress(1.0)
        t = self.elapsed()
        elapsed_str = f"（总耗时 {int(t)}s）" if t else ""
        if self._summary_text:
            done = sum(1 for s in self._batch_states if s == "done")
            failed = sum(1 for s in self._batch_states if s == "failed")
            self._summary_text.markdown(
                f"✅ **全部完成** {elapsed_str}  —  成功 {done} 批 / 失败 {failed} 批"
            )

    def clear(self):
        """清除所有进度 UI（异常时调用）"""
        for slot in self._batch_slots:
            slot.empty()
        if self._progress_bar:
            self._progress_bar.empty()
        if self._summary_text:
            self._summary_text.empty()

    def get_failed_batches(self) -> list:
        """返回所有失败批次的索引列表"""
        return [i for i, s in enumerate(self._batch_states) if s == "failed"]

    def retry_batches(self, failed_batches: list,
                      generate_fn: callable,
                      on_progress: callable = None) -> tuple:
        """
        逐批重试失败批次（在主线程执行，保证 Streamlit UI 安全写入）。

        Args:
            failed_batches: 失败批次索引列表
            generate_fn: 生成函数，接受 (batch_idx) -> {集数: DataFrame}
            on_progress: 进度回调 (text: str) -> None

        Returns:
            (retry_results: dict, retry_errors: list)
            retry_results: 所有重试成功的 {集数: DataFrame}
            retry_errors: 重试后仍失败的批次索引列表
        """
        retry_results = {}
        retry_errors = []

        for bi in failed_batches:
            # 重置为 running 并刷新 UI（在主线程，安全）
            self.set_batch_running(bi)
            if on_progress:
                start_ep = bi * self.episodes_per_batch + 1
                on_progress(f"🔄 正在重试批次 {bi + 1}（第{start_ep}~{start_ep + self.episodes_per_batch - 1}集）...")

            try:
                batch_result = generate_fn(bi)
                is_error = any(
                    isinstance(v, str) and v.startswith("❌")
                    for v in batch_result.values()
                )
                if is_error:
                    err_vals = [v for v in batch_result.values() if isinstance(v, str)]
                    reason = err_vals[0] if err_vals else "未知错误"
                    self.set_batch_failed(bi, reason[:30])
                    retry_errors.append(bi)
                    if on_progress:
                        on_progress(f"⚠️ 批次{bi + 1} 重试失败: {reason[:50]}")
                else:
                    for k, v in batch_result.items():
                        retry_results[k] = v
                    shots = sum(len(v) for v in batch_result.values() if isinstance(v, pd.DataFrame))
                    self.set_batch_done(bi, shots)
                    if on_progress:
                        on_progress(f"✅ 批次{bi + 1} 重试成功，{shots} 个镜头")

            except Exception as retry_err:
                self.set_batch_failed(bi, str(retry_err)[:30])
                retry_errors.append(bi)
                if on_progress:
                    on_progress(f"⚠️ 批次{bi + 1} 重试异常: {str(retry_err)[:50]}")

        return retry_results, retry_errors
