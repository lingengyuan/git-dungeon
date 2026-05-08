"""Phase 14B tests for generated pixel asset pipeline."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
ASSET_PLAN = ROOT / "assets/generated/phase14b/asset_plan.json"
MANIFEST = ROOT / "assets/manifest_sprites.json"


def test_phase14b_asset_plan_has_complete_generation_chain() -> None:
    plan = json.loads(ASSET_PLAN.read_text(encoding="utf-8"))

    assert plan["source"] == "codex_builtin_gpt_image_2"
    assert Path(ROOT / plan["prompt_file"]).is_file()
    assert Path(ROOT / plan["raw_file"]).is_file()
    assert Path(ROOT / plan["contact_sheet"]).is_file()
    assert len(plan["assets"]) == 15

    ids = [asset["id"] for asset in plan["assets"]]
    assert len(ids) == len(set(ids))


def test_phase14b_processed_assets_match_declared_sizes() -> None:
    plan = json.loads(ASSET_PLAN.read_text(encoding="utf-8"))

    for asset in plan["assets"]:
        path = ROOT / "assets/generated/processed" / plan["phase"] / f"{asset['id']}.png"
        with Image.open(path) as image:
            assert image.mode == "RGBA"
            assert image.size == tuple(asset["size"])


def test_phase14b_assets_are_declared_in_runtime_manifest() -> None:
    plan = json.loads(ASSET_PLAN.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    source_roots = {source["root"] for source in manifest["sources"]}
    assert f"assets/generated/processed/{plan['phase']}" in source_roots
    for asset in plan["assets"]:
        expected = f"assets/generated/processed/{plan['phase']}/{asset['id']}.png"
        assert manifest["sprites"][asset["id"]] == expected


def test_phase14b_verifier_accepts_generated_assets() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/verify_pixel_assets.py",
            "--asset-cards",
            "assets/generated/phase14b/asset_plan.json",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
