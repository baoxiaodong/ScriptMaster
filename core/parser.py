import csv
import io
import logging
import re

import pandas as pd

logger = logging.getLogger("ScriptMaster.Parser")


class ScriptParser:
    @staticmethod
    def parse_csv(csv_text: str) -> pd.DataFrame:
        """
        深度优化版：解析带有高度容错机制的 CSV 脚本数据。
        解决了 AI 话痨、Markdown 嵌套、列名变体、以及 CSV 行污染问题。
        """
        if not csv_text or not isinstance(csv_text, str):
            return pd.DataFrame()

        # 1. 基础预处理
        # 替换中文逗号，移除 Markdown 标记
        text = csv_text.replace('```', '').strip()
        # 🌟 降维打击：统一分隔符
        text = text.replace('，', ',').replace('|', ',')

        # --- 监控日志：记录清洗后状态 ---
        logger.info(f"🧹 [解析监控] 完成基础清洗，当前可用长度: {len(text)}")

        lines = text.split('\n')
        parsed_data = []
        rejected_count = 0

        # 🌟 新增：跳过 AI 输出的前导说明文字，找到真正的 CSV 起始位置
        csv_start_idx = 0
        for idx, line in enumerate(lines):
            # 如果找到包含"镜号"或"Shot"的行，或者包含"第 X 集"的行，说明 CSV 开始了
            if any(kw in line for kw in ["镜号", "Shot", "第", "Episode"]):
                csv_start_idx = idx
                logger.info(f"📍 [解析监控] 找到 CSV 起始位置：第 {idx} 行")
                break

        # 从 CSV 起始位置开始解析
        for idx in range(csv_start_idx, len(lines)):
            line = lines[idx].strip()
            if not line:
                continue
            # 🌟 识别集数行（例如：第1集）
            ep_match = re.search(r'(?:第|Episode)\s*(\d+)\s*(?:集|Chapter)', line, re.IGNORECASE)
            if ep_match:
                parsed_data.append([f"第{ep_match.group(1)}集", "", "", ""])
                logger.info(f"📍 [解析监控] 识别到集数标记: 第{ep_match.group(1)}集")
                continue

            # 过滤掉明显的表头和对齐线
            if re.match(r'^[-:,\s]+$', line):
                continue

            # 判定表头并跳过
            if any(kw in line for kw in ["镜号", "场景", "画面", "台词", "Shot", "Scene", "Visual", "Dialogue"]):
                if not any(char.isdigit() for char in line[:10]):
                    logger.debug(f"⏭️ [解析监控] 跳过可能的表头行: {line[:30]}")
                    continue

            # 使用 CSV Reader 解析当前行
            parts = []
            row_io = io.StringIO(line)
            try:
                reader = csv.reader(row_io)
                parts = next(reader)
            except:
                parts = [p.strip() for p in line.split(',')]

            # 🌟 去除首尾空元素 (解决 Markdown 替换带来的额外逗号)
            while parts and not str(parts[0]).strip(): parts.pop(0)
            while parts and not str(parts[-1]).strip(): parts.pop()

            if not parts:
                rejected_count += 1
                continue

            # --- 核心判定逻辑 ---
            first_col = str(parts[0]).strip()
            shot_num_match = re.search(r'\d+', first_col)  # 提取第一列中的数字
            non_empty_parts = [p for p in parts if p.strip()]

            # 准入规则：
            # 1. 第一列包含数字 (如 1. 或 **1**)
            # 2. 或者这行内容非常丰富（至少3列有内容）
            if shot_num_match or len(non_empty_parts) >= 3:
                clean_shot = shot_num_match.group(0) if shot_num_match else first_col

                # 规范化 4 列
                row_data = [""] * 4
                row_data[0] = clean_shot
                for i in range(1, min(len(parts), 4)):
                    row_data[i] = str(parts[i]).strip()

                # 多余列合并
                if len(parts) > 4:
                    row_data[3] = (row_data[3] + " " + " ".join(parts[4:])).strip()

                # 排除被误判的集数行
                if "第" in row_data[0] and "集" in row_data[0]:
                    continue

                parsed_data.append(row_data)
            else:
                rejected_count += 1
                if rejected_count <= 5:  # 只打印前 5 条被拒绝的理由，防止日志爆炸
                    logger.warning(f"⚠️ [解析监控] 行 {idx} 被拒绝 (无数字且内容不足): {line[:50]}...")

        # 5. 总结报告
        if not parsed_data:
            logger.error("❌ [解析监控] 关键错误：全文遍历结束，未提取到任何有效数据行！")
            logger.info(f"💡 [诊断建议] 请检查 AI 的返回内容。如果预览中全是段落文字而没有表格/CSV，说明提示词需要优化。")
            return pd.DataFrame()

        final_cols = ['镜号', '场景', '画面内容 (Visual)', '台词 (Dialogue) & 音效 (SFX)']
        df = pd.DataFrame(parsed_data, columns=final_cols)

        # 🌟 新增：后处理 - 自动清洗第 4 列（台词列），确保只保留纯英文
        if not df.empty and len(df.columns) >= 4:
            def clean_dialogue_column(row):
                dialogue_col = str(row.get('台词 (Dialogue) & 音效 (SFX)', ''))
                if not dialogue_col:
                    return row

                # 🌟 暴力清洗：直接移除所有中文字符和中文标点
                clean_dialogue = re.sub(r'[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]+', '', dialogue_col).strip()

                # 清理多余空格
                clean_dialogue = re.sub(r'\s+', ' ', clean_dialogue).strip()

                row['台词 (Dialogue) & 音效 (SFX)'] = clean_dialogue
                return row

            df = df.apply(clean_dialogue_column, axis=1)

        return df

    @staticmethod
    def _parse_markdown_table(text: str) -> pd.DataFrame:
        return ScriptParser.parse_csv(text)

    @staticmethod
    def _fallback_parse(text: str) -> pd.DataFrame:
        return ScriptParser.parse_csv(text)
