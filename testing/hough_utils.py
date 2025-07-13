from os import path
import math

# Third-Party Imports
import cv2
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import griddata
from sklearn.cluster import DBSCAN as db
from itertools import combinations
from sklearn.cluster import KMeans

#Applies Mask to the image
def prep_image(img, chroma_key,sigma,ksize, threshold):
    oned_fil = cv2.getGaussianKernel(ksize, sigma) # 1D kernel
    twod_fil = oned_fil*np.transpose(oned_fil)

    im_fil_low = img.copy()#cv2.filter2D(img,-1,twod_fil)
    
    dim = 3 if len(im_fil_low.shape) == 3 else 1

    for i in range (im_fil_low.shape[0]):
        for j in range(im_fil_low.shape[1]):
            color = img[i][j]
            difference = np.abs(chroma_key-color)
            im_fil_low[i][j] = np.ones(dim) if (np.sum(difference) < threshold) else np.zeros(dim)
    
    im_fil_low = np.clip(cv2.filter2D(im_fil_low,-1,twod_fil),0,1)
    plt.imshow(im_fil_low)
    plt.show()
    
    return im_fil_low

#Function that calculates Hough and its Helper functions are listed below
from itertools import product
def compute_line(line):
    """Returns line coefficients (a, b, c) from points: ax + by + c = 0"""
    a = line[1] - line[3]
    b = line[2] - line[0]
    c = line[0]*line[3] - line[2]*line[1]
    return a, b, -c

def intersection(L1, L2):
    """Find intersection point of two lines given in ax + by + c = 0 form"""
    D = L1[0] * L2[1] - L1[1] * L2[0]
    if D == 0:
        return None  # parallel lines
    Dx = L1[2] * L2[1] - L1[1] * L2[2]
    Dy = L1[0] * L2[2] - L1[2] * L2[0]
    x = Dx / D
    y = Dy / D
    return x, y

def hough(img):
    print("Made call to Hough")
    mask = prep_image(img,(0,1,0),10,(int)(img.shape[0]/10),0.95)
    masked_img =  (mask*img * 255).astype(np.uint8)
    plt.imshow(masked_img)
    plt.show()

    masked_gray =  cv2.cvtColor(masked_img, cv2.COLOR_RGB2GRAY)
    masked_gray = cv2.GaussianBlur(masked_gray, (5, 5), 0)
    edges = cv2.Canny(masked_gray,25,75)
    lines = cv2.HoughLinesP(edges,rho=1,theta=np.pi / 180,threshold=img.shape[0]//10,minLineLength=img.shape[0]/4,maxLineGap=img.shape[0]//10)
    line_detection_img = img.copy()
    plt.imshow(edges)
    plt.show()

    thetas = []
    for x1,y1,x2,y2 in lines[:,0]:
        theta = np.arctan2(y2-y1, x2-x1) + 3*np.pi/2
        thetas.append([theta])
    thetas = np.array(thetas)

    labels = db(eps=0.1, min_samples=1).fit_predict(thetas)

    vertical = []
    horizontal = []
    vert_dir = np.zeros(2,dtype=np.float64)
    horz_dir = np.zeros(2)
    for i in range(len(lines)):
        x1,y1,x2,y2 = lines[i][0]
        if labels[i] == 1:
            vertical.append(lines[i][0])
            vert_dir += [x2 - x1, y2 - y1]
            color = [1,0,0]
        elif labels[i] == 0:
            horizontal.append(lines[i][0])
            horz_dir += [x2 - x1, y2 - y1]
            color = [0,0,1]
        else:
            v1 = np.array([x2 - x1, y2 - y1],dtype=np.float64)
            v1 /= np.linalg.norm(v1)
            normalized_horz_dir = horz_dir/np.linalg.norm(horz_dir)
            normalized_vert_dir = vert_dir/np.linalg.norm(vert_dir)

            if abs(np.dot(v1, normalized_vert_dir)) > 0.95:
                vertical.append(lines[i][0])
                vert_dir += [x2 - x1, y2 - y1]
                color = [1,0,0]
            elif abs(np.dot(v1, normalized_horz_dir)) > 0.95:
                horizontal.append(lines[i][0])
                horz_dir += [x2 - x1, y2 - y1]
                color = [0,0,1]
            else:
                color = [0,1,0]
        cv2.line(line_detection_img, (x1, y1), (x2, y2), color, 3)
    
    points = []
    for a, b in product(vertical, horizontal):
        L1 = compute_line(a)
        L2 = compute_line(b)
        pt = intersection(L1, L2)
        if pt:
            points.append(pt)
            plt.scatter(pt[0], pt[1], color='pink', s=5, marker='o')
    points = np.array(points)
    plt.imshow(line_detection_img)
    plt.show()

    if points.size > 81:
        kmeans = KMeans(n_clusters=81, n_init='auto')
        labels = kmeans.fit_predict(points)
        points = kmeans.cluster_centers_
    plt.imshow(img)
    plt.scatter(points[:,0],points[:,1], color='yellow', s=5, marker='o')
    plt.show()


    corners = np.zeros((4,2))
    hull = cv2.convexHull(points.astype(np.float32))
    epsilon = 0.02 * cv2.arcLength(hull, True)
    approx = cv2.approxPolyDP(hull, epsilon, True)
    if len(approx) == 4:
        corners = approx[:, 0, :]  # shape (4, 2)
    
    return corners