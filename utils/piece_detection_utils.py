import cv2
import matplotlib.pyplot as plt
import numpy as np
import os 
import ast
################################################################################
# Helper functions

# This function blurs an image using a gaussian kernel which is useful for
# looking into an image's section to determine what color that part of the image
# is.
# It returns a blurred image based on the specfications

def blur_image(transformed_image, ksize, sigma):
  # Create the Gaussian kernel
  gaussian_kernel_1d = cv2.getGaussianKernel(ksize, sigma)
  gaussian_kernel_2d = gaussian_kernel_1d @ gaussian_kernel_1d.T

  # Apply the 2D filter
  blurred = cv2.filter2D(transformed_image, -1, gaussian_kernel_2d)

  return blurred

# This functon takes in a color as an array of 3 numbers from 0 to 1 and returns
# which color it is closest to: black, white, or green. In our testing, using
# sum of least squares was best to define what it means to be "close to". Green
# is also using 0.6 due to the nature of the images not being perfect, so it
# accomodates for values that should be green but may not be detected as such
# by making the threshold for detecting green smaller.
# It returns the color as black: -1, white: 1, green: 0.

def classify_color_rgb(avg_color):
  diff_w = np.square(avg_color - [1, 1, 1])
  diff_g = np.square(avg_color - [0, 0.8, 0]) #Original 0.8
  diff_b = np.square(avg_color - [0, 0, 0]) # for completion sake

  diff_w_s = np.sum(diff_w)
  diff_g_s = np.sum(diff_g)
  diff_b_s = np.sum(diff_b)

  # Find the smallest difference
  if (diff_b_s < diff_g_s and diff_b_s < diff_w_s):
    return -1 # black
  elif (diff_w_s < diff_b_s and diff_w_s < diff_g_s):
    return 1 # white
  else:
    return 0 # green



################################################################################
# This function takes in an image, the corners, and the intended location on the
# board in the form of i, j: the row and column of the piece you want to know
# is white, green or black. The row and columns are somewhat arbitrary since the
# images may be warped and rotated. Since we arent doing any heavy analysis, it
# doesnt matter for our purposes whether the board is rotated 90 degrees off of
# what one might expect.
# It returns the color, the transformed image, the blurred image, and the region
# for testing or debugging purposes.

def detect_piece(image, corners, i, j):
  try:
    # Corresponding square 400 x 400
    mapped_size = 400
    mapped_corners = np.array([
      [0, 0],
      [mapped_size-1, 0],
      [mapped_size-1, mapped_size-1],
      [0, mapped_size-1]
    ], dtype=np.float32)

    # Compute homography matrix
    H = cv2.getPerspectiveTransform(corners, mapped_corners)

    # Transform the image into a sqaure
    transformed = cv2.warpPerspective(image, H, (mapped_size, mapped_size))

    # Define paramters to blur the image.
    ksize = 5
    sigma = 3
    blurred_image = blur_image(transformed, ksize, sigma)

    # Define the sub-region where the piece you want to detect lies
    scale = int(mapped_size / 8)
    y1, y2 = scale*i+(scale//4), scale*i+scale-(scale//4)
    x1, x2 = scale*j+(scale//4),  scale*j+scale-(scale//4)
    region = blurred_image[y1:y2, x1:x2,:]

    # Get the average color of the region
    avg_bgr = np.mean(region, axis=(0, 1))
    avg_rgb = avg_bgr[::-1]

    # Classify the average color as close to black, white or green
    color = classify_color_rgb(avg_rgb)


    #Obtain the coordinates of x1, x2, y1, y2 that would map to the original image not transformed image
    # corners of the region in warped space
    corners_warped = np.array([
        [x1, y1],
        [x2, y1],
        [x2, y2],
        [x1, y2]
    ], dtype=np.float32).reshape(-1, 1, 2)

    # inverse transform all points
    H_inv = np.linalg.inv(H)
    corners_original = cv2.perspectiveTransform(corners_warped, H_inv)

    # Compute average x and y (i.e., the center of the region)
    coords = corners_original.reshape(4, 2)
    avg_x = np.mean(coords[:, 0])
    avg_y = np.mean(coords[:, 1])
    center_original = (avg_x, avg_y)

    return [color, transformed, blurred_image, region, center_original]
  except Exception as e:
    raise RuntimeError(f"piece_detection_failed: {e}")
     


def compare_board_states(board_state, board_index):
    real_board_dir = 'Real_Board_Values/'
    real_board_file = os.path.join(real_board_dir, f'board{board_index}.txt')

    # Read the real board values from the file
    with open(real_board_file, 'r') as f:
        real_board_state = ast.literal_eval(f.read())

    # Convert to numpy arrays for easy comparison
    real_board_state = np.array(real_board_state)
    detected_board_state = np.array(board_state)

    # Calculate total matches
    matches = np.sum(real_board_state == detected_board_state)
    individual_accuracy = (matches / (64)) * 100
    # print(f"Individual Accuracy:  {individual_accuracy:.2f}%")
    true_score = np.sum(real_board_state)
    detected_score = np.sum(detected_board_state)
    # print(f"True Score: {true_score}, Detected_Score: {detected_score}\n")
    return matches