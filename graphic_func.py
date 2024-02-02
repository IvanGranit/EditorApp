from PyQt5.QtCore import *

import math


def rotate_rect(rect, c: QPointF, deg=90):

    deg %= 360

    if deg % 90 != 0:

        return

    rad = math.radians(deg)

    vertices = [
        QPointF(rect.x(), rect.y()),
        QPointF(rect.x() + rect.width(), rect.y()),
        QPointF(rect.x() + rect.width(), rect.y() + rect.height()),
        QPointF(rect.x(), rect.y() + rect.height())
    ]

    cx, cy = c.x(), c.y()

    for point in vertices:

        x, y = point.x(), point.y()
        cos, sin = math.cos(rad), math.sin(rad)
        adjusted_x, adjusted_y = x - cx, y - cy

        new_x = cx + cos * adjusted_x + sin * adjusted_y
        new_y = cy + -sin * adjusted_x + cos * adjusted_y

        point.setX(new_x)
        point.setY(new_y)

    minx, miny, maxx, maxy = vertices[0].x(), vertices[0].y(), vertices[0].x(), vertices[0].y()

    for point in vertices[1:4]:

        minx = min(minx, point.x())
        miny = min(miny, point.y())
        maxx = max(maxx, point.x())
        maxy = max(maxy, point.y())

    return QRectF(minx, miny, maxx-minx, maxy-miny)
