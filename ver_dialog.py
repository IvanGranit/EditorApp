from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from simple_objects import SimpleRect

from graphic_func import rotate_rect


class VerifyDialog(QDialog):

    def __init__(self, view, scene, rects):

        from PyQt5 import uic

        super(VerifyDialog, self).__init__()

        uic.loadUi('VerDialog.ui', self)

        self.view = view
        self.scene = scene
        self.rects = rects

        self.OkayButton.clicked.connect(self.next)

        self.items = []
        self.pointer_index = 0
        self.temp_dict = {}
        self.dict = {}

        self.create_dict()

    def create_dict(self):

        self.temp_dict.clear()

        group_id = self.rects[self.pointer_index]['group_id']
        counter = 0

        while self.rects[self.pointer_index]['group_id'] == group_id:

            if self.rects[self.pointer_index]['description'] != 'other':

                self.temp_dict[counter] = self.rects[self.pointer_index]

            self.pointer_index += 1

        if len(self.dict) != 3 and self.rects[self.pointers_index - 1] != self.rects[-1]:

            return self.create_dict()

        elif len(self.dict) == 3 and self.rects[self.pointers_index - 1] != self.rects[-1]:

            self.verify_group()

        if self.rects[self.pointers_index - 1] != self.rects[-1]:

            self.rects.clear()
            self.rects = self.dict
            self.close()

    def display_group(self):

        self.items.clear()

        for rect in self.temp_dict:

            coord = rect['points']

            rect_f = QRectF(

                coord[0][0],
                coord[0][1],
                abs(coord[0][0] - coord[1][0]),
                abs(coord[0][1] - coord[1][1])

            )

            try:

                name = rect['label'].split('-')[-1]

            except IndexError:

                name = rect['label']

            rect = SimpleRect(x_start=rect_f.x(),
                              y_start=rect_f.y(),
                              x_finish=rect_f.width() + rect_f.x(),
                              y_finish=rect_f.height() + rect_f.y(),
                              object_name=name,
                              mod='AXE')

            self.items.append(rect)
            self.scene.addItem(rect)

    def verify_group(self):

        for rect in self.temp_dict:

            rect['label'] = self.NameLine.text()
            self.dict[len(self.dict) + 1] = rect

        self.create_dict()

    def keyPressEvent(self, event):

        if event.key() == Qt.Key_Return:

            self.verify_group()
