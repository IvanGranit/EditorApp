import re

import numpy as np
from PIL import Image, ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True


class Canvas:

    def __init__(self, path=None, model=None):

        self.path = path
        self.image = self.read_image(self.path)

        self.index = self.get_index()
        self.model = model

    @staticmethod
    def read_image(path: str):
        img = Image.open(path)
        return np.asarray(img)[:, :, ::-1]

    def get_index(self):

        with open(self.path, 'rb') as f:
            image_bytes = bytearray(f.read())
        indexes = re.findall('{"ID" : (\d+)}', str(image_bytes))
        del image_bytes
        if indexes:
            return indexes[-1]
        else:
            return None

    def pins2json(self, coordinates: np.array, confidence=0.25):
        """Функция генерации координат пинов.

        На выходе создается отсортированный массив вида:
        [[LeftTop_x, LeftTop_y],
        ....
         [LeftTop_x, LeftTop_y]]

        Порядок элементов в массиве соответствует номеру вывода микросхемы

        Первый пин определеяется в зависимости от угла нажатия при выделении объекта (выделение объекта начиная с левого
        вехнего угла будет означать, что первый пин находится в левом верхнем углу"""

        # Coordinates: 1 - horizontal min, 2 - vertical min, 3 - horizontal max, 4 - vertical max
        y1, x1, y2, x2 = coordinates
        middle = abs((y1 - y2) / 2) + min(y1, y2)

        crop_img = self.image[min(x1, x2):max(x1, x2), min(y1, y2):max(y1, y2), :]
        #   Сохраняем исходные размерности изображения
        # width, height = crop_img.shape[:2]

        #   Так как нейронная сеть работает с изображениями 256х256, изменяем размерность изображения
        # crop_img = cv2.resize(crop_img, (256, 256))

        #   Определяем коэффициенты для корректировки итоговых координат пинов
        # kx, ky = width / 256, height / 256

        #   Сегментируем изобраэжение

        bboxes = self.model.predict(crop_img, iou=0.001, conf=confidence)[0].boxes.xywh.numpy()

        bboxes[:, 0] = bboxes[:, 0] - bboxes[:, 2] // 2 + min(y1, y2)
        bboxes[:, 2] = bboxes[:, 2]
        bboxes[:, 1] = bboxes[:, 1] - bboxes[:, 3] // 2 + min(x1, x2)
        bboxes[:, 3] = bboxes[:, 3]

        avg_width = int(bboxes[:, 2].mean())
        avg_height = int(bboxes[:, 3].mean())
        avg_left = bboxes[bboxes[:, 0] < middle][:, 0].mean()
        avg_right = bboxes[bboxes[:, 0] > middle][:, 0].mean()

        bboxes[:, 2] = avg_width
        bboxes[:, 3] = avg_height
        bboxes[:, 0] = np.where(bboxes[:, 0] < middle, avg_left, avg_right)

        # Мод = 'rb'
        if x1 > x2 and y1 > y2:
            rectangles = sorted(bboxes[bboxes[:, 0] > middle], key=lambda x: x[1], reverse=True) + \
                         sorted(bboxes[bboxes[:, 0] < middle], key=lambda x: x[1])

        #   Мод = 'lt'
        if x1 < x2 and y1 < y2:
            rectangles = sorted(bboxes[bboxes[:, 0] < middle], key=lambda x: x[1]) + \
                         sorted(bboxes[bboxes[:, 0] > middle], key=lambda x: x[1], reverse=True)

        return rectangles
