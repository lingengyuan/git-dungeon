# Git Dungeon Makefile
# 简化开发、测试、发布流程

.PHONY: help test test-unit test-functional test-all test-golden test-golden-update run lint format clean test-m6 ai-cache-clear bench perf-smoke build-wheel smoke-install

# 默认帮助
help:
	@echo "Git Dungeon - 开发命令"
	@echo ""
	@echo "运行命令:"
	@echo "  make run          - 运行游戏"
	@echo "  make test         - 单元测试 (快速)"
	@echo "  make test-func    - 功能测试 (门禁同款，包含 M6)"
	@echo "  make test-m6      - M6 AI 模块测试"
	@echo "  make test-all     - 全部测试"
	@echo "  make test-golden  - 运行 golden tests"
	@echo "  make test-golden-update - 更新 golden 快照"
	@echo "  make bench        - 运行性能基线 benchmark"
	@echo "  make perf-smoke   - 小数据集性能烟雾检测"
	@echo "  make build-wheel  - 构建 wheel 包"
	@echo "  make smoke-install - wheel 安装烟雾测试"
	@echo ""
	@echo "AI/Cache 命令:"
	@echo "  make test-m6              - 运行 M6 AI 测试"
	@echo "  make ai-cache-clear      - 清理 AI 缓存"
	@echo ""
	@echo "开发命令:"
	@echo "  make lint         - 代码检查"
	@echo "  make format       - 代码格式化"
	@echo "  make clean        - 清理缓存"

# 运行游戏
run:
	python -m git_dungeon .

# 单元测试 (快速本地检查)
test:
	PYTHONPATH=src python3 -m pytest tests/ \
		-m "not functional and not golden and not slow" \
		-v --tb=short -q

# 功能测试 (PR/Merge 门禁同款)
test-func:
	PYTHONPATH=src python3 -m pytest tests/functional/ \
		-v --tb=short

# Golden tests (确定性测试)
test-golden:
	PYTHONPATH=src python3 -m pytest tests/golden_test.py \
		-v --tb=short

# 更新 golden 快照 (谨慎使用，需说明原因)
test-golden-update:
	PYTHONPATH=src python3 -m pytest tests/golden_test.py \
		--update-golden -v

# 全部测试
test-all:
	PYTHONPATH=src python3 -m pytest tests/ \
		-v --tb=short

# 代码检查
lint:
	PYTHONPATH=src python3 -m ruff check src/ tests/
	PYTHONPATH=src python3 -m mypy src/ --ignore-missing-imports

# 代码格式化
format:
	PYTHONPATH=src python3 -m ruff format src/ tests/
	PYTHONPATH=src python3 -m black src/ tests/

# 清理
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".venv" -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleaned cache files"

# M6 AI 测试
test-m6:
	PYTHONPATH=src python3 -m pytest tests/functional/test_m6_ai_text_func.py \
		-v --tb=short
	@echo ""
	@echo "✅ M6 tests passed - Remember to run: make test-func"

# 清理 AI 缓存
ai-cache-clear:
	@if [ -d ".git_dungeon_cache" ]; then \
		rm -rf .git_dungeon_cache/ai_text.sqlite; \
		echo "✅ AI cache cleared"; \
	else \
		echo "No AI cache found"; \
	fi

# 运行性能基线（small + medium + large）
bench:
	PYTHONPATH=src python3 -m benchmarks.run --dataset all --iterations 3 \
		--output-json benchmarks/output/benchmark_results.json

# 小数据集性能烟雾检测（默认不硬失败）
perf-smoke:
	PYTHONPATH=src python3 -m benchmarks.run --dataset small --iterations 2 \
		--output-json benchmarks/output/perf_smoke.json --perf-smoke

build-wheel:
	python3 -m pip install --upgrade pip
	python3 -m pip install build
	python3 -m build --wheel

smoke-install: build-wheel
	python3 -m venv .venv-smoke
	.venv-smoke/bin/python -m pip install --upgrade pip
	.venv-smoke/bin/pip install dist/*.whl
	bash scripts/ci_smoke_demo.sh .venv-smoke/bin/git-dungeon

# 安装开发依赖
dev-install:
	pip install -e ".[dev]"
	pip install ruff mypy black pytest pytest-asyncio

# 安装预提交 hook
pre-commit-install:
	pre-commit install
