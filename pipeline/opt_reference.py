"""Bảng OPT tham khảo — mục 3 project-brief.md (Ohlsson, Peterson & Söderberg 1999, bảng C2).

Đã tự xác nhận lại bằng ILP (xem data/results/ilp/*_setcover.json): tất cả
45 instance đều giải optimal và khớp bảng này.
"""

OPT_REFERENCE = {}
_OPT_TABLE = {
    "scp4": [429, 512, 516, 494, 512, 560, 430, 492, 641, 514],
    "scp5": [253, 302, 226, 242, 211, 213, 293, 288, 279, 265],
    "scp6": [138, 146, 145, 131, 161],
    "scpa": [253, 252, 232, 234, 236],
    "scpb": [69, 76, 80, 79, 72],
    "scpc": [227, 219, 243, 219, 215],
    "scpd": [60, 66, 72, 62, 61],
}
for _prefix, _values in _OPT_TABLE.items():
    for _idx, _value in enumerate(_values, start=1):
        OPT_REFERENCE[f"{_prefix}{_idx}"] = _value
