PY = cd newsroom && uv run
DATE ?= $(shell TZ=America/New_York date +%F)

.PHONY: setup demo episode render studio test

setup:
	cd newsroom && uv sync
	cd studio && npm install
	$(PY) newsroom setup
	ollama pull qwen2.5:14b

demo:
	$(PY) newsroom run --offline --llm mock --tts silent --date $(DATE) --render

episode:
	$(PY) newsroom run --date $(DATE) --render

render:
	$(PY) newsroom render --date $(DATE)

studio:
	cd studio && npm run studio

test:
	$(PY) pytest -q
	$(PY) ruff check src tests
	cd studio && npm run typecheck
