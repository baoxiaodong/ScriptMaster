import csv
import io
import logging
import re

import pandas as pd

logger = logging.getLogger("ScriptMaster.Parser")


class ScriptParser:
    @staticmethod
    def parse_csv(csv_text: str) -> pd.DataFrame:
        if not csv_text or not isinstance(csv_text, str):
            return pd.DataFrame()

        text = csv_text.replace('```', '').strip()
        text = text.replace('，', ',').replace('|', ',')

        logger.info(f"🧹 [解析监控] 完成基础清洗，当前可用长度: {len(text)}")

        lines = text.split('\n')
        parsed_data = []
        rejected_count = 0

        csv_start_idx = 0
        for idx, line in enumerate(lines):
            if any(kw in line for kw in ["镜号", "Shot", "第", "Episode"]):
                csv_start_idx = idx
                logger.info(f"📍 [解析监控] 找到 CSV 起始位置：第 {idx} 行")
                break

        for idx in range(csv_start_idx, len(lines)):
            line = lines[idx].strip()
            if not line:
                continue

            ep_match = re.search(r'(?:第|Episode)\s*(\d+)\s*(?:集|Chapter)', line, re.IGNORECASE)
            if ep_match:
                parsed_data.append([f"第{ep_match.group(1)}集", "", "", ""])
                continue

            if re.match(r'^[-:,\s]+$', line):
                continue

            if any(kw in line for kw in ["镜号", "场景", "画面", "台词", "Shot", "Scene", "Visual", "Dialogue"]):
                if not any(char.isdigit() for char in line[:10]):
                    continue

            parts = []
            row_io = io.StringIO(line)
            try:
                reader = csv.reader(row_io)
                parts = next(reader)
            except:
                parts = [p.strip() for p in line.split(',')]

            while parts and not str(parts[0]).strip(): parts.pop(0)
            while parts and not str(parts[-1]).strip(): parts.pop()

            if not parts:
                rejected_count += 1
                continue

            first_col = str(parts[0]).strip()
            shot_num_match = re.search(r'\d+', first_col)
            non_empty_parts = [p for p in parts if p.strip()]

            if shot_num_match or len(non_empty_parts) >= 3:
                clean_shot = shot_num_match.group(0) if shot_num_match else first_col
                row_data = [""] * 4
                row_data[0] = clean_shot
                for i in range(1, min(len(parts), 4)):
                    row_data[i] = str(parts[i]).strip()

                if len(parts) > 4:
                    row_data[3] = (row_data[3] + " " + " ".join(parts[4:])).strip()

                if "第" in row_data[0] and "集" in row_data[0]:
                    continue

                parsed_data.append(row_data)
            else:
                rejected_count += 1
                if rejected_count <= 5:
                    logger.warning(f"⚠️ [解析监控] 行 {idx} 被拒绝 (无数字且内容不足): {line[:50]}...")

        if not parsed_data:
            logger.error("❌ [解析监控] 关键错误：全文遍历结束，未提取到任何有效数据行！")
            return pd.DataFrame()

        final_cols = ['镜号', '场景', '画面内容 (Visual)', '台词 (Dialogue) & 音效 (SFX)']
        df = pd.DataFrame(parsed_data, columns=final_cols)

        if not df.empty and len(df.columns) >= 4:
            def clean_dialogue_column(row):
                dialogue_col = str(row.get('台词 (Dialogue) & 音效 (SFX)', ''))
                if not dialogue_col:
                    return row

                # 🚨 终极精确清洗：仅移除中文字符（包含基本汉字区），绝不误伤全角英文标点！
                clean_dialogue = re.sub(r'[\u4e00-\u9fa5]+', '', dialogue_col).strip()
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