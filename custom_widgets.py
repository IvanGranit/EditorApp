from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from simple_objects import SimpleRect, SimplePoint, AnchorRect, CropItem
from conf_dialog import ConfDialog
from ver_dialog import VerifyDialog

import numpy as np

from canvas import Canvas

import logging
from datetime import datetime
from preparation_v2 import preparate
from ultralytics import YOLO

from graphic_func import rotate_rect

logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S", filename=f"logs/{datetime.now().date()}.log")
model2 = YOLO("./segmentator.pt")


class MovableTabs(QTabWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setMinimumSize(550, 30)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.parent = parent
        self.setAcceptDrops(True)
        self.tabBar = self.tabBar()
        self.tabBar.setMouseTracking(True)
        self.indexTab = None
        self.setMovable(True)
        self.setDocumentMode(True)

    def mouseMoveEvent(self, e):

        if e.buttons() != Qt.RightButton:

            return

        globalPos = self.mapToGlobal(e.pos())
        tabBar = self.tabBar
        posInTab = tabBar.mapFromGlobal(globalPos)
        self.indexTab = tabBar.tabAt(e.pos())
        tabRect = tabBar.tabRect(self.indexTab)

        pixmap = QPixmap(tabRect.size())
        tabBar.render(pixmap, QPoint(), QRegion(tabRect))
        mimeData = QMimeData()
        drag = QDrag(tabBar)
        drag.setMimeData(mimeData)
        drag.setPixmap(pixmap)
        cursor = QCursor(Qt.OpenHandCursor)
        drag.setHotSpot(e.pos() - posInTab)
        drag.setDragCursor(cursor.pixmap(), Qt.MoveAction)
        dropAction = drag.exec_(Qt.MoveAction)

    def dragEnterEvent(self, event):

        try:

            event.accept()

            if event.source().parentWidget() != self:
                return

            self.parent.TABINDEX = self.indexOf(self.widget(self.indexTab))

        except Exception as ex:

            logging.critical(f"{type(ex)}; Wrong tab drag event; widget: {type(self)}; py: {ex}")

    def dragLeaveEvent(self, event):

        event.accept()

    def dropEvent(self, event):

        if event.source().parentWidget() == self:

            return

        event.setDropAction(Qt.MoveAction)
        event.accept()
        counter = self.count()

        try:

            if counter == 0:

                self.addTab(event.source().parentWidget().widget(self.parent.TABINDEX),
                            event.source().tabText(self.parent.TABINDEX))

            else:

                self.insertTab(counter + 1, event.source().parentWidget().widget(self.parent.TABINDEX),
                               event.source().tabText(self.parent.TABINDEX))

        except Exception as ex:

            logging.critical(f"{type(ex)}; Wrong tab drop event; widget: {type(self)}; py: {ex}")


class TreeWidgetItem(QTreeWidgetItem):

    def __init__(self, el: str = "Ошибка", el_type: str = "Ошибка"):

        super().__init__()

        self.widget = QWidget()
        self.widget.setFixedSize(200, 30)
        self.setSizeHint(0, QSize(200, 30))

        self.name = el
        self.type = el_type

        self.status = False
        self.graphic = None

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.el_label = ELLabel(self.name)
        self.el_label.setFixedSize(80, 30)

        self.el_type_label = ELTypeLabel(self.type)
        self.el_type_label.setFixedSize(120, 30)

        layout.addWidget(self.el_label)
        layout.addWidget(self.el_type_label)

        self.widget.setLayout(layout)

        self.b = None
        self.d = None
        self.k = None

    def change_status(self, status: bool):

        self.status = status

        if self.status:

            self.el_label.setText(self.name + " ✓")

        else:

            self.el_label.setText(self.name)

    def getSBData(self) -> tuple:
        """ (0) body, (1) designator, (2) key """

        return self.b, self.d, self.k

    def setSBData(self, listWidget, children: list) -> None:
        """ [0] body, [1] designator, [2] key """

        for child in children:

            self.addChild(child)
            listWidget.setItemWidget(child, 0, child.widget)

        self.b, self.d, self.k = children

        return


class TreeWidgetChild(QTreeWidgetItem):

    def __init__(self, name="Ошибка"):

        super().__init__()

        self.setText(0, name)

        self.name = name
        self.status = False
        self.graphic = None

    def change_status(self, status: bool):

        self.status = status

        if self.status:

            self.setText(0, self.name + " ✓")

        else:

            self.setText(0, self.name)


class TreeWidgetDescription(QTreeWidgetItem):

    def __init__(self, text: str, status: int = 0):
        
        super().__init__()

        # Status: 0 - unlabeled; 1 - not found; 2 - labeled;

        self.status = status
        self.parameter = text

        self.setSizeHint(0, QSize(200, 20))

        self.widget = QWidget()
        self.widget.setFixedSize(200, 20)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.label = QLabel(self.parameter)
        self.label.setFixedSize(200, 20)
        self.label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        layout.addWidget(self.label)

        self.widget.setLayout(layout)

        self.changeStatus(self.status)

    def changeStatus(self, status: int = 0) -> None:

        if not 0 <= self.status <= 2:

            return

        self.status = status

        if status == 0:

            self.label.setText(f'<font color = "#b1b1b1">{self.parameter}:</font> <font color="gray">Unlabeled</font>')

        elif status == 1:

            self.label.setText(f'<font color = "#b1b1b1">{self.parameter}:</font> <font color="red">Not found</font>')

        elif status == 2:

            self.label.setText(f'<font color = "#b1b1b1">{self.parameter}:</font> <font color="green">Labeled</font>')


class ELLabel(QLabel):

    def __init__(self, el):
        super().__init__()

        self.setText(el)
        self.setObjectName("ItemWidgetEl")
        self.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.setContentsMargins(3, 0, 0, 0)


class ELTypeLabel(QLabel):

    def __init__(self, el_type):
        super().__init__()

        self.setText(el_type)
        self.setObjectName("ItemWidgetElType")
        self.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.setContentsMargins(3, 0, 0, 0)


class GraphicsScene(QGraphicsScene):
    """Интерактивная область для разметки и работы с элементами на отдельном фото ОД"""
    itemClicked = pyqtSignal(QGraphicsItem)
    itemMoved = pyqtSignal(dict)

    def __init__(self, parent, canvas: Canvas):
        super().__init__(parent=parent)

        self.canvas = canvas
        self.pic = QGraphicsPixmapItem()
        self.pixmap = QPixmap(canvas.path)
        w = self.pixmap.width()
        h = self.pixmap.height()
        self.kw = 4800 / w
        self.kh = 3200 / h
        self.pic.setPixmap(self.pixmap)
        self.addItem(self.pic)
        self.setSceneRect(QRectF(0, 0, w, h))


class GraphicsBlueprintItem(QGraphicsPixmapItem):

    def __init__(self, path):
        super().__init__()

        self.path = path
        self.pixmap = QPixmap(path)
        self.setPixmap(self.pixmap)
        self.adjustable = False
        self.visible = True
        self.dx, self.dy = 0, 0
        self.anchors = {}
        self.update_anchors()
        self.anchor_list = []
        self.last_mod = None

        for rect in self.anchors.keys():

            self.anchor_list.append(BlueprintAnchor(self, rect, self.anchors.get(rect)))
            pass

    def setAdjustable(self, status: bool):

        self.adjustable = status

        if status:

            self.setZValue(5)
            self.setCursor(Qt.SizeAllCursor)
            self.last_mod = self.scene().parent().mainwindow.mod
            self.scene().parent().mainwindow.mod = None

            for rect in self.anchor_list:

                rect.setVisible(True)

            self.setAcceptTouchEvents(True)

        else:

            self.setZValue(0)
            self.setCursor(Qt.CrossCursor)
            self.scene().parent().mainwindow.mod = self.last_mod

            for rect in self.anchor_list:

                rect.setVisible(False)

            self.setAcceptTouchEvents(True)

    def mousePressEvent(self, event):

        if self.adjustable:

            self.dx, self.dy = event.scenePos().x() - self.x(), event.scenePos().y() - self.y()

    def mouseMoveEvent(self, event):

        if self.adjustable:

            self.setX(event.scenePos().x() - self.dx)
            self.setY(event.scenePos().y() - self.dy)

    def mouseReleaseEvent(self, event):

        return

    def update_anchors(self):

        self.anchors = {
            "topLeft": [QRectF(0, 0, 20, 20), Qt.SizeFDiagCursor],
            "topRight": [QRectF(self.pixmap.width() - 20, 0, 20, 20), Qt.SizeBDiagCursor],
            "bottomRight": [QRectF(self.pixmap.width() - 20, self.pixmap.height() - 20, 20, 20), Qt.SizeFDiagCursor],
            "bottomLeft": [QRectF(0, self.pixmap.height() - 20, 20, 20), Qt.SizeBDiagCursor],
            "left": [QRectF(0, 20, 20, self.pixmap.height() - 40), Qt.SizeHorCursor],
            "top": [QRectF(20, 0, self.pixmap.width() - 40, 20), Qt.SizeVerCursor],
            "right": [QRectF(0 + self.pixmap.width() - 20, 20, 20, self.pixmap.height() - 40), Qt.SizeHorCursor],
            "bottom": [QRectF(20, self.pixmap.height() - 20, self.pixmap.width() - 40, 20), Qt.SizeVerCursor],
        }

        for el in self.childItems():
            el.setRect(self.anchors[el.location][0])

    def anchor_drag(self, anchor, pos):

        x, y = int(pos.x()), int(pos.y())
        pix_x, pix_y, pix_width, pix_height = int(self.scenePos().x()), int(self.scenePos().y()), self.pixmap.width(), self.pixmap.height()

        if anchor.location == "left":
            if self.pixmap.width() != 100 or pix_x - x > 0:
                self.pixmap = QPixmap(self.image).scaled(QSize(pix_x - x + pix_width, pix_height), Qt.IgnoreAspectRatio)
                self.setPixmap(self.pixmap)
                self.setX(x)
                self.flip_checker(side1="left")
        if anchor.location == "top":
            if self.pixmap.height() != 100 or pix_y - y > 0:
                self.pixmap = QPixmap(self.image).scaled(QSize(pix_width, pix_y - y + pix_height), Qt.IgnoreAspectRatio)
                self.setPixmap(self.pixmap)
                self.setY(y)
                self.flip_checker(side2="top")
        if anchor.location == "right":
            if self.pixmap.width() != 100 or x - (pix_x + pix_width) > 0:
                self.pixmap = QPixmap(self.image).scaled(QSize(x - (pix_x + pix_width) + pix_width, pix_height), Qt.IgnoreAspectRatio)
                self.setPixmap(self.pixmap)
                self.flip_checker(side1="right")
        if anchor.location == "bottom":
            if self.pixmap.height() != 100 or y - (pix_y + pix_height) > 0:
                self.pixmap = QPixmap(self.image).scaled(QSize(pix_width, y - (pix_y + pix_height) + pix_height), Qt.IgnoreAspectRatio)
                self.setPixmap(self.pixmap)
                self.flip_checker(side2="bottom")
        if anchor.location == "topLeft":

            if self.pixmap.width() == 100 and pix_x - x < 0:
                x = int(self.x())
                pix_x = x

            if self.pixmap.height() == 100 and pix_y - y < 0:
                y = int(self.y())
                pix_y = y

            self.pixmap = QPixmap(self.image).scaled(QSize(pix_x - x + pix_width, pix_y - y + pix_height), Qt.IgnoreAspectRatio)
            self.setPixmap(self.pixmap)
            self.setX(x)
            self.setY(y)
            self.flip_checker("left", "top")
        if anchor.location == "topRight":

            if self.pixmap.width() == 100 and x - (pix_x + pix_width) < 0:
                x = int(self.x())
                pix_x = x - pix_width

            if self.pixmap.height() == 100 and pix_y - y < 0:
                y = int(self.y())
                pix_y = y

            self.pixmap = QPixmap(self.image).scaled(QSize(x - (pix_x + pix_width) + pix_width, pix_y - y + pix_height), Qt.IgnoreAspectRatio)
            self.setPixmap(self.pixmap)
            self.setY(y)
            self.flip_checker("right", "top")
        if anchor.location == "bottomRight":

            if self.pixmap.width() == 100 and x - (pix_x + pix_width) < 0:
                x = int(self.x())
                pix_x = x - pix_width

            if self.pixmap.height() == 100 and y - (pix_y + pix_height) < 0:
                y = int(self.y())
                pix_y = y - pix_height

            self.pixmap = QPixmap(self.image).scaled(QSize(x - (pix_x + pix_width) + pix_width, y - (pix_y + pix_height) + pix_height), Qt.IgnoreAspectRatio)
            self.setPixmap(self.pixmap)
            self.flip_checker("right", "bottom")
        if anchor.location == "bottomLeft":

            if self.pixmap.width() == 100 and pix_x - x < 0:
                x = int(self.x())
                pix_x = x

            if self.pixmap.height() == 100 and y - (pix_y + pix_height) < 0:
                y = int(self.y())
                pix_y = y - pix_height

            self.pixmap = QPixmap(self.image).scaled(QSize(pix_x - x + pix_width, y - (pix_y + pix_height) + pix_height), Qt.IgnoreAspectRatio)
            self.setPixmap(self.pixmap)
            self.setX(x)
            self.flip_checker("left", "bottom")

        self.update_anchors()

    def flip_checker(self, side1=None, side2=None):

        if self.pixmap.width() < 100:
            self.pixmap = QPixmap(self.image).scaled(100, self.pixmap.height())
            self.setPixmap(self.pixmap)

        if self.pixmap.height() < 100:
            self.pixmap = QPixmap(self.image).scaled(self.pixmap.width(), 100)
            self.setPixmap(self.pixmap)

        if self.pixmap.width() == 0 and self.pixmap.height() == 0:
            self.pixmap = QPixmap(self.image).scaled(100, 100)


class BlueprintAnchor(QGraphicsRectItem):

    def __init__(self, parent, location, properties):

        super().__init__(parent=parent)

        self.location = location

        self.setRect(properties[0])
        self.setCursor(properties[1])
        self.setOpacity(1)
        self.setZValue(6)
        self.setVisible(False)

        self.setBrush(QBrush(QColor("black")))

    def mousePressEvent(self, event):
        return

    def mouseMoveEvent(self, event):
        self.parentItem().anchor_drag(self, event.scenePos())


class TabWidget(QGraphicsView):

    def __init__(self, path, model, window):

        super().__init__()

        # Setup
        self.mainwindow = window
        canvas = Canvas(path, model=model)
        scene = GraphicsScene(self, canvas)
        scene.setObjectName(path.split('\\')[-1])

        self.setScene(scene)
        self.setCursor(Qt.CrossCursor)

        self.transform_func = QTransform()
        self.div = 0
        self.zoom = 0
        self.flipped = False
        self.mirrored = False
        self.rotation = 0
        self.shift = QPoint()
        self.start = QPoint()
        self.finish = QPoint()
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.points = None
        self.blueprint = None
        self.current_el = []
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Pin stuff
        self.buffer_size = QSize()
        self.reference_size = QSize(10, 10)
        self.x_alignment = False
        self.y_alignment = False
        self.ai_rotation = None

    def change_alignment(self, r: str):

        if r == 'x':

            self.x_alignment = not self.x_alignment

        else:

            self.y_alignment = not self.y_alignment

    def leaveEvent(self, event):

        if self.mainwindow.mod == "ZOOM":
            [self.scene().removeItem(it) for it in self.items() if type(it) == QGraphicsRectItem]

    def keyPressEvent(self, event):

        if event.key() == Qt.Key_Delete:

            try:

                for item in self.current_el:

                    self.scene().removeItem(item.sl)
                    self.scene().removeItem(item)

                    if type(item) == SimpleRect:

                        self.mainwindow.TreeListWidget.findItems(item.object_name, Qt.MatchExactly)[0].change_status(
                            False)

                    else:

                        try:

                            l_item = self.mainwindow.TreeListWidget.findItems(item.object_name.split("_")[0], Qt.MatchExactly)[0]
                            l_item.child(int(item.object_name.split("_")[-1]) - 1).change_status(False)

                        except AttributeError:

                            continue

            except Exception as ex:

                logging.critical(f"{type(ex)}; Wrong item delete event; widget: {type(self)}; py: {ex}")

        self.current_el.clear()

        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_T and self.blueprint:

            self.blueprint.setAdjustable(True)

        if event.key() == Qt.Key_Escape or event.key() == Qt.Key_Return:

            self.start, self.finish = QPoint(), QPoint()

            if self.items():

                [self.scene().removeItem(it) for it in self.items() if type(it) == QGraphicsRectItem]

            if self.blueprint:

                self.blueprint.setAdjustable(False)

        if event.key() == Qt.Key_L:

            self.detect()

    def detect(self):

        import json
        import os

        scene = self.scene()

        # Blueprint recognition
        if os.path.exists(f"{self.scene().canvas.path.removesuffix('.' + self.scene().canvas.path.split('.')[-1])}.json"):

            with open(f"{self.scene().canvas.path.removesuffix('.' + self.scene().canvas.path.split('.')[-1])}.json",
                      'r') as ff:

                rects = json.loads(ff.read())

        else:

            rects = preparate(self.scene().canvas.path)
            tab_widget = self.mainwindow.add_image(
                self.scene().canvas.path.removesuffix(self.scene().canvas.path.split('\\')[-1]) + 'cropped_' +
                self.scene().canvas.path.split('\\')[-1])
            self.mainwindow.BlueprintTabWidget.setCurrentWidget(tab_widget)
            scene = tab_widget.scene()

            rects = self.verify_rects(rects)

        self.unpack_rects(rects, scene)

    def verify_rects(self, rects) -> dict:

        scene = self.mainwindow.BlueprintTabWidget.currentWidget().scene()
        view = self.mainwindow.BlueprintTabWidget.currentWidget()
        rectlist = rects

        dialog = VerifyDialog(view, scene, rectlist)
        pos = self.mapToGlobal(self.pos())
        dialog.move(pos.x() + 10, pos.y() + 10)
        dialog.exec()

        return rectlist

    def unpack_rects(self, rects, scene):

        for point in rects['shapes']:
            coord = point['points']

            rect_f = QRectF(

                coord[0][0],
                coord[0][1],
                abs(coord[0][0] - coord[1][0]),
                abs(coord[0][1] - coord[1][1])

            )

            try:

                name = point['label'].split('-')[-1]

            except IndexError:

                continue

            try:

                item = self.mainwindow.TreeListWidget.findItems(point['label'].split('-')[-1].upper(), Qt.MatchExactly, 0)[0]

            except IndexError:

                continue

            rect = SimpleRect(x_start=rect_f.x(),
                              y_start=rect_f.y(),
                              x_finish=rect_f.width() + rect_f.x(),
                              y_finish=rect_f.height() + rect_f.y(),
                              object_name=name,
                              mod='AXE')

            if point['description'] == 'micro':

                scene.addItem(rect)

                if item:

                    item.child(0).changeStatus(2)

            elif point['description'] == 'text on micro':

                scene.addItem(rect)

                if item:

                    item.child(1).changeStatus(2)

            if point['shape_type'] == 'circle':

                ellipse = SimpleRect(x_start=rect_f.x(),
                                     y_start=rect_f.y(),
                                     x_finish=rect_f.width() + rect_f.x(),
                                     y_finish=rect_f.height() + rect_f.y(),
                                     object_name=name,
                                     mod='AXE')

                scene.addItem(ellipse)

                if item:

                    item.child(2).changeStatus(2)

    def resize_selected(self, size: QSizeF):

        for el in self.current_el:

            if type(el) == SimplePoint:

                el.setRect(el.rect().x(), el.rect().y(), size.width(), size.height())
                el.update_anchors()

    def move_selected(self, x, y, ex: QGraphicsRectItem):

        for el in self.current_el:

            if type(el) == SimplePoint and el != ex:

                el.setRect(el.rect().x() + x, el.rect().y() + y, el.rect().width(), el.rect().height())
                el.update_anchors()

    def align_horizontal(self, x):

        for el in self.current_el:

            if type(el) == SimplePoint:

                el.setRect(x, el.rect().y(), el.rect().width(), el.rect().height())
                el.update_anchors()

    def align_vertical(self, y):

        for el in self.current_el:

            if type(el) == SimplePoint:

                el.setRect(el.rect().x(), y, el.rect().width(), el.rect().height())
                el.update_anchors()

    def mousePressEvent(self, event):

        if self.blueprint and self.blueprint.adjustable and self.itemAt(event.pos()) in [GraphicsBlueprintItem, BlueprintAnchor]:

            super().mousePressEvent(event)
            return

        elif self.blueprint and self.blueprint.adjustable and type(self.itemAt(event.pos())) not in [GraphicsBlueprintItem, BlueprintAnchor]:

            self.blueprint.setAdjustable(False)

        if self.mainwindow.mod == 'STD' and event.button() == Qt.LeftButton:
            self.start = self.mapToScene(event.pos())
            self.finish = self.start

        self.mainwindow.cur_view = self
        self.mainwindow.check_items()

        if type(self.itemAt(event.pos())) in [QGraphicsPixmapItem, GraphicsBlueprintItem]:

            if event.button() == Qt.LeftButton:

                if self.mainwindow.mod == "AI":

                    if type(self.mainwindow.TreeListWidget.currentItem()) == TreeWidgetChild and (event.modifiers() != Qt.AltModifier and event.modifiers() != Qt.ControlModifier):

                        self.mainwindow.log("Can't place pins in AI mode, change current item or mode!")
                        return

                    else:

                        self.start = self.mapToScene(event.pos())
                        self.finish = self.start

                elif self.mainwindow.mod == "AXE":

                    self.start = self.mapToScene(event.pos())
                    self.finish = self.start

                elif self.mainwindow.mod == "CROP":

                    self.start = self.mapToScene(event.pos())
                    self.finish = self.start

            elif event.button() == Qt.RightButton:

                if self.blueprint and self.blueprint.visible:
                    self.blueprint.setVisible(False)

                _event = QMouseEvent(event.type(), event.pos(), Qt.LeftButton, Qt.LeftButton, event.modifiers())
                self.setDragMode(QGraphicsView.ScrollHandDrag)
                super().mousePressEvent(_event)
                event.accept()

        elif event.buttons() == Qt.RightButton | Qt.LeftButton:
            [self.scene().removeItem(it) for it in self.items() if type(it) == QGraphicsRectItem]
            [self.scene().removeItem(item) for item in self.scene().items() if isinstance(item, CropItem)]
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):

        if event.buttons() == Qt.LeftButton and self.mainwindow.mod == 'STD':

            if not self.start.isNull() and not self.finish.isNull():
                self.finish = self.mapToScene(event.pos())
                [self.scene().removeItem(item) for item in self.scene().items() if isinstance(item, CropItem)]

                self.cropItem = CropItem(self.scene().pic, self.start, self.mapToScene(event.pos()))
                self.cropItem.setBrush(QBrush(QColor(10, 0, 0, 80)))
                pen = QPen()
                pen.setColor(QColor(Qt.white))
                pen.setStyle(Qt.DotLine)
                self.cropItem.setPen(pen)

        if self.mainwindow.mod == "ZOOM":

            if self.items():
                [self.scene().removeItem(it) for it in self.items() if type(it) == QGraphicsRectItem]

            center = self.mapToScene(event.pos())

            kx, ky = self.sceneRect().width() / 10, self.sceneRect().height() / 10

            rect = QGraphicsRectItem(center.x() - kx / 2, center.y() - ky / 2, kx, ky)
            self.scene().addItem(rect)
            return

        elif self.mainwindow.mod in ["AXE", "CROP", "AI"]:

            if self.mainwindow.mod in ["AXE", "AI"] and type(
                    self.mainwindow.TreeListWidget.currentItem()) == TreeWidgetChild:
                super().mouseMoveEvent(event)

            if not self.start.isNull() and not self.finish.isNull():

                self.finish = self.mapToScene(event.pos())

                if self.items():
                    [self.scene().removeItem(it) for it in self.items() if type(it) == QGraphicsRectItem]

                start_x = min(self.start.x(), self.finish.x())
                start_y = min(self.start.y(), self.finish.y())
                finish_x = abs(self.finish.x() - self.start.x())
                finish_y = abs(self.finish.y() - self.start.y())

                rect = QGraphicsRectItem(start_x, start_y, finish_x, finish_y)
                self.scene().addItem(rect)

                if self.mainwindow.mod == "AI" and (event.modifiers() != Qt.AltModifier and event.modifiers() != Qt.ControlModifier):

                    if self.rotation not in [90, 270]:

                        if (self.start.x() > self.finish.x() and self.start.y() < self.finish.y()) or (self.start.x() < self.finish.x() and self.start.y() > self.finish.y()):

                            # Horizontal
                            circ_rect = QGraphicsRectItem(QRectF(
                                start_x, start_y + (finish_y * 0.15),
                                finish_x, finish_y - (finish_y * 0.3)
                            ))

                            self.ai_rotation = 1

                        else:

                            # Vertical
                            circ_rect = QGraphicsRectItem(QRectF(
                                start_x + (finish_x * 0.15), start_y,
                                finish_x - (finish_x * 0.3), finish_y
                            ))

                            self.ai_rotation = 2

                        circ_rect.setPen(QPen(Qt.red, 2))
                        self.scene().addItem(circ_rect)

                    else:

                        if (self.start.x() > self.finish.x() and self.start.y() < self.finish.y()) or (
                                self.start.x() < self.finish.x() and self.start.y() > self.finish.y()):

                            # Horizontal
                            circ_rect = QGraphicsRectItem(QRectF(
                                start_x, start_y + (finish_y * 0.15),
                                finish_x, finish_y - (finish_y * 0.3)
                            ))

                            self.ai_rotation = 1

                        else:

                            # Vertical
                            circ_rect = QGraphicsRectItem(QRectF(
                                start_x + (finish_x * 0.15), start_y,
                                finish_x - (finish_x * 0.3), finish_y
                            ))

                            self.ai_rotation = 2

                        circ_rect.setPen(QPen(Qt.red, 2))
                        self.scene().addItem(circ_rect)

                return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):

        if event.button() == Qt.LeftButton and self.mainwindow.mod == 'STD':
            self.scene().removeItem(self.cropItem)

        if event.button() == Qt.LeftButton:

            self.points = np.array([self.start.x(),
                                    self.start.y(),
                                    self.finish.x(),
                                    self.finish.y()]).astype('int16')

            if self.mainwindow.mod in ["AXE", "AI"] and self.start == self.finish and \
                    type(self.itemAt(event.pos())) in [QGraphicsPixmapItem, GraphicsBlueprintItem]:

                for item in self.current_el:

                    if item.object_name.split('_')[-1] != '1':

                        pen = QPen()
                        pen.setColor(QColor("#11ab22"))
                        pen.setWidth(2)
                        item.setPen(pen)

                self.current_el.clear()

            if self.mainwindow.mod == "ZOOM":

                self.transform_func.scale(1.2, 1.2)
                self.setTransform(self.transform_func)

            elif self.mainwindow.mod in ["AXE", "AI"] and (event.modifiers() == Qt.AltModifier or event.modifiers() == Qt.ControlModifier):

                if self.start == self.finish:

                    self.start = QPoint()
                    self.finish = QPoint()

                    return

                start_x = min(self.start.x(), self.finish.x())
                start_y = min(self.start.y(), self.finish.y())
                finish_x = abs(self.finish.x() - self.start.x())
                finish_y = abs(self.finish.y() - self.start.y())

                rect = QRectF(start_x, start_y, finish_x, finish_y)

                if event.modifiers() != Qt.ControlModifier:

                    for item in self.current_el:

                        if item.object_name.split('_')[-1] != '1':

                            pen = QPen()
                            pen.setColor(QColor("#11AB22"))
                            pen.setWidth(2)
                            item.setPen(pen)

                    self.current_el.clear()

                [item.set_current(True) for item in self.scene().items(rect) if type(item) in [SimpleRect, SimplePoint]]

                [self.scene().removeItem(it) for it in self.items() if type(it) == QGraphicsRectItem]

            elif self.mainwindow.mod == "AI":

                if self.start == self.finish:

                    self.start = QPoint()
                    self.finish = QPoint()

                    return

                try:

                    dots = self.scene().canvas.pins2json(self.points, confidence=0.25, rotation=self.ai_rotation)

                except RuntimeWarning:

                    self.mainwindow.log("Error: no points found")
                    [self.scene().removeItem(it) for it in self.items() if type(it) == QGraphicsRectItem]
                    self.start = QPoint()
                    self.finish = QPoint()
                    return

                except Exception:

                    self.mainwindow.log("Error: unknown error")
                    [self.scene().removeItem(it) for it in self.items() if type(it) == QGraphicsRectItem]
                    self.start = QPoint()
                    self.finish = QPoint()
                    return

                # Add rect
                name = self.mainwindow.TreeListWidget.currentItem().text(0)

                rect = SimpleRect(self.start.x(), self.start.y(), self.finish.x(), self.finish.y(),
                                  object_name=name, mod=self.mainwindow.mod, visible_status=self.mainwindow.bodies_status, ai_rotation=self.ai_rotation)

                self.scene().addItem(rect)

                # Add pins

                pins = []
                if self.ai_rotation == 2:

                    for num, point in enumerate(dots):
                        name = f'{self.mainwindow.TreeListWidget.currentItem().text(0)}_{num + 1}'
                        pin = SimplePoint(point, object_name=name, visible_status=self.mainwindow.pins_status, rotation=self.ai_rotation)
                        self.scene().addItem(pin)
                        pins.append(pin)

                else:

                    for num, point in enumerate(dots):

                        name = f'{self.mainwindow.TreeListWidget.currentItem().text(0)}_{num + 1}'

                        pin = SimplePoint(point, object_name=name, visible_status=self.mainwindow.pins_status, rotation=self.ai_rotation)

                        c = QPointF(
                            abs(rect.rect().x() + (rect.rect().width() / 2)),
                            abs(rect.rect().y() + (rect.rect().height() / 2))
                        )

                        pin.setRect(rotate_rect(pin.rect(), c, 90))

                        self.scene().addItem(pin)
                        pins.append(pin)

                [self.scene().removeItem(it) for it in self.items() if type(it) == QGraphicsRectItem]
                self.mainwindow.log(f"Placed element: {self.mainwindow.TreeListWidget.currentItem().text(0)}")

                dialog = ConfDialog(pins=pins, parent_rect=rect, view=self)
                dialog.move(self.mapToGlobal(QPoint(self.pos().x(), self.pos().y())))
                dialog.exec()

                if dialog.status:

                    dialog.pins.append(rect)
                    self.mainwindow.next_item(dialog.pins)

                else:

                    self.scene().removeItem(rect)

            elif self.mainwindow.mod == "AXE":

                name = self.mainwindow.TreeListWidget.currentItem().text(0).replace(" ✓", "")

                if type(self.mainwindow.TreeListWidget.currentItem()) == TreeWidgetItem and self.start != self.finish:

                    [self.scene().removeItem(it) for it in self.items() if
                     type(it) == SimpleRect and it.object_name == name]

                    rect = SimpleRect(self.start.x(), self.start.y(), self.finish.x(), self.finish.y(),
                                      object_name=name, mod=self.mainwindow.mod, visible_status=self.mainwindow.bodies_status)

                    self.scene().addItem(rect)
                    self.mainwindow.log(f"Placed body: {name}")
                    self.mainwindow.next_item(rect)

                else:

                    if type(self.itemAt(event.pos())) in [QGraphicsPixmapItem, GraphicsBlueprintItem] and \
                            type(self.mainwindow.TreeListWidget.currentItem()) == TreeWidgetChild:

                        first_name = name.split('_')[0]
                        x = -1
                        y = -1

                        for item in self.scene().items():
                            if isinstance(item, SimplePoint):
                                if first_name in item.object_name:
                                    width, height = item.rect().width(), item.rect().height()
                                    x, y = item.rect().x(), item.rect().y()
                                    break

                        if 'width' not in locals() and 'height' not in locals():
                            width, height = self.reference_size.width(), self.reference_size.height()

                        for it in self.scene().items():
                            if isinstance(it, SimplePoint):
                                if it.object_name.split('_')[0] == first_name:
                                    if int(it.object_name.split('_')[-1]) >= int(name.split('_')[-1]):
                                        it.object_name = first_name + '_' + str(
                                            int(it.object_name.split('_')[-1]) + 1)

                        [self.scene().removeItem(it) for it in self.items() if type(it) == SimplePoint \
                         and it.object_name == name]

                        if x >= 0 and (abs((self.finish.x() - (width / 2)) - x) <= 30) and self.x_alignment:
                            rect = SimplePoint(
                                    (x, self.finish.y() - (height / 2), width, height),
                                    object_name=name,
                                    visible_status=self.mainwindow.pins_status)

                            self.scene().addItem(rect)

                        elif y >= 0 and (abs((self.finish.y() - (height / 2)) - y) <= 30) and self.y_alignment:

                            rect = SimplePoint(
                                    (self.finish.x() - (width / 2), y, width, height),
                                    object_name=name,
                                    visible_status=self.mainwindow.pins_status)

                            self.scene().addItem(rect)

                        else:

                            rect = SimplePoint(
                                    (self.finish.x() - (width / 2), self.finish.y() - (height / 2), width, height),
                                    object_name=name,
                                    visible_status=self.mainwindow.pins_status)

                            self.scene().addItem(rect)

                        [self.scene().removeItem(it) for it in self.items() if type(it) == QGraphicsRectItem]

                        self.mainwindow.log(f"Placed point: {name}")
                        self.mainwindow.next_item(rect)

            elif self.mainwindow.mod == 'CROP':

                self.fitInView(min(self.start.x(), self.finish.x()),
                               min(self.start.y(), self.finish.y()),
                               np.abs(self.start.x() - self.finish.x()),
                               np.abs(self.start.y() - self.finish.y()),
                               Qt.KeepAspectRatio)

                self.transform_func = self.transform()

                [self.scene().removeItem(it) for it in self.items() if type(it) == QGraphicsRectItem]

        elif event.button() == Qt.RightButton:

            if self.mainwindow.mod == 'ZOOM':

                self.transform_func.scale(0.8, 0.8)
                self.setTransform(self.transform_func)

            else:

                if self.items():
                    [self.scene().removeItem(it) for it in self.items() if type(it) == QGraphicsRectItem]

                _event = QMouseEvent(event.type(), event.pos(), Qt.LeftButton, Qt.LeftButton, event.modifiers())
                super().mouseReleaseEvent(_event)
                event.accept()
                self.setDragMode(QGraphicsView.NoDrag)
                if self.blueprint and self.blueprint.visible:
                    self.blueprint.setVisible(True)

        self.start = QPoint()
        self.finish = QPoint()
        super().mouseReleaseEvent(event)

    def buffer(self, size: QSize):

        self.buffer_size = size

    def reference(self, size: QSize):

        self.reference_size = size

    def wheelEvent(self, event) -> None:
        """Мастабирование с помощью колеса мыши внезависимости от режима"""

        if event.modifiers() == Qt.ControlModifier:
            scale = 1 + event.angleDelta().y() / 1200
            self.transform_func.scale(scale, scale)
            # self.zoom += event.angleDelta().y()
            # Раскоментировать, если вкл. не отдалять дальше исходного размера
            # if self.zoom < 0:
            #     self.resetTransform()
            #     self.transform_func = QTransform()
            #     self.zoom = 0
            #     return
            self.setTransform(self.transform_func)

        else:

            super().wheelEvent(event)
