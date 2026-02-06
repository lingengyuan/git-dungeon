"""Unit tests for M6 CLI AI hooks and prefetch behavior."""

from __future__ import annotations

from types import SimpleNamespace

from git_dungeon.main_cli_ai import GitDungeonAICLI


def _build_chapter() -> SimpleNamespace:
    return SimpleNamespace(
        chapter_id="chapter_0",
        chapter_index=0,
        chapter_type=SimpleNamespace(value="feature"),
        name="Feature Wave",
        is_boss_chapter=False,
        config=SimpleNamespace(shop_enabled=True),
        commits=[
            SimpleNamespace(message="feat: add login"),
            SimpleNamespace(message="fix: patch token issue"),
        ],
    )


def _build_enemy() -> SimpleNamespace:
    return SimpleNamespace(
        enemy_type="feature",
        commit_message="feat: add login",
        commit_hash="abc1234",
        entity_id="enemy_0",
        current_hp=30,
        gold_reward=5,
    )


def test_ai_hooks_emit_text_in_combat(capsys):
    """Combat wrapper should emit AI lines without touching combat rules."""
    cli = GitDungeonAICLI(ai_enabled=True, ai_provider="mock", seed=7, auto_mode=True)
    cli._ensure_aggregator("test/repo")

    chapter = _build_chapter()
    enemy = _build_enemy()

    cli._base_cli.state = SimpleNamespace(
        player=SimpleNamespace(character=SimpleNamespace(current_hp=100))
    )
    cli._base_cli._print_chapter_intro = lambda _chapter: None
    cli._base_cli._open_shop = lambda _chapter: None
    cli._base_cli._boss_combat = lambda _chapter: True
    cli._base_cli._combat = lambda _enemy, _chapter: True

    cli._install_ai_hooks()
    result = cli._base_cli._combat(enemy, chapter)
    out = capsys.readouterr().out

    assert result is True
    assert "🧠" in out


def test_prefetch_chapter_runs_once_per_chapter():
    """Chapter prefetch should avoid duplicate prefetch calls."""
    cli = GitDungeonAICLI(ai_enabled=True, ai_provider="mock", seed=11)

    class DummyAggregator:
        def __init__(self) -> None:
            self.requests: list[tuple[str, str]] = []
            self.prefetch_calls = 0

        def add_request(self, kind, key, extra_context=None) -> None:
            self.requests.append((kind.value, key))

        def prefetch(self) -> dict:
            self.prefetch_calls += 1
            return {}

        def get(self, kind, key, extra_context=None) -> str:
            return ""

    chapter = _build_chapter()
    agg = DummyAggregator()
    cli.ai_aggregator = agg  # type: ignore[assignment]

    cli._prefetch_chapter(chapter)
    cli._prefetch_chapter(chapter)

    assert agg.prefetch_calls == 1
    assert any(item[0] == "enemy_intro" for item in agg.requests)
    assert any(item[0] == "event_flavor" for item in agg.requests)


def test_content_version_is_hashed():
    """Content version should not be a fixed constant."""
    cli = GitDungeonAICLI(ai_enabled=True, ai_provider="mock")
    assert cli._content_version.startswith("m6-")
    assert cli._content_version != "1.0"


def test_gemini_prefetch_auto_adjust_to_off():
    """Gemini should auto-adjust prefetch to off for free-tier safety."""
    cli = GitDungeonAICLI(ai_enabled=True, ai_provider="gemini", ai_prefetch="chapter")
    assert cli.ai_prefetch == "off"
    assert cli.ai_prefetch_auto_adjusted is True
    assert cli.ai_prefetch_requested == "chapter"


def test_non_gemini_prefetch_not_auto_adjusted():
    """Mock/OpenAI should keep requested prefetch strategy."""
    cli = GitDungeonAICLI(ai_enabled=True, ai_provider="mock", ai_prefetch="chapter")
    assert cli.ai_prefetch == "chapter"
    assert cli.ai_prefetch_auto_adjusted is False


def test_lang_alias_zh_normalized_to_zh_cn():
    """`zh` alias should map to `zh_CN` for both base CLI and AI requests."""
    cli = GitDungeonAICLI(ai_enabled=True, ai_provider="mock", lang="zh")
    assert cli.lang == "zh_CN"
    assert cli._base_cli.lang == "zh_CN"
