UV = uv run --native-tls
DATE ?= $(shell TZ=America/New_York date +%F)
OUT ?= $(CURDIR)/out

.PHONY: setup demo episode mcp-http render studio test contracts

setup:
	uv sync --native-tls --all-packages
	cd services/studio && npm install
	$(UV) newsroom-voice setup
	ollama pull qwen2.5:14b
	ollama pull llama3.2

demo:
	$(UV) newsroom-agents run --offline --llm mock --no-record --date $(DATE)
	$(UV) newsroom-voice build --tts silent --date $(DATE)
	$(MAKE) render DATE=$(DATE)
	$(UV) newsroom-publisher build --date $(DATE)

episode:
	$(UV) newsroom-agents run --date $(DATE)
	$(UV) newsroom-voice build --date $(DATE)
	$(MAKE) render DATE=$(DATE)
	$(UV) newsroom-publisher build --date $(DATE)

mcp-http:
	$(UV) newsroom-mcp --transport http --host 127.0.0.1 --port 8765

render:
	cd services/studio && npm run --silent render -- $(OUT)/$(DATE)

studio:
	cd services/studio && npm run studio

test:
	$(UV) pytest -q
	$(UV) ruff check packages services tests scripts
	cd services/studio && npm run typecheck

contracts:
	$(UV) python scripts/gen_contracts.py
	cd services/studio && npm run gen:types
