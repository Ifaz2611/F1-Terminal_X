"""Ensure README examples imports don't raise."""

def test_readme_io_import():
    from f1_terminal.io import load_session_data

    assert callable(load_session_data)


def test_readme_transform_import():
    from f1_terminal.transform import prepare_telemetry_trace

    assert callable(prepare_telemetry_trace)


def test_readme_features_import():
    from f1_terminal.features import engineer_lap_features

    assert callable(engineer_lap_features)


def test_core_reexports():
    from f1_terminal.core import engineer_lap_features, load_session_data, prepare_telemetry_trace

    assert callable(load_session_data)
    assert callable(prepare_telemetry_trace)
    assert callable(engineer_lap_features)


def test_config_import():
    from f1_terminal.config import get_logger, settings

    assert settings.min_year == 2018
    assert settings.max_year == 2030
    logger = get_logger("test")
    assert logger is not None
