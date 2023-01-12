from time import sleep

import matplotlib.pyplot as plt
from PyQt5 import QtCore
from PyQt5.QtCore import QRect, QMimeData, Qt
from PyQt5.QtGui import QPainter, QPixmap
from PyQt5.QtWidgets import QLabel, QListWidget
from qtpy import QtGui
from centralObjects import Geometry

import numpy as np

from canvas import Canvas


class Label(QLabel):

    def __init__(self, images_list=list, parent=None):
        super().__init__(parent=parent)
        self.images_list = images_list
        self.objects = []
        self.current_object = None
        self.start, self.finish = QtCore.QPoint(), QtCore.QPoint()
        self.points = None
        self.setAcceptDrops(True)
        self.flag = True

    def add_widget(self):
        self.objects.append(Geometry(self, self, *self.points))
        self.current_object = -1

    def add_points(self, points: list):
        for point in points:
            self.objects.append(Geometry(self, self, *self.points, point))

    def mousePressEvent(self, event):
        if event.buttons() == QtCore.Qt.LeftButton:
            self.start = event.pos()
            self.finish = self.start
            self.update()

    def mouseMoveEvent(self, event):
        if event.buttons() and QtCore.Qt.LeftButton:
            self.finish = event.pos()
            self.borderCheck()
            self.update()
            print(self.start, self.finish)

    def borderCheck(self):
        if self.finish.x() < 1:
            self.finish.setX(1)
        elif self.finish.x() > self.parent().cen_label.width() - 3:
            self.finish.setX(self.parent().cen_label.width() - 3)
        if self.finish.y() < 1:
            self.finish.setY(1)
        elif self.finish.y() > self.parent().cen_label.height() - 3:
            self.finish.setY(self.parent().cen_label.height() - 3)

    def mouseReleaseEvent(self, event):
        if event.button() and QtCore.Qt.LeftButton and (self.start != self.finish):
            rect = QRect(self.start, self.finish)
            painter = QPainter(self)
            painter.drawRect(rect.normalized())
            self.points = np.array([self.start.x(),
                                    self.start.y(),
                                    self.finish.x(),
                                    self.finish.y()])
            self.start, self.finish = QtCore.QPoint(), QtCore.QPoint()

            self.add_widget()
            dots = self.images_list[-1].pins2json(self.points * 4)
            self.add_points(points=dots)
            self.parent().to_points_elements(self.points)
            self.parent().to_points_dots(dots)
            self.parent().next_item()

    def paintEvent(self, event):
        super(Label, self).paintEvent(event)
        painter = QPainter(self)
        if not self.start.isNull() and not self.finish.isNull():
            rect = QRect(self.start, self.finish)
            painter.drawRect(rect.normalized())

    def dragEnterEvent(self, e):
        e.accept()

    def dropEvent(self, e):

        position = e.pos()
        self.objects[self.current_object].move(position)

        e.setDropAction(QtCore.Qt.MoveAction)
        e.accept()

    def call(self, child_class=None):
        self.current_object = self.objects.index(child_class)



