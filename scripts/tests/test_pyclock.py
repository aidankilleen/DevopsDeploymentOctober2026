import json

import pytest
from PyQt6.QtCore import QPoint

import pyclock


# ============================================================
# Configuration tests
# ============================================================

def test_default_config_values():
    assert pyclock.DEFAULT_CONFIG["x"] == 100
    assert pyclock.DEFAULT_CONFIG["y"] == 100
    assert pyclock.DEFAULT_CONFIG["size"] == 320
    assert pyclock.DEFAULT_CONFIG["opacity"] == 1.0
    assert pyclock.DEFAULT_CONFIG["always_on_top"] is True
    assert pyclock.DEFAULT_CONFIG["show_in_taskbar"] is True


def test_load_config_when_file_does_not_exist(
    tmp_path,
    monkeypatch
):
    config_file = tmp_path / "clock_config.json"

    monkeypatch.setattr(
        pyclock,
        "CONFIG_FILE",
        config_file
    )

    config = pyclock.load_config()

    assert config == pyclock.DEFAULT_CONFIG


def test_load_config_reads_saved_values(
    tmp_path,
    monkeypatch
):
    config_file = tmp_path / "clock_config.json"

    config_file.write_text(
        json.dumps({
            "x": 500,
            "y": 250,
            "size": 450,
            "opacity": 0.8,
            "always_on_top": False,
            "show_in_taskbar": True,
        }),
        encoding="utf-8"
    )

    monkeypatch.setattr(
        pyclock,
        "CONFIG_FILE",
        config_file
    )

    config = pyclock.load_config()

    assert config["x"] == 500
    assert config["y"] == 250
    assert config["size"] == 450
    assert config["opacity"] == 0.8
    assert config["always_on_top"] is False
    assert config["show_in_taskbar"] is True


def test_missing_config_values_use_defaults(
    tmp_path,
    monkeypatch
):
    config_file = tmp_path / "clock_config.json"

    config_file.write_text(
        json.dumps({
            "size": 600
        }),
        encoding="utf-8"
    )

    monkeypatch.setattr(
        pyclock,
        "CONFIG_FILE",
        config_file
    )

    config = pyclock.load_config()

    assert config["size"] == 600
    assert config["x"] == 100
    assert config["y"] == 100
    assert config["opacity"] == 1.0
    assert config["always_on_top"] is True
    assert config["show_in_taskbar"] is True


def test_invalid_json_uses_defaults(
    tmp_path,
    monkeypatch
):
    config_file = tmp_path / "clock_config.json"

    config_file.write_text(
        "THIS IS NOT VALID JSON",
        encoding="utf-8"
    )

    monkeypatch.setattr(
        pyclock,
        "CONFIG_FILE",
        config_file
    )

    config = pyclock.load_config()

    assert config == pyclock.DEFAULT_CONFIG


def test_non_dictionary_json_uses_defaults(
    tmp_path,
    monkeypatch
):
    config_file = tmp_path / "clock_config.json"

    config_file.write_text(
        json.dumps(["not", "a", "dictionary"]),
        encoding="utf-8"
    )

    monkeypatch.setattr(
        pyclock,
        "CONFIG_FILE",
        config_file
    )

    config = pyclock.load_config()

    assert config == pyclock.DEFAULT_CONFIG


def test_save_config(
    tmp_path,
    monkeypatch
):
    config_file = tmp_path / "clock_config.json"

    monkeypatch.setattr(
        pyclock,
        "CONFIG_FILE",
        config_file
    )

    expected = {
        "x": 400,
        "y": 200,
        "size": 500,
        "opacity": 0.7,
        "always_on_top": False,
        "show_in_taskbar": True,
    }

    pyclock.save_config(expected)

    assert config_file.exists()

    actual = json.loads(
        config_file.read_text(
            encoding="utf-8"
        )
    )

    assert actual == expected


# ============================================================
# Test fixture
# ============================================================

@pytest.fixture
def analog_clock(qtbot, tmp_path, monkeypatch):
    """
    Create a clock whose configuration is stored in pytest's
    temporary directory.

    This prevents the tests from modifying the user's real
    clock_config.json file.
    """

    config_file = tmp_path / "clock_config.json"

    monkeypatch.setattr(
        pyclock,
        "CONFIG_FILE",
        config_file
    )

    widget = pyclock.AnalogClock()
    qtbot.addWidget(widget)

    widget.show()

    yield widget

    widget.clock_timer.stop()
    widget.save_timer.stop()

    # Avoid invoking closeEvent(), because the current
    # implementation explicitly quits QApplication.
    widget.hide()


# ============================================================
# Initial state tests
# ============================================================

def test_clock_default_size(analog_clock):
    assert analog_clock.width() == 320
    assert analog_clock.height() == 320


def test_clock_has_minimum_size(analog_clock):
    assert analog_clock.minimumWidth() == 140
    assert analog_clock.minimumHeight() == 140


def test_clock_default_always_on_top(analog_clock):
    assert analog_clock.always_on_top is True


def test_clock_default_taskbar_setting(analog_clock):
    assert analog_clock.show_in_taskbar is True


def test_clock_is_square(analog_clock):
    assert analog_clock.width() == analog_clock.height()


def test_clock_animation_timer_is_active(analog_clock):
    assert analog_clock.clock_timer.isActive() is True


def test_save_timer_is_single_shot(analog_clock):
    assert analog_clock.save_timer.isSingleShot() is True


# ============================================================
# Size tests
# ============================================================

def test_set_clock_size(analog_clock):
    analog_clock.set_clock_size(450)

    assert analog_clock.width() == 450
    assert analog_clock.height() == 450


def test_size_cannot_go_below_minimum(analog_clock):
    analog_clock.set_clock_size(20)

    assert analog_clock.width() == 140
    assert analog_clock.height() == 140


def test_size_cannot_go_above_maximum(analog_clock):
    analog_clock.set_clock_size(5000)

    assert analog_clock.width() == 1000
    assert analog_clock.height() == 1000


def test_size_remains_square(analog_clock):
    analog_clock.set_clock_size(475)

    assert analog_clock.width() == 475
    assert analog_clock.height() == 475
    assert analog_clock.width() == analog_clock.height()


# ============================================================
# Opacity tests
# ============================================================

def test_set_opacity(analog_clock):
    analog_clock.set_opacity(70)

    assert analog_clock.windowOpacity() == pytest.approx(
        0.7,
        abs=0.02
    )


def test_opacity_has_lower_limit(analog_clock):
    analog_clock.set_opacity(1)

    assert analog_clock.windowOpacity() == pytest.approx(
        0.2,
        abs=0.02
    )


def test_opacity_has_upper_limit(analog_clock):
    analog_clock.set_opacity(200)

    assert analog_clock.windowOpacity() == pytest.approx(
        1.0,
        abs=0.02
    )


# ============================================================
# Settings toggle tests
# ============================================================

def test_toggle_always_on_top(analog_clock):
    original = analog_clock.always_on_top

    analog_clock.toggle_always_on_top()

    assert analog_clock.always_on_top is not original


def test_toggle_always_on_top_twice_restores_state(
    analog_clock
):
    original = analog_clock.always_on_top

    analog_clock.toggle_always_on_top()
    analog_clock.toggle_always_on_top()

    assert analog_clock.always_on_top == original


def test_toggle_taskbar(analog_clock):
    original = analog_clock.show_in_taskbar

    analog_clock.toggle_taskbar()

    assert analog_clock.show_in_taskbar is not original


def test_toggle_taskbar_twice_restores_state(
    analog_clock
):
    original = analog_clock.show_in_taskbar

    analog_clock.toggle_taskbar()
    analog_clock.toggle_taskbar()

    assert analog_clock.show_in_taskbar == original


# ============================================================
# Persistence tests
# ============================================================

def test_save_settings_persists_widget_state(
    analog_clock,
    tmp_path,
    monkeypatch
):
    config_file = tmp_path / "saved_config.json"

    monkeypatch.setattr(
        pyclock,
        "CONFIG_FILE",
        config_file
    )

    analog_clock.move(250, 300)
    analog_clock.resize(450, 450)
    analog_clock.setWindowOpacity(0.8)

    analog_clock.always_on_top = False
    analog_clock.show_in_taskbar = True

    analog_clock.save_settings()

    saved = json.loads(
        config_file.read_text(
            encoding="utf-8"
        )
    )

    assert saved["x"] == 250
    assert saved["y"] == 300
    assert saved["size"] == 450

    assert saved["opacity"] == pytest.approx(
        0.8,
        abs=0.02
    )

    assert saved["always_on_top"] is False
    assert saved["show_in_taskbar"] is True


def test_setting_clock_size_is_saved(
    analog_clock,
    tmp_path,
    monkeypatch
):
    config_file = tmp_path / "saved_config.json"

    monkeypatch.setattr(
        pyclock,
        "CONFIG_FILE",
        config_file
    )

    analog_clock.set_clock_size(600)

    saved = json.loads(
        config_file.read_text(
            encoding="utf-8"
        )
    )

    assert saved["size"] == 600


def test_setting_opacity_is_saved(
    analog_clock,
    tmp_path,
    monkeypatch
):
    config_file = tmp_path / "saved_config.json"

    monkeypatch.setattr(
        pyclock,
        "CONFIG_FILE",
        config_file
    )

    analog_clock.set_opacity(80)

    saved = json.loads(
        config_file.read_text(
            encoding="utf-8"
        )
    )

    assert saved["opacity"] == pytest.approx(
        0.8,
        abs=0.02
    )


def test_clock_restores_saved_configuration(
    qtbot,
    tmp_path,
    monkeypatch
):
    config_file = tmp_path / "clock_config.json"

    saved = {
        "x": 200,
        "y": 150,
        "size": 500,
        "opacity": 0.8,
        "always_on_top": False,
        "show_in_taskbar": True,
    }

    config_file.write_text(
        json.dumps(saved),
        encoding="utf-8"
    )

    monkeypatch.setattr(
        pyclock,
        "CONFIG_FILE",
        config_file
    )

    widget = pyclock.AnalogClock()
    qtbot.addWidget(widget)

    assert widget.x() == 200
    assert widget.y() == 150
    assert widget.width() == 500
    assert widget.height() == 500

    assert widget.windowOpacity() == pytest.approx(
        0.8,
        abs=0.02
    )

    assert widget.always_on_top is False
    assert widget.show_in_taskbar is True

    widget.clock_timer.stop()
    widget.save_timer.stop()
    widget.hide()


def test_invalid_saved_size_uses_fallback(
    qtbot,
    tmp_path,
    monkeypatch
):
    config_file = tmp_path / "clock_config.json"

    config_file.write_text(
        json.dumps({
            "size": "not-a-number"
        }),
        encoding="utf-8"
    )

    monkeypatch.setattr(
        pyclock,
        "CONFIG_FILE",
        config_file
    )

    widget = pyclock.AnalogClock()
    qtbot.addWidget(widget)

    assert widget.width() == 320
    assert widget.height() == 320

    widget.clock_timer.stop()
    widget.save_timer.stop()
    widget.hide()


def test_saved_size_is_limited_to_maximum(
    qtbot,
    tmp_path,
    monkeypatch
):
    config_file = tmp_path / "clock_config.json"

    config_file.write_text(
        json.dumps({
            "size": 5000
        }),
        encoding="utf-8"
    )

    monkeypatch.setattr(
        pyclock,
        "CONFIG_FILE",
        config_file
    )

    widget = pyclock.AnalogClock()
    qtbot.addWidget(widget)

    assert widget.width() == 1000
    assert widget.height() == 1000

    widget.clock_timer.stop()
    widget.save_timer.stop()
    widget.hide()


# ============================================================
# Edge and resize detection tests
# ============================================================

def test_centre_is_not_resize_area(analog_clock):
    centre = analog_clock.rect().center()

    assert analog_clock.is_near_edge(centre) is False


def test_outer_edge_is_resize_area(analog_clock):
    position = QPoint(
        analog_clock.width() - 2,
        analog_clock.height() // 2
    )

    assert analog_clock.is_near_edge(position) is True


def test_position_outside_clock_is_not_resize_area(
    analog_clock
):
    position = QPoint(
        analog_clock.width() + 100,
        analog_clock.height() + 100
    )

    assert analog_clock.is_near_edge(position) is False

# ============================================================
# Theme tests
# ============================================================

def test_default_theme_is_midnight():
    assert pyclock.DEFAULT_CONFIG["theme"] == "midnight"


def test_load_missing_theme_uses_default(
    tmp_path,
    monkeypatch
):
    themes_dir = tmp_path / "themes"

    monkeypatch.setattr(
        pyclock,
        "THEMES_DIR",
        themes_dir
    )

    theme = pyclock.load_theme(
        "does_not_exist"
    )

    assert theme == pyclock.DEFAULT_THEME


def test_load_custom_theme(
    tmp_path,
    monkeypatch
):
    themes_dir = tmp_path / "themes"
    themes_dir.mkdir()

    theme_file = themes_dir / "test_theme.json"

    theme_file.write_text(
        json.dumps({
            "name": "Test Theme",
            "face": "#123456",
            "second_hand": "#ABCDEF"
        }),
        encoding="utf-8"
    )

    monkeypatch.setattr(
        pyclock,
        "THEMES_DIR",
        themes_dir
    )

    theme = pyclock.load_theme(
        "test_theme"
    )

    assert theme["name"] == "Test Theme"
    assert theme["face"] == "#123456"
    assert theme["second_hand"] == "#ABCDEF"

    # Unspecified properties should inherit defaults.
    assert (
        theme["hour_hand"]
        == pyclock.DEFAULT_THEME["hour_hand"]
    )


def test_available_themes(
    tmp_path,
    monkeypatch
):
    themes_dir = tmp_path / "themes"
    themes_dir.mkdir()

    (themes_dir / "one.json").write_text(
        json.dumps({
            "name": "Theme One"
        }),
        encoding="utf-8"
    )

    (themes_dir / "two.json").write_text(
        json.dumps({
            "name": "Theme Two"
        }),
        encoding="utf-8"
    )

    monkeypatch.setattr(
        pyclock,
        "THEMES_DIR",
        themes_dir
    )

    themes = pyclock.available_themes()

    assert ("one", "Theme One") in themes
    assert ("two", "Theme Two") in themes


def test_invalid_theme_file_is_ignored(
    tmp_path,
    monkeypatch
):
    themes_dir = tmp_path / "themes"
    themes_dir.mkdir()

    (themes_dir / "broken.json").write_text(
        "NOT JSON",
        encoding="utf-8"
    )

    monkeypatch.setattr(
        pyclock,
        "THEMES_DIR",
        themes_dir
    )

    themes = pyclock.available_themes()

    assert themes == []


def test_set_theme(
    analog_clock,
    tmp_path,
    monkeypatch
):
    themes_dir = tmp_path / "themes"
    themes_dir.mkdir()

    config_file = tmp_path / "clock_config.json"

    (themes_dir / "blue.json").write_text(
        json.dumps({
            "name": "Blue",
            "face": "#0000FF"
        }),
        encoding="utf-8"
    )

    monkeypatch.setattr(
        pyclock,
        "THEMES_DIR",
        themes_dir
    )

    monkeypatch.setattr(
        pyclock,
        "CONFIG_FILE",
        config_file
    )

    analog_clock.set_theme("blue")

    assert analog_clock.theme_name == "blue"
    assert analog_clock.theme["face"] == "#0000FF"

    saved = json.loads(
        config_file.read_text(
            encoding="utf-8"
        )
    )

    assert saved["theme"] == "blue"    