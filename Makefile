# --- acceptance_backfill (EVAL_ACCEPTANCE_STANDARD.md P4) ---
# 证据来源: ci.yml
# 命令逐字取自该来源，未增删任何参数。
# 归一: python → python3（本机无 python 别名，实测 Error 127）
.PHONY: eval

# 一键回归：验收题库（20 条）→ 题库自检（必须变红）→ 既有 pytest 套件。
# 三步任一非 0 即整体失败（run_cases 通过率 < 100% 返回 1；selftest 若没变红返回 3）。
eval:
	python3 eval/run_cases.py
	python3 eval/run_cases.py --selftest
	python3 -m pytest -q
