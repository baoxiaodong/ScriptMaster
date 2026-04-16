""" 文件处理模块 """
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
        """读取上传的文件并自动识别表头，支持 CSV 和 Excel。"""
        try:
            if file.name.endswith('.csv'):
                try:
                    df = pd.read_csv(file, encoding='utf-8-sig', header=None)
                except UnicodeDecodeError:
                    file.seek(0)
                    df = pd.read_csv(file, encoding='gbk', header=None)
                except Exception as e:
                    file.seek(0)
                    df = pd.read_csv(file, encoding='utf-8', header=None)
            else:
                df = pd.read_excel(file, header=None)

            df = df.dropna(how='all').reset_index(drop=True)
            if df.empty:
                return pd.DataFrame()

            if len(df) > 0:
                first_row = df.iloc[0].astype(str).tolist()
                col1 = first_row[0].strip() if len(first_row) > 0 else ""
                col2 = first_row[1].strip() if len(first_row) > 1 else ""

                pure_header_keywords =  ['标题', '章节', 'chapter', 'title', 'content', '正文', '内容', 'text']
                is_header = False
                has_chapter_mark = bool(re.search(r'第\s*\d+\s*章|chapter\s*\d+|第\s*[一二三四五]\s*章', col1, re.I))

                if not has_chapter_mark:
                    col1_is_header_like = any(kw == col1.lower() or kw in col1.lower() for kw in pure_header_keywords)
                    col2_is_header_like = any(kw == col2.lower() or kw in col2.lower() for kw in pure_header_keywords)
                    is_short_header = len(col1) < 10 and len(col2) < 30

                    if col1_is_header_like and col2_is_header_like and is_short_header:
                        is_header = True

                if is_header:
                    df = df.iloc[1:].reset_index(drop=True)

            df = df.iloc[:, :2].copy()
            df = df.fillna("")
            return df
        except Exception as e:
            logger.error(f"读取文件出错: {e}", exc_info=True)
            return pd.DataFrame()

    @staticmethod
    def export_to_csv(df: pd.DataFrame) -> bytes:
        if df is None or df.empty:
            return b""
        return df.to_csv(index=False).encode('utf-8-sig')

    @staticmethod
    def export_to_excel(results: Dict[str, pd.DataFrame]) -> bytes:
        if not results:
            return b""
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            def extract_sort_key(x):
                match = re.search(r'\d+', str(x))
                return int(match.group()) if match else float('inf')

            keys = sorted(results.keys(), key=extract_sort_key)
            for key in keys:
                df = results[key]
                if isinstance(df, pd.DataFrame) and not df.empty:
                    sheet_name = str(key)[:31]
                    for char in ['[', ']', ':', '*', '?', '/', '\\', '\'', '"']:
                        sheet_name = sheet_name.replace(char, '_')
                    if sheet_name.startswith("'"):
                        sheet_name = "_" + sheet_name[1:]
                    if not sheet_name:
                        sheet_name = "Sheet"
                    try:
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                    except Exception:
                        df.to_excel(writer, sheet_name=f"Sheet_{keys.index(key)}", index=False)
        return output.getvalue()