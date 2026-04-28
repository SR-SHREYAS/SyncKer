.PHONY: fmt-check test-core test-http-smoke ci

fmt-check:
	python -m black --check app tests

test-core:
	python -m pytest --ignore=tests/test_mvp_scheduler_http_flow.py

test-http-smoke:
	python -m pytest tests/test_mvp_scheduler_http_flow.py

ci: fmt-check test-core test-http-smoke
