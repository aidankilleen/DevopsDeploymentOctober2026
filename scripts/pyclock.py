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
)
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QMenu,
)


# ============================================================
# Configuration
# ============================================================

CONFIG_FILE = Path(__file__).with_name("clock_config.json")

DEFAULT_CONFIG = {
    "x": 100,
    "y": 100,
    "size": 320,
    "opacity": 1.0,
    "always_on_top": True,
    "show_in_taskbar": True,
}


def load_config():
    """Load settings from clock_config.json."""

    config = DEFAULT_CONFIG.copy()

    if not CONFIG_FILE.exists():
        return config

    try:
        with CONFIG_FILE.open("r", encoding="utf-8") as file:
            saved_config = json.load(file)

        if isinstance(saved_config, dict):
            config.update(saved_config)

    except (OSError, json.JSONDecodeError) as error:
        print(f"Could not read configuration: {error}")
        print("Using default settings.")

    return config


def save_config(config):
    """Write settings to clock_config.json."""

    try:
        with CONFIG_FILE.open("w", encoding="utf-8") as file:
            json.dump(config, file, indent=4)

    except OSError as error:
        print(f"Could not save configuration: {error}")


# ============================================================
# Analogue clock
# ============================================================

class AnalogClock(QWidget):

    MINIMUM_CLOCK_SIZE = 140
    MAXIMUM_CLOCK_SIZE = 1000
    RESIZE_MARGIN = 18

    def __init__(self):
        super().__init__()

        self.config = load_config()

        # Mouse interaction state
        self.drag_position = QPoint()
        self.resizing = False
        self.resize_start_position = QPoint()
        self.resize_start_size = 0
        self.resize_direction = 1

        # Persistent window settings
        self.always_on_top = bool(
            self.config.get("always_on_top", True)
        )

        self.show_in_taskbar = bool(
            self.config.get("show_in_taskbar", True)
        )

        self.setWindowTitle("Analogue Clock")

        # Apply flags before showing the window
        self.apply_window_flags()

        # Transparent area outside the circular face
        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground
        )

        # Receive mouse movement when no button is pressed
        self.setMouseTracking(True)

        self.setMinimumSize(
            self.MINIMUM_CLOCK_SIZE,
            self.MINIMUM_CLOCK_SIZE
        )

        # ----------------------------------------------------
        # Restore size
        # ----------------------------------------------------

        try:
            size = int(self.config.get("size", 320))
        except (TypeError, ValueError):
            size = 320

        size = max(
            self.MINIMUM_CLOCK_SIZE,
            min(size, self.MAXIMUM_CLOCK_SIZE)
        )

        self.resize(size, size)

        # ----------------------------------------------------
        # Restore position
        # ----------------------------------------------------

        try:
            x = int(self.config.get("x", 100))
            y = int(self.config.get("y", 100))
        except (TypeError, ValueError):
            x = 100
            y = 100

        self.move(x, y)

        # ----------------------------------------------------
        # Restore opacity
        # ----------------------------------------------------

        try:
            opacity = float(
                self.config.get("opacity", 1.0)
            )
        except (TypeError, ValueError):
            opacity = 1.0

        opacity = max(0.2, min(opacity, 1.0))
        self.setWindowOpacity(opacity)

        # ----------------------------------------------------
        # Delayed configuration saving
        # ----------------------------------------------------

        self.save_timer = QTimer(self)
        self.save_timer.setSingleShot(True)
        self.save_timer.timeout.connect(
            self.save_settings
        )

        # ----------------------------------------------------
        # Clock animation
        # ----------------------------------------------------

        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.update)

        # Roughly 60 FPS for a smooth second hand
        self.clock_timer.start(16)

    # ========================================================
    # Window flags
    # ========================================================

    def apply_window_flags(self):
        """Apply taskbar and always-on-top settings."""

        if self.show_in_taskbar:
            flags = (
                Qt.WindowType.Window
                | Qt.WindowType.FramelessWindowHint
            )
        else:
            flags = (
                Qt.WindowType.Tool
                | Qt.WindowType.FramelessWindowHint
            )

        if self.always_on_top:
            flags |= Qt.WindowType.WindowStaysOnTopHint

        self.setWindowFlags(flags)

    def reapply_window_flags(self):
        """
        Changing Qt window flags hides and recreates the native
        window, so preserve the geometry and show it again.
        """

        geometry = self.geometry()

        self.apply_window_flags()

        self.setGeometry(geometry)
        self.show()
        self.raise_()
        self.activateWindow()

    # ========================================================
    # Configuration
    # ========================================================

    def schedule_save(self):
        """
        Avoid writing the JSON file continuously while the user
        is moving or resizing the clock.
        """

        self.save_timer.start(400)

    def save_settings(self):
        """Save the current window settings."""

        self.config = {
            "x": self.x(),
            "y": self.y(),
            "size": self.width(),
            "opacity": round(self.windowOpacity(), 2),
            "always_on_top": self.always_on_top,
            "show_in_taskbar": self.show_in_taskbar,
        }

        save_config(self.config)

    # ========================================================
    # Drawing
    # ========================================================

    def paintEvent(self, event):
        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        width = self.width()
        height = self.height()
        size = min(width, height)

        painter.translate(
            width / 2,
            height / 2
        )

        # Draw against a logical 320 × 320 coordinate system
        scale = size / 320.0
        painter.scale(scale, scale)

        self.draw_face(painter)
        self.draw_numbers(painter)
        self.draw_hands(painter)
        self.draw_centre(painter)

    def draw_face(self, painter):
        radius = 145

        # Main clock face and soft outer edge
        painter.setPen(
            QPen(
                QColor(0, 0, 0, 100),
                8
            )
        )

        painter.setBrush(
            QBrush(
                QColor(25, 27, 31, 245)
            )
        )

        painter.drawEllipse(
            -radius,
            -radius,
            radius * 2,
            radius * 2
        )

        # Inner border
        painter.setBrush(
            Qt.BrushStyle.NoBrush
        )

        painter.setPen(
            QPen(
                QColor(110, 115, 125),
                2
            )
        )

        painter.drawEllipse(
            -radius + 3,
            -radius + 3,
            (radius - 3) * 2,
            (radius - 3) * 2
        )

        # Minute and hour markings
        for index in range(60):
            painter.save()
            painter.rotate(index * 6)

            if index % 5 == 0:
                painter.setPen(
                    QPen(
                        QColor(235, 235, 240),
                        3,
                        Qt.PenStyle.SolidLine,
                        Qt.PenCapStyle.RoundCap
                    )
                )

                painter.drawLine(
                    0,
                    -130,
                    0,
                    -140
                )

            else:
                painter.setPen(
                    QPen(
                        QColor(120, 125, 135),
                        1
                    )
                )

                painter.drawLine(
                    0,
                    -134,
                    0,
                    -140
                )

            painter.restore()

    def draw_numbers(self, painter):
        painter.setPen(
            QColor(225, 225, 230)
        )

        font = QFont("Segoe UI")
        font.setPointSize(13)
        font.setWeight(QFont.Weight.Medium)

        painter.setFont(font)

        number_radius = 108

        for number in range(1, 13):
            angle = math.radians(
                number * 30 - 90
            )

            x = math.cos(angle) * number_radius
            y = math.sin(angle) * number_radius

            painter.drawText(
                int(x - 17),
                int(y - 14),
                34,
                28,
                Qt.AlignmentFlag.AlignCenter,
                str(number)
            )

    def draw_hands(self, painter):
        now = datetime.now()

        seconds = (
            now.second
            + now.microsecond / 1_000_000
        )

        minutes = (
            now.minute
            + seconds / 60
        )

        hours = (
            now.hour % 12
            + minutes / 60
        )

        # Hour hand
        self.draw_hand(
            painter=painter,
            angle=hours * 30,
            length=68,
            width=7,
            colour=QColor(240, 240, 245)
        )

        # Minute hand
        self.draw_hand(
            painter=painter,
            angle=minutes * 6,
            length=100,
            width=5,
            colour=QColor(220, 225, 235)
        )

        # Second hand
        self.draw_hand(
            painter=painter,
            angle=seconds * 6,
            length=118,
            width=2,
            colour=QColor(255, 75, 75),
            tail=25
        )

    def draw_hand(
        self,
        painter,
        angle,
        length,
        width,
        colour,
        tail=0
    ):
        painter.save()
        painter.rotate(angle)

        painter.setPen(
            QPen(
                colour,
                width,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap
            )
        )

        painter.drawLine(
            0,
            tail,
            0,
            -length
        )

        painter.restore()

    def draw_centre(self, painter):
        painter.setPen(
            Qt.PenStyle.NoPen
        )

        painter.setBrush(
            QColor(255, 75, 75)
        )

        painter.drawEllipse(
            -7,
            -7,
            14,
            14
        )

        painter.setBrush(
            QColor(235, 235, 240)
        )

        painter.drawEllipse(
            -3,
            -3,
            6,
            6
        )

    # ========================================================
    # Resize detection
    # ========================================================

    def is_near_edge(self, position):
        centre_x = self.width() / 2
        centre_y = self.height() / 2

        dx = position.x() - centre_x
        dy = position.y() - centre_y

        distance = math.hypot(dx, dy)
        radius = min(self.width(), self.height()) / 2

        # Restrict resizing to a ring around the clock edge
        return (
            radius - self.RESIZE_MARGIN
            <= distance
            <= radius + 4
        )

    def resize_cursor_for_position(self, position):
        centre_x = self.width() / 2
        centre_y = self.height() / 2

        dx = position.x() - centre_x
        dy = position.y() - centre_y

        if dx * dy >= 0:
            return Qt.CursorShape.SizeFDiagCursor

        return Qt.CursorShape.SizeBDiagCursor

    # ========================================================
    # Mouse interaction
    # ========================================================

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
            return

        if self.is_near_edge(event.position()):
            self.resizing = True

            self.resize_start_position = (
                event.globalPosition().toPoint()
            )

            self.resize_start_size = self.width()

            # Determine whether outward movement should increase
            # or decrease the clock size.
            horizontal_direction = (
                1
                if event.position().x() >= self.width() / 2
                else -1
            )

            vertical_direction = (
                1
                if event.position().y() >= self.height() / 2
                else -1
            )

            self.resize_direction = (
                horizontal_direction,
                vertical_direction
            )

        else:
            self.resizing = False

            self.drag_position = (
                event.globalPosition().toPoint()
                - self.frameGeometry().topLeft()
            )

        event.accept()

    def mouseMoveEvent(self, event):
        # ----------------------------------------------------
        # Resize
        # ----------------------------------------------------

        if (
            self.resizing
            and event.buttons() & Qt.MouseButton.LeftButton
        ):
            current_position = (
                event.globalPosition().toPoint()
            )

            delta = (
                current_position
                - self.resize_start_position
            )

            horizontal_change = (
                delta.x() * self.resize_direction[0]
            )

            vertical_change = (
                delta.y() * self.resize_direction[1]
            )

            change = max(
                horizontal_change,
                vertical_change
            )

            new_size = int(
                self.resize_start_size + change
            )

            new_size = max(
                self.MINIMUM_CLOCK_SIZE,
                min(new_size, self.MAXIMUM_CLOCK_SIZE)
            )

            self.resize(new_size, new_size)
            self.schedule_save()

            event.accept()
            return

        # ----------------------------------------------------
        # Move
        # ----------------------------------------------------

        if event.buttons() & Qt.MouseButton.LeftButton:
            new_position = (
                event.globalPosition().toPoint()
                - self.drag_position
            )

            self.move(new_position)
            self.schedule_save()

            event.accept()
            return

        # ----------------------------------------------------
        # Cursor feedback
        # ----------------------------------------------------

        if self.is_near_edge(event.position()):
            self.setCursor(
                self.resize_cursor_for_position(
                    event.position()
                )
            )
        else:
            self.setCursor(
                Qt.CursorShape.ArrowCursor
            )

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.resizing = False

            # Save immediately when moving or resizing stops
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

    # ========================================================
    # Right-click menu
    # ========================================================

    def contextMenuEvent(self, event):
        menu = QMenu(self)

        # Always on top
        always_on_top_action = QAction(
            "Always on top",
            self
        )

        always_on_top_action.setCheckable(True)
        always_on_top_action.setChecked(
            self.always_on_top
        )

        always_on_top_action.triggered.connect(
            self.toggle_always_on_top
        )

        menu.addAction(always_on_top_action)

        # Show in taskbar
        taskbar_action = QAction(
            "Show in taskbar",
            self
        )

        taskbar_action.setCheckable(True)
        taskbar_action.setChecked(
            self.show_in_taskbar
        )

        taskbar_action.triggered.connect(
            self.toggle_taskbar
        )

        menu.addAction(taskbar_action)
        menu.addSeparator()

        # Size submenu
        size_menu = menu.addMenu("Size")

        sizes = {
            "Small": 200,
            "Medium": 320,
            "Large": 450,
            "Extra large": 600,
        }

        for name, size in sizes.items():
            action = QAction(
                f"{name} ({size}px)",
                self
            )

            action.triggered.connect(
                lambda checked=False, selected_size=size:
                self.set_clock_size(selected_size)
            )

            size_menu.addAction(action)

        # Opacity submenu
        opacity_menu = menu.addMenu("Opacity")

        for percentage in (
            100,
            90,
            80,
            70,
            60,
            50
        ):
            action = QAction(
                f"{percentage}%",
                self
            )

            action.setCheckable(True)

            current_percentage = round(
                self.windowOpacity() * 100
            )

            action.setChecked(
                current_percentage == percentage
            )

            action.triggered.connect(
                lambda checked=False, selected=percentage:
                self.set_opacity(selected)
            )

            opacity_menu.addAction(action)

        menu.addSeparator()

        # Open configuration folder
        config_action = QAction(
            "Open configuration folder",
            self
        )

        config_action.triggered.connect(
            self.open_config_folder
        )

        menu.addAction(config_action)

        menu.addSeparator()

        # Exit
        exit_action = QAction(
            "Exit",
            self
        )

        exit_action.triggered.connect(
            self.close
        )

        menu.addAction(exit_action)

        menu.exec(event.globalPos())

    # ========================================================
    # Menu actions
    # ========================================================

    def set_clock_size(self, size):
        size = max(
            self.MINIMUM_CLOCK_SIZE,
            min(int(size), self.MAXIMUM_CLOCK_SIZE)
        )

        self.resize(size, size)
        self.save_settings()

    def set_opacity(self, percentage):
        opacity = max(
            0.2,
            min(percentage / 100, 1.0)
        )

        self.setWindowOpacity(opacity)
        self.save_settings()

    def toggle_always_on_top(self):
        self.always_on_top = not self.always_on_top

        self.reapply_window_flags()
        self.save_settings()

    def toggle_taskbar(self):
        self.show_in_taskbar = not self.show_in_taskbar

        self.reapply_window_flags()
        self.save_settings()

    def open_config_folder(self):
        """
        Open the folder containing clock_config.json in Windows
        File Explorer.
        """

        try:
            os.startfile(str(CONFIG_FILE.parent))
        except OSError as error:
            print(
                f"Could not open configuration folder: {error}"
            )
            print(f"Configuration file: {CONFIG_FILE}")

    # ========================================================
    # Application shutdown
    # ========================================================

    def closeEvent(self, event):
        self.save_settings()

        self.clock_timer.stop()
        self.save_timer.stop()

        event.accept()

        application = QApplication.instance()

        if application is not None:
            application.quit()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            event.accept()
            return

        super().keyPressEvent(event)


# ============================================================
# Start application
# ============================================================

if __name__ == "__main__":
    app = QApplication(sys.argv)

    app.setApplicationName(
        "Desktop Analogue Clock"
    )

    app.setApplicationDisplayName(
        "Analogue Clock"
    )

    app.setQuitOnLastWindowClosed(True)

    clock = AnalogClock()
    clock.show()

    sys.exit(app.exec())