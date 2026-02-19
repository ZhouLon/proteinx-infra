"""
常量定义：
- aa_map：氨基酸字符到索引的映射（含 '-' 占位）
- database_header：示例数据表头（按项目数据约定）
"""

aa_map = {
    'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4,
    'F': 5, 'G': 6, 'H': 7, 'I': 8, 'J': 9,
    'K': 10, 'L': 11, 'M': 12, 'N': 13, 'O': 14,
    'P': 15, 'Q': 16, 'R': 17, 'S': 18, 'T': 19,
    'U': 20, 'V': 21, 'W': 22, 'X': 23, 'Y': 24,
    'Z': 25, '-': 26
}

database_header=['mutant','mutated_sequence','DMS_score','DMS_score_bin']
