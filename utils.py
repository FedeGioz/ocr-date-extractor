import os
import re
import cv2
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import random
import imutils
from skimage.filters import threshold_local
import dateparser.search import search_dates


def rescale_image(img):
  # rescales the very large images
  height, width = img.size
  factor = min(1, float(1024.0 / height))
  size = int(factor * height), int(factor * width)
  img = img.resize(size, Image.ANTIALIAS)
  img = np.array(img)
  # adding border to image
  img = cv2.copyMakeBorder(img,10,10,10,10,cv2.BORDER_CONSTANT,value=[0,0,0])
  return img

def threshold(img):
  # threshold an image
  # convert rgb to gray
  gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
  # invert image
  gray = cv2.bitwise_not(gray)
  # blur to remove noise
  blur = cv2.GaussianBlur(gray, (5, 5), 0)
  # apply thresholding
  thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)[1]
  return thresh

def edged(img):
  # find edges in image
  # adding border
  img = cv2.copyMakeBorder(img,10,10,10,10,cv2.BORDER_CONSTANT,value=[0,0,0])
  # convert rgb to gray
  gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
  # blur to remove noise
  blur = cv2.GaussianBlur(gray, (5, 5), 0)
  # find edges
  edged = cv2.Canny(blur, 5, 70)
  return edged

def find_bbox(thresh):
  # finds bounding box of receipt
  # finding contours
  cnts = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
  cnts = cnts[0] if imutils.is_cv2() else cnts[1]
  # sorting contours by area
  cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:5]
  # finding min area rect for second biggest contour
  rect = cv2.minAreaRect(cnts[1])
  bbox = cv2.boxPoints(rect)
  bbox = np.int0(box)
  return cnts, bbox

def crop_img(img, bbox):
  # crop the image using receipt bounding box
  left, top = bbox[bbox.sum(axis=1).argmin()]
  right, bottom = bbox[bbox.sum(axis=1).argmax()]
  img = img[top:bottom,left:right]
  return img

def image_smoothening(img):
  # thresholding with less noise 
  ret1, th1 = cv2.threshold(img, 150, 255, cv2.THRESH_BINARY)
  blur = cv2.GaussianBlur(th1, (5, 5), 0)
  ret2, th2 = cv2.threshold(th1, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
  return th2

def remove_noise_and_smooth(img):
  # thresholding image for final OCR
  gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
  thresh = threshold_local(gray, 11, offset = 10, method = "gaussian")
  thresh = (gray > thresh).astype("uint8") * 255
  # applying morph operations
  kernel = np.ones((1, 1), np.uint8)
  thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
  thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
  smooth_img = image_smoothening(gray)
  # merging both threshold
  final_img = cv2.bitwise_or(smooth_img, thresh)
  return final_img

def random_string():
  return ''.join([chr(random.randint(97,122)) for i in range(10)])