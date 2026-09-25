"""Cache hygiene: import should not create nested f1_cache outside cache/."""

from pathlib import Path


def test_import_does_not_create_nested_cache(tmp_path, monkeypatch):
    # Ensure project root cache logic is not cwd-dependent
    # We check that importing the visualizer does not create stray dirs

    # Record existing cache dirs before import
    project_root = Path(__file__).parent.parent
    project_root / "cache"
    f1_cache_legacy = project_root / "f1_cache"
    nested = project_root / "f1_terminal" / "f1_cache"

    # Remove legacy if exists for test isolation (don't delete real cache, just check)
    # We simply assert import doesn't CREATE them if they don't exist
    had_legacy = f1_cache_legacy.exists()
    had_nested = nested.exists()

    # Import (should not trigger network or stray cache creation)
    import f1_terminal.f1_advanced_visualizer  # noqa: F401

    # Unified cache may exist (allowed), but nested/legacy should not be newly created
    if not had_legacy:
        assert not f1_cache_legacy.exists(), "Import created stray f1_cache/ at root"
    if not had_nested:
        assert not nested.exists(), "Import created stray f1_terminal/f1_cache/"


def test_config_cache_dir_is_unified():
    from f1_terminal.config import settings

    # Should resolve to <project>/cache
    assert settings.cache_dir.name == "cache"
    assert settings.cache_dir.is_absolute()
    # Parent should be project root (contains pyproject.toml)
    assert (settings.cache_dir.parent / "pyproject.toml").exists()
