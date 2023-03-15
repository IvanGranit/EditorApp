# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'data\untitled.ui'
#
# Created by: PyQt5 UI code generator 5.15.7
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.

import glob

from PyQt5.QtCore import QRect, Qt, QObject
from PyQt5.QtGui import QColor, QPixmap
from PyQt5 import QtCore
from PyQt5.QtWidgets import QLabel, QMainWindow, QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QMessageBox, \
    QPushButton, QFileDialog, QApplication, QHBoxLayout, QGraphicsScene, QGraphicsPixmapItem
import json

from canvas import Canvas
from centralLabel import Label, GraphicsScene
from SimpleObjects import SimplePoint, SimpleRect
from model import build_model
from centralLabel import GraphicsView


class Ui_MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.images_list = []

        self.setObjectName("MainWindow")
        self.resize(1920, 1080)

        self.central_widget = CentralWidget()
        self.central_widget.setObjectName("centralwidget")

        self.setCentralWidget(self.central_widget)


class CentralWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.dict = None
        self.elements_list = QListWidget()
        self.scene_list = QListWidget()
        self.create_list()
        self.dirlist = None
        self.setupUI()
        self.graphics_view = GraphicsView(self)
        self.graphics_view.setGeometry(150, 100, 1200, 800)

        self.load_project()

    def load_project(self):

        self.dirlist = QFileDialog.getExistingDirectory(None, "Выбрать папку", ".")

        if self.dirlist:
            try:
                with open(self.dirlist + r'/Контрольные точки/Points', 'r') as ff:
                    self.dict = json.loads(ff.read(), strict=False)
            except FileNotFoundError:
                message = QMessageBox()
                message.setText('Файл Points не найден,\n найти вручную?')
                message.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                answer = message.exec_()
                if answer == QMessageBox.Yes:
                    dirlist_points, _ = QFileDialog.getOpenFileName(None, "Выбрать папку",
                                                                    self.dirlist + '/Контрольные точки/')
                    if dirlist_points:
                        with open(dirlist_points, 'r') as ff:
                            self.dict = json.loads(ff.read(), strict=False)
                elif answer in (QMessageBox.No, QMessageBox.Close):
                    return

            if self.dict:
                self.elements_list.clear()
                for el in self.dict['Elements'].keys():
                    element = QListWidgetItem(el)

                    try:
                        item_widget, el_label, el_type = self.create_item(self.dict['Elements'][el]['Type'])
                    except KeyError:
                        item_widget, el_label, el_type = self.create_item()

                    self.elements_list.addItem(element)
                    self.elements_list.setItemWidget(element, item_widget)

                    el_label.setFixedSize(int(item_widget.width() * 0.25), item_widget.height())
                    el_type.setFixedSize(int(item_widget.width() * 0.75), item_widget.height())

                self.elements_list.setCurrentRow(0)

            self.scene_list.clear()
            for file in glob.glob(self.dirlist + r'\Виды\*'):
                self.scene_list.addItem(QListWidgetItem(file.split('\\')[-1]))
                self.create_scene(file)
            self.scene_list.setCurrentRow(0)
            self.scene_list_clicked()

            self.set_line(f'Elements & images loaded from {self.dirlist}')
        else:
            self.set_line('Project are not loaded')

    def next_item(self):
        self.elements_list.currentItem().setBackground(QColor("#AAFFAA"))
        self.elements_list.setCurrentRow(self.elements_list.currentRow() + 1)
        if self.elements_list.currentItem() is None:
            raise AttributeError

    def elements_list_clicked(self):
        print(f'item clicked {self.elements_list.currentItem().text()}')

    def scene_list_clicked(self):

        item = self.scene_list.currentItem().text()
        for element in self.findChildren(GraphicsScene):
            if element.objectName() == item:
                # noinspection PyTypeChecker
                self.graphics_view.setScene(element)

    def rewrite(self):
        self_dict = self.dict
        for scene in self.findChildren(GraphicsScene):
            for element in scene.items():

                if isinstance(element, SimpleRect):
                    if element.object_name in self_dict['Elements']:
                        self_dict['Elements'][element.object_name] \
                            ['Views'][str(scene.canvas.index)] = \
                            [{'L': int(element.rect().topLeft().x()),
                              'T': int(element.rect().topLeft().y()),
                              'R': int(element.rect().bottomRight().x()),
                              'B': int(element.rect().bottomRight().y()),
                              'Section': element.object_name}]

                if isinstance(element, SimplePoint):
                    if element.object_name in self_dict['Dots']:
                        self_dict['Dots'][element.object_name] \
                            ['Views'][str(scene.canvas.index)] = \
                            {'L': int(element.rect().topLeft().x()),
                             'T': int(element.rect().topLeft().y()),
                             'R': int(element.rect().bottomRight().x()),
                             'B': int(element.rect().bottomRight().y()),
                             'Section': element.object_name}

        with open(self.dirlist + r'/Контрольные точки/Points', 'w') as ff:
            json.dump(self_dict, ff, indent=1)
        self.set_line(f'File {self.dirlist}/Контрольные точки/Points rewrote', 'rgb(0, 200, 0)')

    def create_list(self):
        list_area = QWidget(self)
        list_area.setObjectName('ListElements')
        list_area.setGeometry(QRect(1400, 100, 400, 800))
        list_area.setStyleSheet(
            '#ListElements {border: 3px solid black};')
        vbox = QVBoxLayout()
        vbox.addWidget(self.elements_list)
        vbox.addWidget(self.scene_list)
        list_area.setLayout(vbox)

    def create_item(self, el_type: str = "Ошибка"):
        item_widget = QWidget()
        item_widget.setFixedSize(400, 22)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignLeft)

        el_label = QLabel()
        el_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        el_label.setContentsMargins(3, 0, 0, 0)

        el_type_label = QLabel(el_type)
        el_type_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        el_type_label.setContentsMargins(3, 0, 0, 0)

        layout.addWidget(el_label)
        layout.addWidget(el_type_label)

        el_type_label.setStyleSheet("color: #1111BB; "
                                    "font-size: 8pt; "
                                    "border: 1px solid #727272; "
                                    "border-right: 0px; "
                                    "border-top: 0px;"
                                    "border-bottom: 0px;")

        item_widget.setLayout(layout)

        return item_widget, el_label, el_type_label

    def create_scene(self, path):
        canvas = Canvas(path, model=model)
        scene = GraphicsScene(self.graphics_view, canvas)
        scene.setObjectName(path.split('\\')[-1])
        scene.setSceneRect(0, 0, scene.width(), scene.height())
        self.graphics_view.setScene(scene)

    def set_line(self, text=None, color='rgb(0, 0, 0)'):
        self.info_line.setText(text)
        if color:
            self.info_line.setStyleSheet(f"color: {color};")

    def setupUI(self):
        self.button_load = QPushButton(self)
        self.button_load.setGeometry(QtCore.QRect(10, 40, 121, 30))
        self.button_load.setObjectName("load_project")
        self.button_load.setText('Load project')

        self.button_rewrite = QPushButton(self)
        self.button_rewrite.setGeometry(QtCore.QRect(10, 120, 101, 30))
        self.button_rewrite.setObjectName("rewrite")
        self.button_rewrite.setText('Rewrite')

        self.info_line = QLabel('Hellow!', parent=self)
        self.info_line.setGeometry(QtCore.QRect(0, 933, 1920, 30))
        self.info_line.setAlignment(QtCore.Qt.AlignCenter)

        self.button_load.clicked.connect(self.load_project)
        self.button_rewrite.clicked.connect(self.rewrite)

        self.elements_list.clicked.connect(self.elements_list_clicked)
        self.scene_list.clicked.connect(self.scene_list_clicked)


if __name__ == "__main__":
    import sys

    model = build_model()
    model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
    model.load_weights('data/U-net/weights.hdf5')

    app = QApplication(sys.argv)
    ui = Ui_MainWindow()
    ui.show()
    sys.exit(app.exec_())
