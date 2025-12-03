from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import QPainter, QTabletEvent, QColor
import sys

class TabletWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tablet Input Example")
        self.resize(800, 600)
        self.strokes = []

    def tabletEvent(self, event: QTabletEvent):
        if event.type() == QTabletEvent.TabletMove:
            pos = event.pos()
            pressure = event.pressure()
            self.strokes.append((pos, pressure))
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        for pos, pressure in self.strokes:
            radius = pressure * 10
            painter.setBrush(QColor(0, 0, 0))
            painter.drawEllipse(pos, radius, radius)

app = QApplication(sys.argv)
window = TabletWidget()
window.show()
sys.exit(app.exec_())

