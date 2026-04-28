fmt-check:
	python -m black --check app tests

test-core:
	python -m pytest -q --ignore=tests/test_mvp_scheduler_http_flow.py

test-http-smoke:
	python -m pytest -q tests/test_mvp_scheduler_http_flow.py

ci: fmt-check test-core test-http-smoke
