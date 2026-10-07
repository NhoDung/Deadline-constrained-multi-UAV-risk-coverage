"""Các script trong pipeline/ có số đầu tên (04_greedy_pure.py) nên không import
được bằng cú pháp thường. Đăng ký chúng dưới tên module không số để test import."""

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

ALIASES = {
    "pipeline.greedy_pure": "04_greedy_pure.py",
    "pipeline.validate_solution": "05_validate_solution.py",
    "pipeline.greedy_ls": "06_greedy_ls.py",
    "pipeline.rn_prepare": "07_rn_prepare.py",
}

for module_name, file_name in ALIASES.items():
    spec = importlib.util.spec_from_file_location(module_name, ROOT / "pipeline" / file_name)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
