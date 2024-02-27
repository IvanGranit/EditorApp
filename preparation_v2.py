import cv2
import numpy
import numpy as np
import matplotlib.pyplot as plt
import math

from recognize import recognize

# from imutils.object_detection import non_max_suppression
# from mpl_toolkits.axes_grid1 import ImageGrid

plt.rcParams['figure.figsize'] = [15, 10]


# удаление наклонных линий
def isAroundAxes(rad, eps=10 * np.pi / 180):
    r = abs(rad)
    return r < eps or abs(np.pi - r) < eps or abs(np.pi / 2 - r) < eps


def remove_lines(bin_img, size=10, eps=10 * np.pi / 180):
    h, w = bin_img.shape
    mask = np.ones((h, w), np.uint8) * 255
    linesP = cv2.HoughLinesP(bin_img, 1, np.pi / 180, 50, None, 150, 10)

    remove_lines = []
    add_lines = []

    if linesP is not None:
        for l in linesP:
            l = l[0]
            # value is between PI and -PI.
            t = math.atan2(l[3] - l[1], l[2] - l[0])
            if not isAroundAxes(t, eps):
                remove_lines.append(l)
            else:
                add_lines.append(l)
    for l in remove_lines:
        cv2.line(mask, (l[0], l[1]), (l[2], l[3]), (0, 0, 0), size, cv2.LINE_AA)
    for l in add_lines:
        cv2.line(mask, (l[0], l[1]), (l[2], l[3]), (255, 255, 255), size, cv2.LINE_AA)

    return cv2.bitwise_and(bin_img, bin_img, mask=mask)


def createKernel(sx, sy, k=0.5):
    kernel = np.ones((sx, sy), 'float32')
    sx_2 = sx // 2
    sy_2 = sy // 2

    for j in range(sy):
        if j == sy_2:
            continue
        for i in range(sx_2):
            v = k / (sx_2 - i)
            kernel[i][j] *= v
            kernel[sx - 1 - i][j] *= v

    for i in range(sx):
        if i == sx_2:
            continue
        for j in range(sy_2):
            v = k / (sy_2 - j)
            kernel[i][j] *= v
            kernel[i][sy - 1 - j] *= v
    return kernel


def remove_contour(bin_img, contour, size=10):
    h, w = bin_img.shape
    mask = np.ones((h, w), np.uint8) * 255

    # contour
    cv2.drawContours(mask, [contour], -1, (0, 0, 0), size)

    return cv2.bitwise_and(bin_img, bin_img, mask=mask)


def remove_circles(bin_img, circles, size=10):
    if circles is None:
        return bin_img

    h, w = bin_img.shape
    mask = np.ones((h, w), np.uint8) * 255

    # convert the (x, y) coordinates and radius of the circles to integers
    circles = np.round(circles[0, :]).astype("int")

    # loop over the (x, y) coordinates and radius of the circles
    for (x, y, r) in circles:
        # draw the circle in the output image, then draw a rectangle
        # corresponding to the center of the circle
        cv2.circle(mask, (x, y), r, (0, 0, 0), size)

    return cv2.bitwise_and(bin_img, bin_img, mask=mask)


def crop_image(bin_img, epsMinArea=0.05):
    w = bin_img.shape[0]
    h = bin_img.shape[1]
    minArea = epsMinArea * w * h

    maxBlock = None
    maxArea = minArea

    contours, _ = cv2.findContours(bin_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for i, contour in enumerate(contours):
        _, _, wc, hc = cv2.boundingRect(contour)
        area = wc * hc
        if area > maxArea:
            maxArea = area
            maxBlock = i

    # обрезаем по схеме
    return cv2.boundingRect(contours[maxBlock]), contours[maxBlock]


def filterContoursByMinArea(contours, hierarchy, minArea, eps=0.5):
    fContours = []
    pRect = []
    for i, cnt in enumerate(contours):
        # Check if it is an external contour and its area is more than minArea
        area = cv2.contourArea(cnt)
        x, y, w, h = cv2.boundingRect(cnt)
        rect_area = w * h
        p = abs(rect_area - area)
        if minArea < area and p < eps * rect_area:
            fContours.append(cnt)
            pRect.append(1 - p / float(rect_area))
    return fContours, pRect


def removeSamePoints(contour, eps_cos_180=-0.6, eps_cos_90=0.05, eps_len=5):
    x, y, w, h = cv2.boundingRect(contour)

    res = [p for p in contour]  # [20:45]

    t = [np.array([p[0][0] - x, p[0][1] - y]) for p in res]

    i = 0
    while i < len(res):
        j = (i - 1) % len(res)
        k = (i + 1) % len(res)
        ik = res[k][0] - res[i][0]
        len_ik = np.linalg.norm(ik)
        ik = ik.astype('float') / len_ik

        ij = res[j][0] - res[i][0]
        len_ij = np.linalg.norm(ij)
        ij = ij.astype('float') / len_ij

        tj, ti, tk = t[j], t[i], t[k]
        cos_jik = np.dot(ij, ik)

        skipped = cos_jik < eps_cos_180

        if skipped:
            # remove i from contour
            del res[i]
        elif abs(cos_jik) < eps_cos_90:
            if len_ik < eps_len:
                if k == 1:
                    j -= 1
                del res[k]
            if len_ij < eps_len:
                del res[j]
                i -= 1
            i += 1
        else:
            i += 1

    return np.array(res)


refvec = [0, 1]


def clockwiseangle_and_distance(point, origin):
    # Vector between point and the origin: v = p - o
    vector = [point[0] - origin[0], point[1] - origin[1]]
    # Length of vector: ||v||
    lenvector = math.hypot(vector[0], vector[1])
    # If length is zero there is no angle
    if lenvector == 0:
        return -math.pi, 0
    # Normalize vector: v/||v||
    normalized = [vector[0] / lenvector, vector[1] / lenvector]
    dotprod = normalized[0] * refvec[0] + normalized[1] * refvec[1]  # x1*x2 + y1*y2
    diffprod = refvec[1] * normalized[0] - refvec[0] * normalized[1]  # x1*y2 - y1*x2
    angle = math.atan2(diffprod, dotprod)
    # Negative angles represent counter-clockwise angles so we need to subtract them
    # from 2*pi (360 degrees)
    if angle < 0:
        return 2 * math.pi + angle, lenvector
    # I return first the angle because that's the primary sorting criterium
    # but if two vectors have the same angle then the shorter distance should come first.
    return angle, lenvector


def isRect(contour, eps_rect_area):
    area = cv2.contourArea(contour)
    x, y, w, h = cv2.boundingRect(contour)
    rect_area = w * h
    return abs(rect_area - area) < eps_rect_area * rect_area


# крест
def isCross(contour, eps_rect_area=0.05, eps_radius_center=5, canvas=None):
    # горизонтальный прямоугольник
    fcntX = sorted(contour, key=lambda x: x[0][0])
    fcntX = np.array(fcntX[:2] + fcntX[-2:])
    x, y, w, h = cv2.boundingRect(fcntX)

    cByX = np.array([x + w / 2., y + h / 2.])
    fcntX = np.array(sorted(fcntX, key=lambda x: clockwiseangle_and_distance(x[0], cByX)))

    y0, h0 = y, h

    cross_area = cv2.contourArea(fcntX)

    # вертикальный прямоугольник
    fcntY = sorted(contour, key=lambda x: x[0][1])
    fcntY = fcntY[:2] + fcntY[-2:]
    fcntY = np.array(fcntY)

    x, y, w, h = cv2.boundingRect(fcntY)
    cByY = np.array([x + w / 2., y + h / 2.])
    fcntY = np.array(sorted(fcntY, key=lambda x: clockwiseangle_and_distance(x[0], cByY)))

    x0, w0 = x, w

    cross_area += cv2.contourArea(fcntY) - w0 * h0

    # равенство центров прямоугольников + равенство площади
    area = cv2.contourArea(contour)

    if canvas is not None:
        cv2.drawCountors(canvas, [fcntX, fcntY])

    if abs(cross_area - area) > eps_rect_area * cross_area:
        return False

    return np.linalg.norm(cByX - cByY) < eps_radius_center


def isChipContour(contour, eps_approx=0.01, eps_rect_area=0.05, eps_cross_area=0.05, eps_radius_center=5):
    # calc arclentgh
    arclen = cv2.arcLength(contour, True)

    # грубо аппроксимируем -> убируем шум
    epsilon = arclen * eps_approx
    approx = cv2.approxPolyDP(contour, epsilon, True)

    # прямоугольник
    if len(approx) == 4:
        return isRect(contour, eps_rect_area)

    # крест
    elif len(approx) == 12:
        # return True
        # canvas=img_contours
        return isCross(approx)  # , 0.21, eps_radius_center)

    return False


def findPin(elem, th=10):
    h2 = elem.shape[0] // 2
    w2 = elem.shape[1] // 2

    maxN = -1
    possiblePin = (0, 0)
    for pin, part in [
        ((0, 0), elem[:h2, :w2]),
        ((0, 1), elem[:h2, w2:]),
        ((1, 1), elem[h2:, w2:]),
        ((1, 0), elem[h2:, :w2])
    ]:
        n = np.sum(part > th)
        # print(n)
        if n > maxN:
            maxN = n
            possiblePin = pin

    return possiblePin


def normalizeWord(word):
    for old, new in [
        ('a', '0'),
        ('b', 'D'),
        ('c', '6'),
        # d
        ('e', '8'),
        ('f', '9'),
        ('g', '9'),
        ('h', '6'),
        ("i", "1"),
        ("j", "1"),
        ("k", "1"),
        ("l", "1"),
        ("m", "m"),
        ("n", "0"),
        ("o", "0"),
        ("p", "8"),
        ("q", "9"),
        ("r", "6"),
        ('s', '5'),
        ('t', '4'),
        ('u', '4'),
        ('v', '0'),
        ('w', 'w'),
        ('x', 'x'),
        ('y', '4'),
        ('z', '2'),
    ]:
        word = word.replace(old, new)
    if len(word) > 0:
        if word[0] == '0':
            word = "D" + word[1:]
        elif word[0] in "123456789":
            word = "D" + word
    return word


def main_e(image):
    img = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    img_filter = img.copy()

    _, tresh = cv2.threshold(img_filter, 0, 255, cv2.THRESH_OTSU)
    tresh = cv2.bitwise_not(tresh)

    # проверить необходимость использования
    kernel = createKernel(3, 3, k=0.1)
    dilate_tresh = cv2.dilate(tresh, kernel, 5)

    (x, y, w, h), contour = crop_image(dilate_tresh)

    # обрезать и удалить контур
    cropped_image = image[y:y + h, x:x + w]
    cropped_tresh = remove_contour(dilate_tresh, contour, size=30)[y:y + h, x:x + w]

    # удалить наклонные линии
    cropped_tresh_lines = remove_lines(cropped_tresh, size=10)

    h, w = cropped_tresh.shape
    size = int(max(min(h * 0.005, w * 0.005), 3))

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (size, size))
    closed_cropped_tresh = cv2.morphologyEx(cropped_tresh_lines, cv2.MORPH_CLOSE, kernel)

    # поиск конутуров
    # closed_cropped_tresh_blur = cv2.blur(closed_cropped_tresh, (15, 15))
    contours, hierarchy = cv2.findContours(closed_cropped_tresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    h, w = closed_cropped_tresh.shape
    minArea = 0.0005 * w * h
    fcontours, p_rects = filterContoursByMinArea(contours, hierarchy, minArea)

    fcontours = [removeSamePoints(cnt) for cnt in fcontours]

    rects = []
    for cnt in fcontours:
        x, y, w, h = cv2.boundingRect(cnt)
        rects.append((x, y, w, h))

    # анализ контуров
    contours = fcontours
    h, w = img.shape

    eps_approx = 0.01
    rect_chips = []
    # contours = [contours[21]]
    cropped_images = []

    chips_info = []
    for i, contour in enumerate(contours):
        # пытаемся понять что внутри контура
        x, y, w, h = cv2.boundingRect(contour)
        elem = cropped_image[y:y + h, x:x + w]
        wordsRecognized = recognize(elem, cropped_out=cropped_images, confThreshold=0.8, nmsThreshold=0.4)

        info_d_word = None
        for info in wordsRecognized:
            word = info["word"]
            minP, maxP = info["rect"]
            # если первая буква -- цифра, то скорее всего это D
            # if word[0] in "o0389":
            #     word = "D" + word[1:]
            if len(word) > 0 and word[0] in "1234567890o":
                if len(word) >= 3:
                    word = "D" + word[1:]
                elif maxP[0] - minP[0] > 100:
                    word = "D" + word[1:]
                else:
                    word = "D" + word
            info["word"] = word

            if len(word) > 0 and (word[0].lower() == 'd' or word[0].lower() == 'y'):
                info_d_word = info

        if isChipContour(contour, eps_approx) or info_d_word is not None:
            rect_chips.append(((x, y, w, h), info_d_word, wordsRecognized))
        else:
            # TODO: на будущее
            word = ""
            if len(wordsRecognized) > 0:
                word = wordsRecognized[0]["word"]

                chips_info.append({
                    "label": "other-" + word,
                    "points": [[x, y], [x + w, y + h]],
                    "group_id": i,
                    "description": "other",
                    "shape_type": "rectangle",
                    "flags": {}
                })
                (x1, y1), (x2, y2) = wordsRecognized[0]["rect"]
                chips_info.append({
                    "label": "other-text-" + word,
                    "points": [[x + x1, y + y1], [x + x2, y + y2]],
                    "group_id": i,
                    "description": "text on other",
                    "shape_type": "rectangle",
                    "flags": {}
                })
            else:
                chips_info.append({
                    "label": "other",
                    "points": [[x, y], [x + w, y + h]],
                    "group_id": i,
                    "description": "other",
                    "shape_type": "rectangle",
                    "flags": {}
                })

    margin = 5
    canvas = cropped_image.copy()
    for info in rect_chips:
        (x, y, w, h), info, wordsRecognized = info

        # cv2.rectangle(canvas, (x, y), (x+w, y+h), (255,0,127), 2)

        elem = cropped_image[y:y + h, x:x + w]

        if info is None and len(wordsRecognized) > 0:
            info = wordsRecognized[0]
            word = info["word"]
            if len(word) > 0 and word[0] not in "1234567890o":
                word = "D" + word[1:]
            else:
                word = "D" + word

            info["word"] = word

        ht, wt = closed_cropped_tresh.shape
        word = ""
        word_rect = None
        if info is not None:
            word = normalizeWord(info["word"])

            (x1, y1), (x2, y2) = info["rect"]
            word_rect = info["rect"]

            cx, cy = info["p"][0]
            # cv2.putText(canvas, word, (int(x + cx), int(y + cy - (y2 - y1) / 2)), cv2.FONT_HERSHEY_SIMPLEX, 1,
            #             (0, 0, 255), thickness=1)

            # print((x1, y1), (x2, y2), x, y, x+w, y+h)
            closed_cropped_tresh[y + y1:min(y + y2, ht), x + x1:min(x + x2, wt)] = np.zeros_like(
                closed_cropped_tresh[y + y1:min(y + y2, ht), x + x1:min(x + x2, wt)])

        rect = (x, y, w, h)
        x, y, w, h = x - margin, y - margin, w + 2 * margin, h + 2 * margin
        elem_bin = closed_cropped_tresh[y:y + h, x:x + w]

        # удалить возможные шумы
        kernel = np.ones((5, 5), np.uint8)
        opening = cv2.morphologyEx(elem_bin, cv2.MORPH_OPEN, kernel)

        ix, iy = findPin(opening)
        cx, cy = ix * w / 2 + w / 4, iy * h / 2 + h / 4
        # cv2.circle(canvas, (int(x + cx),int(y + cy)), 10, 255, -1)

        # x, y, w, h = rect
        chips_info.append({
            "label": "micro-" + word,
            "points": [[x, y], [x + w, y + h]],
            "group_id": i,
            "description": "micro",
            "shape_type": "rectangle",
            "flags": {}
        })

        r = min(w, h) / 32
        chips_info.append({
            "label": "pin-" + word,
            "points": [[x + cx, y + cy], [x + cx + r, y + cy + r]],
            "group_id": i,
            "description": "pin of micro",
            "shape_type": "circle",
            "flags": {}
        })
        if word_rect is not None:
            (x1, y1), (x2, y2) = word_rect
            chips_info.append({
                "label": "text-" + word,
                "points": [[x + x1, y + y1], [x + x2, y + y2]],
                "group_id": i,
                "description": "text on micro",
                "shape_type": "rectangle",
                "flags": {}
            })
        i += 1

    return canvas, cropped_image, rects, chips_info


import json
import base64
import pickle
import PIL.Image
from io import BytesIO
import os
import glob
import pathlib


def im2base64(img):
    """Convert a Numpy array to JSON string"""
    # You may need to convert the color.
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    im_pil = PIL.Image.fromarray(img)

    buffered = BytesIO()
    im_pil.save(buffered, format="JPEG")
    # img_str = base64.b64encode(buffered.getvalue())

    # imdata = pickle.dumps(im)
    return base64.b64encode(buffered.getvalue()).decode("utf-8")


def preparate(filename):
    filename = filename.replace('\\', '/')
    file = pathlib.Path(filename).stem
    folder = filename.removesuffix(filename.split('/')[-1])

    os.chdir(folder)

    image = cv2.imread(file + '.jpg')
    canvas, cropped_image, rects, chips_info = main_e(image.copy())

    cv2.imwrite(f"cropped_{file}.jpg", canvas)
    h, w, _ = cropped_image.shape
    json_val = {
        "version": "5.2.0.post4",
        "flags": {},
        "shapes": chips_info,
        "imagePath": f"{folder}{file}.jpg",
        "imageData": im2base64(canvas),
        "imageHeight": h,
        "imageWidth": w
    }

    with open('cropped_' + file + '.json', 'w') as fp:
        json.dump(json_val, fp)

    return json_val


if __name__ == "__main__":

    path = 'cb/*'
    files = glob.glob(path)

    for file in files:
        if os.path.isfile(file):
            preparate(file)
