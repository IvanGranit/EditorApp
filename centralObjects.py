from PyQt5.QtWidgets import QLabel
from qtpy import QtGui
from PyQt5.QtCore import QMimeData, Qt


class Geometry(QLabel):

    def mouseMoveEvent(self, ev: QtGui.QMouseEvent) -> None:
        if ev.buttons() != Qt.RightButton:
            mimeData = QMimeData()

            drag = QtGui.QDrag(self)
            drag.setMimeData(mimeData)
            drag.setHotSpot(ev.pos() - self.rect().topLeft())

            drag.exec_(Qt.MoveAction)

    def mousePressEvent(self, ev):
        QLabel.mousePressEvent(self, ev)

        if ev.button() == Qt.LeftButton:
            self.setStyleSheet('border: 3px solid black')

        self.parent_class.call(self)


class simpleRect(Geometry):

    def __init__(self, parent=None, parent_class=None, x=None, y=None, w=None, h=None):
        super().__init__(parent)
        self.parent_class = parent_class
        self.setStyleSheet('border: 3px solid white')
        self.setGeometry(x, y, w - x, h - y)
        self.show()


class simplePoint(Geometry):

    def __init__(self, parent=None, parent_class=None, geom=None):
        super().__init__(parent)
        self.parent_class = parent_class
        self.setStyleSheet('border: 1px solid red; background-color: rgb(100,100,100);')
        self.setGeometry(int(geom[0] / 4), int(geom[1] / 4), 7, 7)
        self.show()
