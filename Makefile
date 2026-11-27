UV = uv run --native-tls
DATE ?= $(shell TZ=America/New_York date +%F)
OUT ?= $(CURDIR)/out
SITE_DAYS ?= $(shell python3 -c "from datetime import date, timedelta as t; print(*[(date.today() - t(n)).isoformat() for n in (3, 2, 1)])")
SITE_WEEKS ?= $(shell python3 -c "from datetime import date, timedelta as t; print(*[(date.today() - t(weeks=n)).strftime('%G-W%V') for n in (1, 0)])")

.PHONY: setup demo episode mcp-http api site-data render studio web site test contracts

setup:
	uv sync --native-tls --all-packages
	npm install
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

api:
	$(UV) newsroom-api

site-data:
	for d in $(SITE_DAYS); do \
		$(UV) newsroom-agents run --offline --llm mock --no-record --date $$d && \
		$(UV) newsroom-voice build --tts silent --date $$d && \
		$(UV) newsroom-publisher build --date $$d || exit 1; \
	done
	for w in $(SITE_WEEKS); do \
		$(UV) newsroom-agents weekly --offline --llm mock --no-record --week $$w || exit 1; \
	done

render:
	cd services/studio && npm run --silent render -- $(OUT)/$(DATE)

studio:
	cd services/studio && npm run studio

web:
	npm run dev -w @newsroom/web

site:
	@echo "Run in two terminals:"
	@echo "  make api    (NEWSROOM_OFFLINE=1 make api for sample data)"
	@echo "  make web    (http://localhost:3000)"

test:
	$(UV) pytest -q
	$(UV) ruff check packages services tests scripts
	npm run typecheck -w newsroom-studio
	npm run typecheck -w @newsroom/web
	npm run build -w @newsroom/web

contracts:
	$(UV) python scripts/gen_contracts.py
	npm run gen:types -w newsroom-studio
	npm run gen:types -w @newsroom/web
