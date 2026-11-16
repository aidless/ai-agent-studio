.PHONY: check eval

# Offline gate. No API key and no embedding-model download.
# `run_cases.py --selftest` exits 0 only when the harness goes red.
# A selftest that stays green exits 3.
check:
	python3 eval/negative_retrieval.py --check
	python3 eval/run_cases.py
	python3 eval/run_cases.py --selftest
	python3 -m pytest -q

eval: check
