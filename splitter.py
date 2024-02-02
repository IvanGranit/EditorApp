import cv2
import numpy as np
import matplotlib.pyplot as plt

import os
import glob
import pathlib
import warnings

def crop_image(bin_img, epsMinArea=0.005, maxIter = 10):
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

    if maxBlock is None:
        warnings.warn(f"Not found schema for eps = {epsMinArea*100}%")
        if maxIter > 0:
            return crop_image(bin_img, epsMinArea / 2, maxIter-1)
        else:
            maxBlock = 0 

    # обрезаем по схеме
    return cv2.boundingRect(contours[maxBlock]), contours[maxBlock]

def crop_images(bin_img, epsMinArea=0.05, margin=10, epsArea=0.1):
    res = []

    while True:
        (x, y, w, h), contour = crop_image(bin_img, epsMinArea)
        bin_img[y-margin:y+h+margin, x-margin:x+w+margin] = np.zeros_like(bin_img[y-margin:y+h+margin, x-margin:x+w+margin])

        # canvas = bin_img.copy()
        # cv2.rectangle(canvas, (x, y), (x+w, y+h), (255,0,127), 2)
        # plt.imshow(canvas)
        # plt.show()

        if len(res) > 0:
            _, _, w0, h0 = res[0]
            area = h0 * w0
            if abs(area - w * h) > area * epsArea:
                break

        res.append((x, y, w, h))

    res.sort(key=lambda x: x[2] * x[3], reverse=True)
    return res

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
            kernel[sx-1 - i][j] *= v
            
    for i in range(sx):
        if i == sx_2:
            continue
        for j in range(sy_2):
            v = k / (sy_2 - j)
            kernel[i][j] *= v
            kernel[i][sy-1 - j] *= v
    return kernel

def splitter(filename):
    file = pathlib.Path(filename).stem

    image = cv2.imread(filename)
    img = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    _, tresh = cv2.threshold(img, 0,255,cv2.THRESH_OTSU)
    tresh = cv2.bitwise_not(tresh)

    kernel = createKernel(3, 3, k=0.1)
    dilate_tresh = cv2.dilate(tresh, kernel, 5)

    boxes = crop_images(dilate_tresh, margin=0)[:2]

    margin = 5
    for i, box in enumerate(boxes):
        x, y, w, h = box
        cropped_img = image[y-margin:y+h+margin, x-margin:x+w+margin]
        cv2.imwrite(f'./cb/{file}-{i}.jpg', cropped_img)

if __name__ == "__main__":
    path = './cb/forbidden/*'
    files = glob.glob(path)

    for file in files:
        if os.path.isfile(file):
            splitter(file)

#splitter("./cb/forbidden/2.jpg")