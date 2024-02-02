from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


class LabelRect(QGraphicsRectItem):

    def __init__(self, rect, parent=None):

        super().__init__(parent=parent)


class FirstPin(QGraphicsEllipseItem):

    def __init__(self, rect, parent=None):
        
        super().__init__(parent=parent)


class Designator(QGraphicsRectItem):
    
    def __init__(self, rect, parent=None):
        
        super().__init__(parent=parent)
