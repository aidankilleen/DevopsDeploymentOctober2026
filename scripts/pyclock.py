import sys
import math
import json
import os
from pathlib import Path
from datetime import datetime

from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import (
    QColor,
    QPainter,
    QPen,
    QBrush,
    QFont,
    QAction,
    QActionGroup,
    QIcon,
    QPixmap,
)
from PyQt6.QtWidgets import QApplication, QWidget, QMenu


BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "clock_config.json"
THEMES_DIR = BASE_DIR / "themes"
ICON_FILE = BASE_DIR / "pyclock.ico"

DEFAULT_CONFIG = {
    "x": 100,
    "y": 100,
    "size": 320,
    "opacity": 1.0,
    "always_on_top": True,
    "show_in_taskbar": True,
    "theme": "midnight",
    "animated_taskbar_icon": True,
}

DEFAULT_THEME = {
    "name": "Midnight",
    "face": "#191B1F",
    "face_alpha": 245,
    "outer_shadow": "#000000",
    "outer_shadow_alpha": 100,
    "border": "#6E737D",
    "hour_markers": "#EBEBF0",
    "minute_markers": "#787D87",
    "numbers": "#E1E1E6",
    "hour_hand": "#F0F0F5",
    "minute_hand": "#DCE1EB",
    "second_hand": "#FF4B4B",
    "centre_outer": "#FF4B4B",
    "centre_inner": "#EBEBF0",
    "font": "Segoe UI",
}


def load_config():
    config = DEFAULT_CONFIG.copy()
    if not CONFIG_FILE.exists():
        return config
    try:
        with CONFIG_FILE.open("r", encoding="utf-8") as file:
            saved = json.load(file)
        if isinstance(saved, dict):
            config.update(saved)
    except (OSError, json.JSONDecodeError) as error:
        print(f"Could not read configuration: {error}")
    return config


def save_config(config):
    try:
        with CONFIG_FILE.open("w", encoding="utf-8") as file:
            json.dump(config, file, indent=4)
    except OSError as error:
        print(f"Could not save configuration: {error}")


def colour(value, alpha=255):
    result = QColor(value)
    if not result.isValid():
        result = QColor("#FFFFFF")
    result.setAlpha(max(0, min(int(alpha), 255)))
    return result


def load_theme(theme_name):
    theme = DEFAULT_THEME.copy()
    theme_file = THEMES_DIR / f"{theme_name}.json"
    if not theme_file.exists():
        return theme
    try:
        with theme_file.open("r", encoding="utf-8") as file:
            saved = json.load(file)
        if isinstance(saved, dict):
            theme.update(saved)
    except (OSError, json.JSONDecodeError) as error:
        print(f"Could not load theme '{theme_name}': {error}")
    return theme


def available_themes():
    themes = []
    if not THEMES_DIR.exists():
        return themes
    for theme_file in sorted(THEMES_DIR.glob("*.json")):
        try:
            with theme_file.open("r", encoding="utf-8") as file:
                data = json.load(file)
            if not isinstance(data, dict):
                continue
            theme_id = theme_file.stem
            display_name = data.get("name", theme_id.replace("_", " ").title())
            themes.append((theme_id, display_name))
        except (OSError, json.JSONDecodeError):
            print(f"Ignoring invalid theme: {theme_file.name}")
    return themes


class AnalogClock(QWidget):
    MINIMUM_CLOCK_SIZE = 140
    MAXIMUM_CLOCK_SIZE = 1000
    RESIZE_MARGIN = 18

    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.drag_position = QPoint()
        self.resizing = False
        self.resize_start_position = QPoint()
        self.resize_start_size = 0
        self.resize_direction = (1, 1)

        self.always_on_top = bool(self.config.get("always_on_top", True))
        self.show_in_taskbar = bool(self.config.get("show_in_taskbar", True))
        self.theme_name = str(self.config.get("theme", "midnight"))
        self.animated_taskbar_icon = bool(
            self.config.get("animated_taskbar_icon", True)
        )
        self.theme = load_theme(self.theme_name)

        self.setWindowTitle("Analogue Clock")
        self.apply_window_flags()
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self.setMinimumSize(self.MINIMUM_CLOCK_SIZE, self.MINIMUM_CLOCK_SIZE)

        try:
            size = int(self.config.get("size", 320))
        except (TypeError, ValueError):
            size = 320
        size = max(self.MINIMUM_CLOCK_SIZE, min(size, self.MAXIMUM_CLOCK_SIZE))
        self.resize(size, size)

        try:
            x = int(self.config.get("x", 100))
            y = int(self.config.get("y", 100))
        except (TypeError, ValueError):
            x, y = 100, 100
        self.move(x, y)

        try:
            opacity = float(self.config.get("opacity", 1.0))
        except (TypeError, ValueError):
            opacity = 1.0
        self.setWindowOpacity(max(0.2, min(opacity, 1.0)))

        self.save_timer = QTimer(self)
        self.save_timer.setSingleShot(True)
        self.save_timer.timeout.connect(self.save_settings)

        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.update)
        self.clock_timer.start(16)

        self.icon_timer = QTimer(self)
        self.icon_timer.timeout.connect(self.update_taskbar_icon)
        self.icon_timer.start(1000)
        self.update_taskbar_icon()

    def apply_window_flags(self):
        if self.show_in_taskbar:
            flags = Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint
        else:
            flags = Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint
        if self.always_on_top:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)

    def reapply_window_flags(self):
        geometry = self.geometry()
        self.apply_window_flags()
        self.setGeometry(geometry)
        self.show()
        self.raise_()
        self.activateWindow()
        self.update_taskbar_icon()

    def schedule_save(self):
        self.save_timer.start(400)

    def save_settings(self):
        self.config = {
            "x": self.x(),
            "y": self.y(),
            "size": self.width(),
            "opacity": round(self.windowOpacity(), 2),
            "always_on_top": self.always_on_top,
            "show_in_taskbar": self.show_in_taskbar,
            "theme": self.theme_name,
            "animated_taskbar_icon": self.animated_taskbar_icon,
        }
        save_config(self.config)

    def set_theme(self, theme_name):
        self.theme_name = theme_name
        self.theme = load_theme(theme_name)
        self.update()
        self.update_taskbar_icon()
        self.save_settings()

    def create_live_icon(self, icon_size=64):
        pixmap = QPixmap(icon_size, icon_size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        centre = icon_size / 2
        radius = icon_size * 0.45
        painter.setPen(QPen(colour(self.theme["border"]), max(1, icon_size // 32)))
        painter.setBrush(QBrush(colour(self.theme["face"], 255)))
        painter.drawEllipse(
            int(centre - radius), int(centre - radius),
            int(radius * 2), int(radius * 2)
        )

        for index in range(12):
            angle = math.radians(index * 30 - 90)
            outer = radius * 0.86
            inner = radius * 0.72
            painter.setPen(QPen(
                colour(self.theme["hour_markers"]),
                max(1, icon_size // 32),
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
            ))
            painter.drawLine(
                int(centre + math.cos(angle) * inner),
                int(centre + math.sin(angle) * inner),
                int(centre + math.cos(angle) * outer),
                int(centre + math.sin(angle) * outer),
            )

        now = datetime.now()
        seconds = now.second + now.microsecond / 1_000_000
        minutes = now.minute + seconds / 60
        hours = (now.hour % 12) + minutes / 60

        def draw_icon_hand(angle_degrees, length, width, hand_colour):
            angle = math.radians(angle_degrees - 90)
            painter.setPen(QPen(
                colour(hand_colour), width,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
            ))
            painter.drawLine(
                int(centre), int(centre),
                int(centre + math.cos(angle) * length),
                int(centre + math.sin(angle) * length),
            )

        draw_icon_hand(hours * 30, radius * 0.48, max(2, icon_size // 16), self.theme["hour_hand"])
        draw_icon_hand(minutes * 6, radius * 0.68, max(2, icon_size // 20), self.theme["minute_hand"])
        draw_icon_hand(seconds * 6, radius * 0.76, max(1, icon_size // 32), self.theme["second_hand"])

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(colour(self.theme["centre_outer"]))
        pin = max(4, icon_size // 10)
        painter.drawEllipse(
            int(centre - pin / 2), int(centre - pin / 2), pin, pin
        )
        painter.end()
        return QIcon(pixmap)

    def static_icon(self):
        if ICON_FILE.exists():
            return QIcon(str(ICON_FILE))
        return self.create_live_icon()

    def update_taskbar_icon(self):
        icon = (
            self.create_live_icon()
            if self.animated_taskbar_icon
            else self.static_icon()
        )
        self.setWindowIcon(icon)
        app = QApplication.instance()
        if app is not None:
            app.setWindowIcon(icon)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        size = min(self.width(), self.height())
        painter.translate(self.width() / 2, self.height() / 2)
        painter.scale(size / 320.0, size / 320.0)
        self.draw_face(painter)
        self.draw_numbers(painter)
        self.draw_hands(painter)
        self.draw_centre(painter)

    def draw_face(self, painter):
        radius = 145
        painter.setPen(QPen(colour(
            self.theme["outer_shadow"],
            self.theme.get("outer_shadow_alpha", 100)
        ), 8))
        painter.setBrush(QBrush(colour(
            self.theme["face"], self.theme.get("face_alpha", 245)
        )))
        painter.drawEllipse(-radius, -radius, radius * 2, radius * 2)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(colour(self.theme["border"]), 2))
        painter.drawEllipse(-radius + 3, -radius + 3, (radius - 3) * 2, (radius - 3) * 2)

        for index in range(60):
            painter.save()
            painter.rotate(index * 6)
            if index % 5 == 0:
                painter.setPen(QPen(
                    colour(self.theme["hour_markers"]), 3,
                    Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap
                ))
                painter.drawLine(0, -130, 0, -140)
            else:
                painter.setPen(QPen(colour(self.theme["minute_markers"]), 1))
                painter.drawLine(0, -134, 0, -140)
            painter.restore()

    def draw_numbers(self, painter):
        painter.setPen(colour(self.theme["numbers"]))
        font = QFont(self.theme.get("font", "Segoe UI"))
        font.setPointSize(13)
        font.setWeight(QFont.Weight.Medium)
        painter.setFont(font)
        for number in range(1, 13):
            angle = math.radians(number * 30 - 90)
            x = math.cos(angle) * 108
            y = math.sin(angle) * 108
            painter.drawText(
                int(x - 17), int(y - 14), 34, 28,
                Qt.AlignmentFlag.AlignCenter, str(number)
            )

    def draw_hands(self, painter):
        now = datetime.now()
        seconds = now.second + now.microsecond / 1_000_000
        minutes = now.minute + seconds / 60
        hours = (now.hour % 12) + minutes / 60
        self.draw_hand(painter, hours * 30, 68, 7, colour(self.theme["hour_hand"]))
        self.draw_hand(painter, minutes * 6, 100, 5, colour(self.theme["minute_hand"]))
        self.draw_hand(painter, seconds * 6, 118, 2, colour(self.theme["second_hand"]), 25)

    def draw_hand(self, painter, angle, length, width, hand_colour, tail=0):
        painter.save()
        painter.rotate(angle)
        painter.setPen(QPen(
            hand_colour, width,
            Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap
        ))
        painter.drawLine(0, tail, 0, -length)
        painter.restore()

    def draw_centre(self, painter):
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(colour(self.theme["centre_outer"]))
        painter.drawEllipse(-7, -7, 14, 14)
        painter.setBrush(colour(self.theme["centre_inner"]))
        painter.drawEllipse(-3, -3, 6, 6)

    def is_near_edge(self, position):
        centre_x = self.width() / 2
        centre_y = self.height() / 2
        distance = math.hypot(position.x() - centre_x, position.y() - centre_y)
        radius = min(self.width(), self.height()) / 2
        return radius - self.RESIZE_MARGIN <= distance <= radius + 4

    def resize_cursor_for_position(self, position):
        dx = position.x() - self.width() / 2
        dy = position.y() - self.height() / 2
        return (
            Qt.CursorShape.SizeFDiagCursor
            if dx * dy >= 0
            else Qt.CursorShape.SizeBDiagCursor
        )

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
            return
        if self.is_near_edge(event.position()):
            self.resizing = True
            self.resize_start_position = event.globalPosition().toPoint()
            self.resize_start_size = self.width()
            self.resize_direction = (
                1 if event.position().x() >= self.width() / 2 else -1,
                1 if event.position().y() >= self.height() / 2 else -1,
            )
        else:
            self.resizing = False
            self.drag_position = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
        event.accept()

    def mouseMoveEvent(self, event):
        if self.resizing and event.buttons() & Qt.MouseButton.LeftButton:
            delta = event.globalPosition().toPoint() - self.resize_start_position
            change = max(
                delta.x() * self.resize_direction[0],
                delta.y() * self.resize_direction[1],
            )
            new_size = int(self.resize_start_size + change)
            new_size = max(self.MINIMUM_CLOCK_SIZE, min(new_size, self.MAXIMUM_CLOCK_SIZE))
            self.resize(new_size, new_size)
            self.schedule_save()
            event.accept()
            return
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            self.schedule_save()
            event.accept()
            return
        self.setCursor(
            self.resize_cursor_for_position(event.position())
            if self.is_near_edge(event.position())
            else Qt.CursorShape.ArrowCursor
        )

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.resizing = False
            self.save_settings()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_always_on_top()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def contextMenuEvent(self, event):
        menu = QMenu(self)

        top_action = QAction("Always on top", self)
        top_action.setCheckable(True)
        top_action.setChecked(self.always_on_top)
        top_action.triggered.connect(self.toggle_always_on_top)
        menu.addAction(top_action)

        taskbar_action = QAction("Show in taskbar", self)
        taskbar_action.setCheckable(True)
        taskbar_action.setChecked(self.show_in_taskbar)
        taskbar_action.triggered.connect(self.toggle_taskbar)
        menu.addAction(taskbar_action)

        animated_icon_action = QAction("Animated taskbar icon", self)
        animated_icon_action.setCheckable(True)
        animated_icon_action.setChecked(self.animated_taskbar_icon)
        animated_icon_action.triggered.connect(self.toggle_animated_taskbar_icon)
        menu.addAction(animated_icon_action)
        menu.addSeparator()

        theme_menu = menu.addMenu("Theme")
        theme_group = QActionGroup(self)
        theme_group.setExclusive(True)
        themes = available_themes()
        if themes:
            for theme_id, display_name in themes:
                action = QAction(display_name, self)
                action.setCheckable(True)
                action.setChecked(theme_id == self.theme_name)
                action.triggered.connect(
                    lambda checked=False, selected=theme_id: self.set_theme(selected)
                )
                theme_group.addAction(action)
                theme_menu.addAction(action)
        else:
            action = QAction("No themes found", self)
            action.setEnabled(False)
            theme_menu.addAction(action)

        size_menu = menu.addMenu("Size")
        for name, size in {"Small": 200, "Medium": 320, "Large": 450, "Extra large": 600}.items():
            action = QAction(f"{name} ({size}px)", self)
            action.triggered.connect(
                lambda checked=False, selected=size: self.set_clock_size(selected)
            )
            size_menu.addAction(action)

        opacity_menu = menu.addMenu("Opacity")
        for percentage in (100, 90, 80, 70, 60, 50):
            action = QAction(f"{percentage}%", self)
            action.setCheckable(True)
            action.setChecked(round(self.windowOpacity() * 100) == percentage)
            action.triggered.connect(
                lambda checked=False, selected=percentage: self.set_opacity(selected)
            )
            opacity_menu.addAction(action)

        menu.addSeparator()
        themes_action = QAction("Open themes folder", self)
        themes_action.triggered.connect(self.open_themes_folder)
        menu.addAction(themes_action)

        config_action = QAction("Open configuration folder", self)
        config_action.triggered.connect(self.open_config_folder)
        menu.addAction(config_action)

        menu.addSeparator()
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        menu.addAction(exit_action)
        menu.exec(event.globalPos())

    def set_clock_size(self, size):
        size = max(self.MINIMUM_CLOCK_SIZE, min(int(size), self.MAXIMUM_CLOCK_SIZE))
        self.resize(size, size)
        self.save_settings()

    def set_opacity(self, percentage):
        self.setWindowOpacity(max(0.2, min(percentage / 100, 1.0)))
        self.save_settings()

    def toggle_always_on_top(self):
        self.always_on_top = not self.always_on_top
        self.reapply_window_flags()
        self.save_settings()

    def toggle_taskbar(self):
        self.show_in_taskbar = not self.show_in_taskbar
        self.reapply_window_flags()
        self.save_settings()

    def toggle_animated_taskbar_icon(self):
        self.animated_taskbar_icon = not self.animated_taskbar_icon
        self.update_taskbar_icon()
        self.save_settings()

    def open_config_folder(self):
        try:
            os.startfile(str(CONFIG_FILE.parent))
        except OSError as error:
            print(f"Could not open configuration folder: {error}")

    def open_themes_folder(self):
        THEMES_DIR.mkdir(parents=True, exist_ok=True)
        try:
            os.startfile(str(THEMES_DIR))
        except OSError as error:
            print(f"Could not open themes folder: {error}")

    def closeEvent(self, event):
        self.save_settings()
        self.clock_timer.stop()
        self.icon_timer.stop()
        self.save_timer.stop()
        event.accept()
        app = QApplication.instance()
        if app is not None:
            app.quit()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            event.accept()
            return
        super().keyPressEvent(event)


def set_windows_app_id():
    """Give Windows a stable taskbar identity when run as a script."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "PyClock.DesktopClock.1"
        )
    except (AttributeError, OSError):
        pass


if __name__ == "__main__":
    THEMES_DIR.mkdir(parents=True, exist_ok=True)
    set_windows_app_id()

    app = QApplication(sys.argv)
    app.setApplicationName("Desktop Analogue Clock")
    app.setApplicationDisplayName("Analogue Clock")
    app.setQuitOnLastWindowClosed(True)

    if ICON_FILE.exists():
        app.setWindowIcon(QIcon(str(ICON_FILE)))

    clock = AnalogClock()
    clock.show()
    sys.exit(app.exec())
