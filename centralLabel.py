from time import sleep

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import QRect
from PyQt5.QtGui import QPainter, QFont
from PyQt5.QtWidgets import QLabel, QMessageBox
from centralObjects import Geometry
import cv2
from centralInstruments import Selection

import numpy as np


class Label(QLabel):

    def __init__(self, images_list=list, parent=None, ):
        super().__init__(parent=parent)

        self.images_list = images_list
        self.objects = []
        self.current_object = None
        self.start, self.finish = QtCore.QPoint(), QtCore.QPoint()
        self.points = None
        self.setAcceptDrops(True)

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
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() and QtCore.Qt.LeftButton and (self.start != self.finish):
            try:
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
            except IndexError:
                ex = 'Не найдено ни одной контрольной точки, \n попробуйте снова'
                self.onerror(ex)
            except KeyError:
                ex = 'Ошибка определения \n (Возможно вы не выбрали проект)'
                self.onerror(ex)
            except cv2.error:
                ex = 'Ошибка выделения, пожалуйста не выходите за границы окна'
                self.onerror(ex)
            except ValueError:
                ex = 'Ошибка обработки значений, \n попробуйте снова'
                self.onerror(ex)
            except Exception:
                ex = 'Неизвестная ошибка'
                self.onerror(ex)

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

    def onerror(self, ex):
        message = QMessageBox()
        message.setWindowTitle('Ошибка')
        message.setText(ex)
        message.exec_()
