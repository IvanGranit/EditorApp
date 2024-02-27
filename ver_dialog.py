from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from simple_objects import SimpleRect


class VerifyDialog(QDialog):

    def __init__(self, view, scene, rects):

        super(VerifyDialog, self).__init__()

        # UI setup
        self.LineEditFrame = QFrame(self)
        self.LineEditFrame.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.LineEditFrame.setFixedSize(300, 130)
        self.LineEditFrame.move(0, 0)

        self.NameLine = QLineEdit(self.LineEditFrame)
        self.NameLine.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.NameLine.setFixedSize(200, 50)
        self.NameLine.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.NameLine.move(40, 50)

        self.ButtonsFrame = QFrame(self)
        self.ButtonsFrame.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.ButtonsFrame.setFixedSize(300, 40)
        self.ButtonsFrame.move(0, 160)

        self.LeftButton = QPushButton(self.ButtonsFrame)
        self.LeftButton.setText('<---')
        self.LeftButton.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.LeftButton.setFixedSize(45, 25)
        self.LeftButton.move(164, 7)

        self.RightButton = QPushButton(self.ButtonsFrame)
        self.RightButton.setText('--->')
        self.RightButton.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.RightButton.setFixedSize(45, 25)
        self.RightButton.move(233, 7)

        self.view = view
        self.scene = scene
        self.rects = rects

        self.items = []
        self.pointer_index = 0
        self.temp_dict = {}
        self.dict = {}

        self.create_dict()

    def create_dict(self):

        self.temp_dict.clear()

        group_id = self.rects['shapes'][self.pointer_index]['group_id']

        counter = 0

        # Try

        while self.rects['shapes'][self.pointer_index]['group_id'] == group_id:

            if self.rects['shapes'][self.pointer_index]['description'] != 'other':

                self.temp_dict[counter] = self.rects['shapes'][self.pointer_index]
                self.NameLine.setPlaceholderText(self.rects['shapes'][self.pointer_index]['label'])

            self.pointer_index += 1

        if len(self.dict) != 3:

            return self.create_dict()

        elif len(self.dict) == 3:

            self.display_group()
            self.verify_group()

        if self.rects['shapes'][self.pointer_index - 1] != self.rects['shapes'][-1]:

            self.rects.clear()
            self.rects = self.dict
            self.close()

    def left_clicked(self):

        if self.pointer_index >= 0:

            self.pointer_index -= 1
            self.create_dict()

    def right_clicked(self):

        if self.pointer_index < len(self.rects['shapes']):

            self.pointer_index -= 1
            self.create_dict()

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

    def keyPressEvent(self, event):

        if event.key() == Qt.Key_Return:

            self.verify_group()
