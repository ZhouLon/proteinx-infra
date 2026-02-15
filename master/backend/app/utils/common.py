"""
通用工具函数
"""
import unicodedata

def normalize_name(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "")
    s = s.strip()
    s = " ".join(s.split())
    return s
