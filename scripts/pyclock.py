import sys
import math
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


class AnalogClock(QWidget):
    def __init__(self):
        super().__init__()

        self.clock_size = 320
        self.drag_position = QPoint()
        self.always_on_top = True

        self.setWindowTitle("Analogue Clock")
        self.resize(self.clock_size, self.clock_size)

        # Make the window frameless and always on top
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )

        # Allow transparent areas around the circular clock
        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground
        )

        # Timer drives the animation
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(16)  # ~60 FPS

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

        size = min(width, height)

        painter.translate(
            width / 2,
            height / 2
        )

        scale = size / 320.0
        painter.scale(scale, scale)

        self.draw_face(painter)
        self.draw_numbers(painter)
        self.draw_hands(painter)
        self.draw_centre(painter)

    def draw_face(self, painter):
        radius = 145

        # Shadow-like outer ring
        painter.setPen(
            QPen(QColor(0, 0, 0, 100), 8)
        )

        painter.setBrush(
            QBrush(QColor(25, 27, 31, 245))
        )

        painter.drawEllipse(
            -radius,
            -radius,
            radius * 2,
            radius * 2
        )

        # Border
        painter.setBrush(Qt.BrushStyle.NoBrush)

        painter.setPen(
            QPen(QColor(110, 115, 125), 2)
        )

        painter.drawEllipse(
            -radius + 3,
            -radius + 3,
            (radius - 3) * 2,
            (radius - 3) * 2
        )

        # Minute/hour markers
        for i in range(60):

            painter.save()

            painter.rotate(i * 6)

            if i % 5 == 0:
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

        radius = 108

        for number in range(1, 13):

            angle = math.radians(
                number * 30 - 90
            )

            x = math.cos(angle) * radius
            y = math.sin(angle) * radius

            rect_width = 34
            rect_height = 28

            painter.drawText(
                int(x - rect_width / 2),
                int(y - rect_height / 2),
                rect_width,
                rect_height,
                Qt.AlignmentFlag.AlignCenter,
                str(number)
            )

    def draw_hands(self, painter):
        now = datetime.now()

        hour = now.hour % 12
        minute = now.minute
        second = now.second
        microsecond = now.microsecond

        # Smooth fractional seconds
        seconds = second + microsecond / 1_000_000

        minutes = (
            minute
            + seconds / 60
        )

        hours = (
            hour
            + minutes / 60
        )

        # Hour hand
        self.draw_hand(
            painter,
            angle=hours * 30,
            length=68,
            width=7,
            colour=QColor(240, 240, 245)
        )

        # Minute hand
        self.draw_hand(
            painter,
            angle=minutes * 6,
            length=100,
            width=5,
            colour=QColor(220, 225, 235)
        )

        # Second hand
        self.draw_hand(
            painter,
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

        pen = QPen(
            colour,
            width,
            Qt.PenStyle.SolidLine,
            Qt.PenCapStyle.RoundCap
        )

        painter.setPen(pen)

        painter.drawLine(
            0,
            tail,
            0,
            -length
        )

        painter.restore()

    def draw_centre(self, painter):
        painter.setPen(Qt.PenStyle.NoPen)

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

    # ---------------------------------------------------------
    # Window dragging
    # ---------------------------------------------------------

    def mousePressEvent(self, event):
        if (
            event.button()
            == Qt.MouseButton.LeftButton
        ):
            self.drag_position = (
                event.globalPosition().toPoint()
                - self.frameGeometry().topLeft()
            )

            event.accept()

    def mouseMoveEvent(self, event):
        if (
            event.buttons()
            & Qt.MouseButton.LeftButton
        ):
            self.move(
                event.globalPosition().toPoint()
                - self.drag_position
            )

            event.accept()

    # ---------------------------------------------------------
    # Double click
    # ---------------------------------------------------------

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_always_on_top()

    # ---------------------------------------------------------
    # Right-click menu
    # ---------------------------------------------------------

    def contextMenuEvent(self, event):
        menu = QMenu(self)

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

        menu.addAction(top_action)

        # Opacity submenu
        opacity_menu = menu.addMenu(
            "Opacity"
        )

        for percentage in (
            100,
            90,
            80,
            70,
            60,
            50,
        ):
            action = QAction(
                f"{percentage}%",
                self
            )

            action.triggered.connect(
                lambda checked,
                p=percentage:
                self.setWindowOpacity(
                    p / 100
                )
            )

            opacity_menu.addAction(action)

        menu.addSeparator()

        exit_action = QAction(
            "Exit",
            self
        )

        exit_action.triggered.connect(
            QApplication.quit
        )

        menu.addAction(exit_action)

        menu.exec(
            event.globalPos()
        )

    def toggle_always_on_top(self):
        self.always_on_top = (
            not self.always_on_top
        )

        flags = (
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
        )

        if self.always_on_top:
            flags |= (
                Qt.WindowType.WindowStaysOnTopHint
            )

        position = self.pos()

        self.setWindowFlags(flags)

        self.move(position)
        self.show()

    # ---------------------------------------------------------
    # Keyboard
    # ---------------------------------------------------------

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    app.setApplicationName(
        "Desktop Analogue Clock"
    )

    clock = AnalogClock()
    clock.show()

    sys.exit(app.exec())