import sys
import math
import json
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
from PyQt6.QtWidgets import QApplication, QWidget, QMenu


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

CONFIG_FILE = Path(__file__).with_name("clock_config.json")

DEFAULT_CONFIG = {
    "x": 100,
    "y": 100,
    "size": 320,
    "opacity": 1.0,
    "always_on_top": True,
}


def load_config():
    """
    Load configuration from clock_config.json.

    Missing values automatically fall back to defaults.
    """

    config = DEFAULT_CONFIG.copy()

    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as file:
                saved_config = json.load(file)

            config.update(saved_config)

        except (OSError, json.JSONDecodeError):
            print("Could not read configuration file. Using defaults.")

    return config


def save_config(config):
    """
    Save configuration to clock_config.json.
    """

    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as file:
            json.dump(
                config,
                file,
                indent=4
            )

    except OSError as error:
        print(f"Could not save configuration: {error}")


# ---------------------------------------------------------
# Analogue clock
# ---------------------------------------------------------

class AnalogClock(QWidget):

    def __init__(self):
        super().__init__()

        self.config = load_config()

        self.drag_position = QPoint()

        self.resizing = False
        self.resize_start_position = QPoint()
        self.resize_start_size = 0

        self.resize_margin = 18

        self.always_on_top = bool(
            self.config["always_on_top"]
        )

        self.setWindowTitle("Analogue Clock")

        # -------------------------------------------------
        # Window flags
        # -------------------------------------------------

        self.apply_window_flags()

        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground
        )

        self.setMouseTracking(True)

        # -------------------------------------------------
        # Restore size
        # -------------------------------------------------

        size = int(self.config["size"])

        # Prevent bad config values making the clock vanish
        size = max(140, min(size, 1000))

        self.setMinimumSize(140, 140)

        self.resize(
            size,
            size
        )

        # -------------------------------------------------
        # Restore position
        # -------------------------------------------------

        self.move(
            int(self.config["x"]),
            int(self.config["y"])
        )

        # -------------------------------------------------
        # Restore opacity
        # -------------------------------------------------

        opacity = float(
            self.config["opacity"]
        )

        opacity = max(
            0.2,
            min(opacity, 1.0)
        )

        self.setWindowOpacity(opacity)

        # -------------------------------------------------
        # Save delay
        #
        # Moving/resizing can generate lots of events.
        # Rather than writing the JSON file constantly,
        # wait briefly until the activity settles.
        # -------------------------------------------------

        self.save_timer = QTimer(self)
        self.save_timer.setSingleShot(True)
        self.save_timer.timeout.connect(
            self.save_settings
        )

        # -------------------------------------------------
        # Clock animation
        # -------------------------------------------------

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(16)

    # ---------------------------------------------------------
    # Window flags
    # ---------------------------------------------------------

    def apply_window_flags(self):

        flags = (
            Qt.WindowType.Window
            | Qt.WindowType.FramelessWindowHint
        )

        if self.always_on_top:
            flags |= Qt.WindowType.WindowStaysOnTopHint

        self.setWindowFlags(flags)

    # ---------------------------------------------------------
    # Configuration saving
    # ---------------------------------------------------------

    def schedule_save(self):
        """
        Wait 400 ms before actually writing the config.

        Each new movement restarts the timer.
        """

        self.save_timer.start(400)

    def save_settings(self):

        self.config = {
            "x": self.x(),
            "y": self.y(),
            "size": self.width(),
            "opacity": round(
                self.windowOpacity(),
                2
            ),
            "always_on_top": self.always_on_top,
        }

        save_config(self.config)

    # ---------------------------------------------------------
    # Drawing
    # ---------------------------------------------------------

    def paintEvent(self, event):

        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        width = self.width()
        height = self.height()

        size = min(
            width,
            height
        )

        painter.translate(
            width / 2,
            height / 2
        )

        scale = size / 320.0

        painter.scale(
            scale,
            scale
        )

        self.draw_face(painter)
        self.draw_numbers(painter)
        self.draw_hands(painter)
        self.draw_centre(painter)

    # ---------------------------------------------------------

    def draw_face(self, painter):

        radius = 145

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

        # Border

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

        # Markings

        for i in range(60):

            painter.save()

            painter.rotate(
                i * 6
            )

            if i % 5 == 0:

                painter.setPen(
                    QPen(
                        QColor(
                            235,
                            235,
                            240
                        ),
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
                        QColor(
                            120,
                            125,
                            135
                        ),
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

    # ---------------------------------------------------------

    def draw_numbers(self, painter):

        painter.setPen(
            QColor(
                225,
                225,
                230
            )
        )

        font = QFont(
            "Segoe UI"
        )

        font.setPointSize(13)

        font.setWeight(
            QFont.Weight.Medium
        )

        painter.setFont(font)

        radius = 108

        for number in range(1, 13):

            angle = math.radians(
                number * 30 - 90
            )

            x = (
                math.cos(angle)
                * radius
            )

            y = (
                math.sin(angle)
                * radius
            )

            painter.drawText(
                int(x - 17),
                int(y - 14),
                34,
                28,
                Qt.AlignmentFlag.AlignCenter,
                str(number)
            )

    # ---------------------------------------------------------

    def draw_hands(self, painter):

        now = datetime.now()

        seconds = (
            now.second
            + now.microsecond
            / 1_000_000
        )

        minutes = (
            now.minute
            + seconds / 60
        )

        hours = (
            (now.hour % 12)
            + minutes / 60
        )

        self.draw_hand(
            painter,
            hours * 30,
            68,
            7,
            QColor(
                240,
                240,
                245
            )
        )

        self.draw_hand(
            painter,
            minutes * 6,
            100,
            5,
            QColor(
                220,
                225,
                235
            )
        )

        self.draw_hand(
            painter,
            seconds * 6,
            118,
            2,
            QColor(
                255,
                75,
                75
            ),
            25
        )

    # ---------------------------------------------------------

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

    # ---------------------------------------------------------

    def draw_centre(self, painter):

        painter.setPen(
            Qt.PenStyle.NoPen
        )

        painter.setBrush(
            QColor(
                255,
                75,
                75
            )
        )

        painter.drawEllipse(
            -7,
            -7,
            14,
            14
        )

        painter.setBrush(
            QColor(
                235,
                235,
                240
            )
        )

        painter.drawEllipse(
            -3,
            -3,
            6,
            6
        )

    # ---------------------------------------------------------
    # Resize detection
    # ---------------------------------------------------------

    def is_near_edge(self, position):

        centre_x = (
            self.width() / 2
        )

        centre_y = (
            self.height() / 2
        )

        dx = (
            position.x()
            - centre_x
        )

        dy = (
            position.y()
            - centre_y
        )

        distance = math.sqrt(
            dx * dx
            + dy * dy
        )

        radius = (
            min(
                self.width(),
                self.height()
            ) / 2
        )

        return (
            distance
            >= radius
            - self.resize_margin
        )

    # ---------------------------------------------------------
    # Mouse press
    # ---------------------------------------------------------

    def mousePressEvent(self, event):

        if (
            event.button()
            == Qt.MouseButton.LeftButton
        ):

            if self.is_near_edge(
                event.position()
            ):

                self.resizing = True

                self.resize_start_position = (
                    event
                    .globalPosition()
                    .toPoint()
                )

                self.resize_start_size = (
                    self.width()
                )

            else:

                self.resizing = False

                self.drag_position = (
                    event
                    .globalPosition()
                    .toPoint()
                    - self.frameGeometry()
                    .topLeft()
                )

            event.accept()

    # ---------------------------------------------------------
    # Mouse movement
    # ---------------------------------------------------------

    def mouseMoveEvent(self, event):

        # Resize

        if (
            self.resizing
            and event.buttons()
            & Qt.MouseButton.LeftButton
        ):

            current = (
                event
                .globalPosition()
                .toPoint()
            )

            delta = (
                current
                - self.resize_start_position
            )

            if (
                abs(delta.x())
                > abs(delta.y())
            ):

                change = delta.x()

            else:

                change = delta.y()

            new_size = (
                self.resize_start_size
                + change
            )

            new_size = max(
                140,
                min(
                    new_size,
                    1000
                )
            )

            self.resize(
                new_size,
                new_size
            )

            self.schedule_save()

            event.accept()

            return

        # Move

        if (
            event.buttons()
            & Qt.MouseButton.LeftButton
        ):

            self.move(
                event
                .globalPosition()
                .toPoint()
                - self.drag_position
            )

            self.schedule_save()

            event.accept()

            return

        # Cursor

        if self.is_near_edge(
            event.position()
        ):

            centre_x = (
                self.width()
                / 2
            )

            centre_y = (
                self.height()
                / 2
            )

            dx = (
                event.position().x()
                - centre_x
            )

            dy = (
                event.position().y()
                - centre_y
            )

            if dx * dy >= 0:

                self.setCursor(
                    Qt.CursorShape.SizeFDiagCursor
                )

            else:

                self.setCursor(
                    Qt.CursorShape.SizeBDiagCursor
                )

        else:

            self.setCursor(
                Qt.CursorShape.ArrowCursor
            )

    # ---------------------------------------------------------

    def mouseReleaseEvent(self, event):

        if (
            event.button()
            == Qt.MouseButton.LeftButton
        ):

            self.resizing = False

            # Save immediately after move/resize finishes
            self.save_settings()

            event.accept()

    # ---------------------------------------------------------
    # Context menu
    # ---------------------------------------------------------

    def contextMenuEvent(self, event):

        menu = QMenu(self)

        # Always on top

        top_action = QAction(
            "Always on top",
            self
        )

        top_action.setCheckable(True)

        top_action.setChecked(
            self.always_on_top
        )

        top_action.triggered.connect(
            self.toggle_always_on_top
        )

        menu.addAction(
            top_action
        )

        # -------------------------------------------------
        # Size
        # -------------------------------------------------

        size_menu = menu.addMenu(
            "Size"
        )

        sizes = {
            "Small": 200,
            "Medium": 320,
            "Large": 450,
            "Extra Large": 600,
        }

        for name, size in sizes.items():

            action = QAction(
                f"{name} ({size}px)",
                self
            )

            action.triggered.connect(
                lambda checked=False, s=size:
                self.set_clock_size(s)
            )

            size_menu.addAction(
                action
            )

        # -------------------------------------------------
        # Opacity
        # -------------------------------------------------

        opacity_menu = menu.addMenu(
            "Opacity"
        )

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

            action.triggered.connect(
                lambda checked=False, p=percentage:
                self.set_opacity(p)
            )

            opacity_menu.addAction(
                action
            )

        menu.addSeparator()

        # -------------------------------------------------
        # Open config file
        # -------------------------------------------------

        config_action = QAction(
            "Show Config Location",
            self
        )

        config_action.triggered.connect(
            self.show_config_location
        )

        menu.addAction(
            config_action
        )

        menu.addSeparator()

        # Exit

        exit_action = QAction(
            "Exit",
            self
        )

        exit_action.triggered.connect(
            self.close
        )

        menu.addAction(
            exit_action
        )

        menu.exec(
            event.globalPos()
        )

    # ---------------------------------------------------------

    def set_clock_size(self, size):

        self.resize(
            size,
            size
        )

        self.save_settings()

    # ---------------------------------------------------------

    def set_opacity(self, percentage):

        opacity = (
            percentage
            / 100
        )

        self.setWindowOpacity(
            opacity
        )

        self.save_settings()

    # ---------------------------------------------------------

    def toggle_always_on_top(self):

        self.always_on_top = (
            not self.always_on_top
        )

        position = self.pos()

        self.apply_window_flags()

        self.move(position)

        self.show()

        self.save_settings()

    # ---------------------------------------------------------

    def show_config_location(self):

        print(
            f"Configuration: {CONFIG_FILE}"
        )

    # ---------------------------------------------------------
    # Save when closing
    # ---------------------------------------------------------

    def closeEvent(self, event):
        self.save_settings()

        # Stop our timers
        self.timer.stop()
        self.save_timer.stop()

        event.accept()

        # Terminate the Qt application/event loop
        QApplication.instance().quit()

    # ---------------------------------------------------------

    def keyPressEvent(self, event):

        if (
            event.key()
            == Qt.Key.Key_Escape
        ):

            self.close()


# ---------------------------------------------------------
# Start application
# ---------------------------------------------------------
if __name__ == "__main__":

    app = QApplication(sys.argv)

    app.setApplicationName(
        "Desktop Analogue Clock"
    )

    # Ensure closing the clock terminates Python
    app.setQuitOnLastWindowClosed(True)

    clock = AnalogClock()
    clock.show()

    sys.exit(app.exec())
