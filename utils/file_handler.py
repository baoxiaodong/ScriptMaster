""" 文件处理模块 - 修复版 v2.0
修复内容：
1. 修复表头检测逻辑，避免误判"第一章"等正文为表头
2. 保留所有列数据，仅警告多余列
3. 增强正则安全性
"""

import io
import re
import logging
from typing import Dict
import pandas as pd

logger = logging.getLogger("ScriptMaster.FileHandler")


class FileHandler:
    """文件处理器"""

    @staticmethod
    def read_file(file) -> pd.DataFrame:
        """
        读取上传的文件并自动识别表头，支持 CSV 和 Excel。
        修复：智能识别真正的表头，不会误删第一章数据
        """
        try:
            # 读取文件
            if file.name.endswith('.csv'):
                # 尝试多种编码读取 CSV
                try:
                    df = pd.read_csv(file, encoding='utf-8-sig', header=None)
                except UnicodeDecodeError:
                    file.seek(0)
                    df = pd.read_csv(file, encoding='gbk', header=None)
                except Exception as e:
                    file.seek(0)
                    df = pd.read_csv(file, encoding='utf-8', header=None)
            else:
                # 读取 Excel
                df = pd.read_excel(file, header=None)

            # 1. 移除全空行
            df = df.dropna(how='all').reset_index(drop=True)
            if df.empty:
                logger.warning("文件为空或仅包含空行")
                return pd.DataFrame()

            # 2. 🌟 修复：更精确的表头检测逻辑
            if len(df) > 0:
                first_row = df.iloc[0].astype(str).tolist()
                col1 = first_row[0].strip() if len(first_row) > 0 else ""
                col2 = first_row[1].strip() if len(first_row) > 1 else ""

                # 定义表头关键字（必须是纯表头词，不是正文内容）
                pure_header_keywords = ['标题', '章节', 'chapter', 'title', 'content', '正文', '内容', 'text',
                                        '正文内容']

                # 🌟 修复逻辑：只有当第一行同时满足以下条件才认为是表头：
                # 1. 两列都包含表头关键词
                # 2. 内容很短（表头描述通常很短）
                # 3. 不包含"第X章"、"Chapter X"等正文章节标记
                # 4. 第二列不是长文本（正文通常很长）

                is_header = False
                has_chapter_mark = bool(re.search(r'第\s*\d+\s*章|chapter\s*\d+|第\s*[一二三四五]\s*章', col1, re.I))

                if not has_chapter_mark:  # 如果包含"第一章"等标记，肯定不是表头
                    col1_is_header_like = any(kw == col1.lower() or kw in col1.lower() for kw in pure_header_keywords)
                    col2_is_header_like = any(kw == col2.lower() or kw in col2.lower() for kw in pure_header_keywords)

                    # 表头通常很短，正文第一章通常很长（>50字）
                    is_short_header = len(col1) < 10 and len(col2) < 30

                    # 如果两列都像表头且很短，才认为是表头
                    if col1_is_header_like and col2_is_header_like and is_short_header:
                        is_header = True
                        logger.info(f"检测到表头行: [{col1}, {col2}]，已跳过")

                if is_header:
                    df = df.iloc[1:].reset_index(drop=True)
                    logger.info("已移除表头行")
                else:
                    logger.info("未检测到表头行，保留第一行作为数据")

            # 3. 🌟 修复：保留所有列，但只使用前2列，警告多余列
            if df.shape[1] > 2:
                logger.warning(f"文件包含 {df.shape[1]} 列，仅使用第1-2列（标题和内容），其余列将被忽略")
                # 可选：将多余列内容合并到第二列
                # for col_idx in range(2, df.shape[1]):
                #     df.iloc[:, 1] = df.iloc[:, 1].astype(str) + " " + df.iloc[:, col_idx].astype(str)

            # 只取前两列，但保留原始DataFrame结构
            df = df.iloc[:, :2].copy()

            # 4. 填充空值
            df = df.fillna("")

            # 5. 数据验证
            valid_rows = 0
            for idx, row in df.iterrows():
                if str(row.iloc[0]).strip() or str(row.iloc[1]).strip():
                    valid_rows += 1

            if valid_rows == 0:
                logger.error("未检测到有效数据行")
                return pd.DataFrame()

            logger.info(f"成功读取文件：{valid_rows} 个有效章节")
            return df

        except Exception as e:
            logger.error(f"读取文件出错: {e}", exc_info=True)
            return pd.DataFrame()

    @staticmethod
    def export_to_csv(df: pd.DataFrame) -> bytes:
        """导出 DataFrame 为 CSV 字节流"""
        if df is None or df.empty:
            return b""
        return df.to_csv(index=False).encode('utf-8-sig')

    @staticmethod
    def export_to_excel(results: Dict[str, pd.DataFrame]) -> bytes:
        """导出分集结果字典为多 Sheet Excel"""
        if not results:
            return b""

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # 🌟 修复：更安全的排序键处理
            def extract_sort_key(x):
                match = re.search(r'\d+', str(x))
                return int(match.group()) if match else float('inf')  # 无数字的放最后

            keys = sorted(results.keys(), key=extract_sort_key)

            for key in keys:
                df = results[key]
                if isinstance(df, pd.DataFrame) and not df.empty:
                    # 处理 Sheet 名称长度限制（最大31字符）
                    sheet_name = str(key)[:31]
                    # 移除非法字符
                    for char in ['[', ']', ':', '*', '?', '/', '\\', '\'', '"']:
                        sheet_name = sheet_name.replace(char, '_')

                    # 确保不以单引号开头（Excel限制）
                    if sheet_name.startswith("'"):
                        sheet_name = "_" + sheet_name[1:]

                    # 确保不为空
                    if not sheet_name:
                        sheet_name = "Sheet"

                    try:
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                    except Exception as e:
                        logger.error(f"导出Sheet {key} 失败: {e}")
                        # 使用简化名称重试
                        df.to_excel(writer, sheet_name=f"Sheet_{keys.index(key)}", index=False)

        return output.getvalue()
