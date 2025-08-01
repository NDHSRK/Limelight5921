# import the necessary packages
import numpy as np
import cv2
from enum import Enum
import sys
import traceback

## 7/13/2025 copy/paste from Pycharm AutomaticThresholding project
# with modifications to contour filtering for the Limelight.
#################################################################
# ImageUtils.py
#################################################################
class ImageUtils:

    @staticmethod
    def apply_grayscale_threshold(p_grayscale_image, grayscale_threshold_low):
        thresh_binary_flag = cv2.THRESH_BINARY if grayscale_threshold_low >= 0 else cv2.THRESH_BINARY_INV
        _, thresholded = cv2.threshold(p_grayscale_image, grayscale_threshold_low, 255, thresh_binary_flag)
        return thresholded

    @staticmethod
    def apply_inRange(p_hsv_roi, hue_low, hue_high, sat_threshold_low, val_threshold_low):
        # Sanity check for hue.
        if not ((0 <= hue_low <= 180) and (0 <= hue_high <= 180)):
            raise Exception("Hue out of range")

        if hue_low < hue_high:  # Normal hue range.
            # Define lower and upper bounds in this way to avoid Python warnings.
            lower_bounds = np.array([hue_low, sat_threshold_low, val_threshold_low], dtype=np.uint8)
            upper_bounds = np.array([hue_high, 255, 255], dtype=np.uint8)
            thresholded = cv2.inRange(p_hsv_roi, lower_bounds, upper_bounds)
        else:
            # For a hue range from the XML file of low 170, high 10
            # the following yields two new ranges: 170 - 180 and 0 - 10.
            lower_bounds_1 = np.array([hue_low, sat_threshold_low, val_threshold_low])
            upper_bounds_1 = np.array([180, 255, 255])
            range1 = cv2.inRange(p_hsv_roi, lower_bounds_1, upper_bounds_1)

            lower_bounds_2 = np.array([0, sat_threshold_low, val_threshold_low])
            upper_bounds_2 = np.array([hue_high, 255, 255])
            range2 = cv2.inRange(p_hsv_roi, lower_bounds_2, upper_bounds_2)
            thresholded = cv2.bitwise_or(range1, range2)

        return thresholded

    @staticmethod
    def get_hue_range(p_hist, dominant_bin_index):
        # Log all non-zero histogram bins.
        min_pixel_count = np.min(p_hist)
        print("Minimum pixel count", min_pixel_count)
        for bin_index, count in enumerate(p_hist):
            if count[0] != min_pixel_count:
                print(f"Bin {bin_index}: {count[0]}")

        # Look at bins on each side of the dominant bin/hue
        # until you find one with the minimum pixel count,
        # typically 0. Be mindful of the wrap-around at 0/180.
        adjacent_bin = dominant_bin_index
        while True:
            adjacent_bin = adjacent_bin - 1
            if adjacent_bin == -1:
                adjacent_bin = 179  # crossed boundary at 0

            print("Bin " + str(adjacent_bin) + ", pixel count " + str(p_hist[adjacent_bin]))
            if p_hist[adjacent_bin] == min_pixel_count:
                print("Found minimum pixel count at bin " + str(adjacent_bin))
                hsv_hue_low = adjacent_bin
                break

        adjacent_bin = dominant_bin_index
        while True:
            adjacent_bin = adjacent_bin + 1
            if adjacent_bin == 180:
                adjacent_bin = 0  # crossed boundary at 179

            print("Bin " + str(adjacent_bin) + ", pixel count " + str(p_hist[adjacent_bin]))
            if p_hist[adjacent_bin] == min_pixel_count:
                print("Found minimum pixel count at bin " + str(adjacent_bin))
                hsv_hue_high = adjacent_bin
                break

        print("Hue low, high " + str(hsv_hue_low) + ", " + str(hsv_hue_high))
        return hsv_hue_low, hsv_hue_high

    # Based on - but not the same as - AutomaticThresholding.ImageUtils.
    @staticmethod
    def filter_contours_limelight(p_thresholded, image_height, image_width, min_area, max_area):
        contours, _ = cv2.findContours(p_thresholded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        filtered_contours = []

        # Draw on an all-black background; drawContours requires a BGR image.
        filtered_bgr = np.zeros((image_height, image_width, 3), dtype=np.uint8)

        num_below_min_area = 0
        num_above_max_area = 0
        num_filtered = 0
        for i, contour in enumerate(contours):
            oneContourArea = cv2.contourArea(contours[i])
            if oneContourArea < min_area:
                num_below_min_area = num_below_min_area + 1
                continue

            if oneContourArea > max_area:
                num_above_max_area = num_above_max_area + 1
                continue

            # Got a contour whose area is in range.
            num_filtered = num_filtered + 1
            filtered_contours.append(contours[i])
            cv2.drawContours(filtered_bgr, contours, i, (255, 255, 255), cv2.FILLED)
            # debug cv2.imshow("Found contour ", filtered_bgr)
            # debug cv2.waitKey(0)

        # Convert the BGR image to grayscale, which in our case should be binary.
        filtered_binary = cv2.cvtColor(filtered_bgr, cv2.COLOR_BGR2GRAY)

        # The Limelight runtime wants the largest contour.
        if filtered_contours:
            largest_filtered_contour = max(filtered_contours, key=cv2.contourArea)
        else:
            largest_filtered_contour = np.array([[]])

        return ImageUtils.FilteredContoursRecordLimelight(len(contours), num_below_min_area, num_above_max_area,
                                                          largest_filtered_contour, filtered_binary)

    class FilteredContoursRecordLimelight:
        def __init__(self, num_unfiltered_contours, num_below_min_area, num_above_max_area,
                     largest_filtered_contour, filtered_binary_output):
            self.numUnfilteredContours = num_unfiltered_contours
            self.numBelowMinArea = num_below_min_area
            self.numAboveMaxArea = num_above_max_area
            self.largest_filtered_contour = largest_filtered_contour
            self.filtered_binary_output = filtered_binary_output


#################################################################
# SampleParameters.py
#################################################################

# Python grayscale threshold/HSV inRange values derived from
# IJThresholdTester or Gimp.
class SampleParameters:
    ##!! As a demonstration, for the yellow sample use the
    # green rgb channel and grayscale threshold.
    GREEN_CHANNEL_THRESHOLD_LOW = 160 # LRS03081735... Regional

    # hsv for blue
    BLUE_HSV_HUE_LOW = 110
    BLUE_HSV_HUE_HIGH = 125
    BLUE_HSV_SAT_THRESHOLD_LOW = 50
    BLUE_HSV_VAL_THRESHOLD_LOW = 100

    # hsv for red
    RED_HSV_HUE_LOW = 170
    RED_HSV_HUE_HIGH = 5
    RED_HSV_SAT_THRESHOLD_LOW = 50
    RED_HSV_VAL_THRESHOLD_LOW = 100

    MIN_SAMPLE_AREA = 9000.0
    MAX_SAMPLE_AREA = 21000.0

    MIN_SAMPLE_ASPECT_RATIO = 1.6
    MAX_SAMPLE_ASPECT_RATIO = 3.0

#################################################################
# OpenCVRotatedRect.py
#################################################################
# Class for the public attributes in an OpenCV RotatedRect,
# created so that we can reference them by name. The attributes
# are defined in the c++ documentation as:

# float 	angle
# 	returns the rotation angle. When the angle is 0, 90, 180, 270 etc., the rectangle becomes an up-right rectangle.

# Point2f 	center
# 	returns the rectangle mass center

# Size2f 	size
# 	returns width and height of the rectangle

# In Python these attributes are represented as:
# (center(x, y), (width, height), angle of rotation)

class OpenCVRotatedRect:
    def __init__(self, opencv_rotated_rect):
        self.opencv_rotated_rect = opencv_rotated_rect
        self.center_x = opencv_rotated_rect[0][0]
        self.center_y = opencv_rotated_rect[0][1]
        self.width = opencv_rotated_rect[1][0]
        self.height = opencv_rotated_rect[1][1]
        self.angle = opencv_rotated_rect[2]


#################################################################
# SampleRecognition.py
#################################################################

class SampleRecognition:
    class Alliance(Enum):
        BLUE = 1
        RED = 2

    class SampleColor(Enum):
        BLUE = 0
        RED = 1
        YELLOW = 2
        NONE = 3

    class SampleOrientation(Enum):
        VERTICAL = 1
        HORIZONTAL = 2
        COUNTER_CLOCKWISE = 3
        CLOCKWISE = 4

    def __init__(self, p_alliance):
        self.alliance = p_alliance
        self.image_roi_height = 0.0
        self.image_roi_width = 0.0
        self.image_roi_center = (0.0, 0.0)

    class SampleRecognitionReturn:
        class RecognitionStatus(Enum):
            SUCCESS = 200
            PYTHON_APP_CRASH = 300
            IDLE = 400
            IMAGE_NOT_AVAILABLE = 450
            FAILURE = 500

        def __init__(self, status, color_value, ftc_angle, selected_sample_center_x, selected_sample_center_y,
                     sample_contour, drawn_target):
            self.status = status
            self.color_value = color_value
            self.ftc_angle = ftc_angle
            self.selected_sample_center_x = selected_sample_center_x
            self.selected_sample_center_y = selected_sample_center_y
            self.sample_contour = sample_contour
            self.drawn_target = drawn_target

    # The points of an OpenCV RotatedRect are numbered 0 to 4, where
    # point 0 is that with the least x (first) and least y (second,
    # in case two points have the same x) value. The angle of a
    # RotatedRect is always measured from point 0 and always lies
    # between [0,90], exclusive of 0 but inclusive of 90,
    # because if the object is rotated more than 90 degrees, the
    # next point (either point 1 or point 2, depending on the
    # direction of the rotation) becomes point 0.

    # The angle is measured from a line between point 0 and point 1
    # (clockwise) and a line through point 0 parallel to the left
    # boundary of the image. The "height" of a RotatedRect is
    # *always" the distance between point 0 x and point 1 x; the
    # "width" is always the distance between point 1 y and point 2 y.
    # In the case of IntoTheDeep samples, our "width" is always the
    # longer of these two RotatedRect values, i.e. the 3.5" side of
    # a sample.

    # The angle of both a perfectly vertical RotatedRectangle
    # and a perfectly horizontal RotatedRectangle is 90.0.
    def get_sample_orientation_and_ftc_angle(self, p_rotated_sample):
        # Always get the box points for debugging.
        box = cv2.boxPoints(p_rotated_sample.opencv_rotated_rect)
        rect_points = np.int32(box)  # Integer values for pixel indices

        if p_rotated_sample.angle == 90.0:
            if p_rotated_sample.height < p_rotated_sample.width:
                sample_orientation = self.SampleOrientation.VERTICAL
                ftc_angle = 0.0
            elif p_rotated_sample.height > p_rotated_sample.width:
                sample_orientation = self.SampleOrientation.HORIZONTAL
                ftc_angle = 90.0
            else:  # square
                sample_orientation = self.SampleOrientation.VERTICAL
                ftc_angle = 0.0

        # The RotatedRect must be angled counter-clockwise or clockwise
        elif p_rotated_sample.width > p_rotated_sample.height:
            sample_orientation = self.SampleOrientation.COUNTER_CLOCKWISE
            ftc_angle = 90.0 - p_rotated_sample.angle
        elif p_rotated_sample.width < p_rotated_sample.height:
            sample_orientation = self.SampleOrientation.CLOCKWISE
            ftc_angle = -1 * p_rotated_sample.angle
        else:
            # Got an angled square. This should not happen but we have to deal with it.
            # If point 1 y < point 0 y then the orientation is CCW, else CW.
            if round(rect_points[1][1]) < round(rect_points[0][1]):
                sample_orientation = self.SampleOrientation.COUNTER_CLOCKWISE
                ftc_angle = 90.0 - p_rotated_sample.angle
            else:
                sample_orientation = self.SampleOrientation.CLOCKWISE
                ftc_angle = -1 * p_rotated_sample.angle

        return sample_orientation, ftc_angle

    def perform_recognition(self, image):
        self.image_roi_height, self.image_roi_width = image.shape[:2]
        self.image_roi_center = (self.image_roi_width / 2.0, self.image_roi_height / 2.0)

        ##**TODO In the real IntoTheDeep game you'd want to recognize
        # both alliance and neutral (yellow) samples and combine the
        # results to target the best sample to pick up. But in the
        # interest of simplicity let's just look for the neutral
        # samples.

        # Demonstrate how to find the yellow samples by thresholding
        # the green channel of the original BGR image.
        b, g, r = cv2.split(image) # split the image into its BGR channels
        thresholdedN = ImageUtils.apply_grayscale_threshold(g, SampleParameters.GREEN_CHANNEL_THRESHOLD_LOW)
        cv2.imshow("ThrN", thresholdedN)
        cv2.waitKey(0)

        # Sanitize the thresholded neutral samples by eliminating contours
        # that are below the minimum allowable area or above the maximum
        # allowable area.
        filteredN = ImageUtils.filter_contours_limelight(thresholdedN, self.image_roi_height, self.image_roi_width,
                                                         SampleParameters.MIN_SAMPLE_AREA / 2.0,
                                                         SampleParameters.MAX_SAMPLE_AREA)

        # Get a rotated rectangle from the largest contour.
        ret_status = self.SampleRecognitionReturn.RecognitionStatus.FAILURE
        color_value = SampleRecognition.SampleColor.YELLOW.value
        drawn_targets = np.copy(image)
        ftc_angle = 0.0
        sample_center_x = 0
        sample_center_y = 0

        # Make sure we found at least one contour.
        if filteredN.largest_filtered_contour.size > 0:
            ret_status = self.SampleRecognitionReturn.RecognitionStatus.SUCCESS
            one_rotated_rect = cv2.minAreaRect(filteredN.largest_filtered_contour)
            rotated_sample = OpenCVRotatedRect(one_rotated_rect)

            # From the OpenCV RotatedRect determine the orientation and
            # FTC angle of the sample.
            sample_orientation, ftc_angle = self.get_sample_orientation_and_ftc_angle(rotated_sample)
            print("Sample orientation: " + str(sample_orientation) + ", FTC angle " + str(ftc_angle))

            sample_center_x = rotated_sample.center_x
            sample_center_y = rotated_sample.center_y
            points = cv2.boxPoints(rotated_sample.opencv_rotated_rect)
            points = np.int32(points)

            # Draw the rotated rectangle around the sample contour.
            cv2.drawContours(drawn_targets, [points], 0, (0, 255, 0), 2)

        return self.SampleRecognitionReturn(ret_status,
                                            color_value, ftc_angle,
                                            sample_center_x,
                                            sample_center_y,
                                            filteredN.largest_filtered_contour, drawn_targets)

'''
llPython return value mapping:
llPython[0] = status, one of SampleRecognition.SampleRecognitionReturn.RecognitionStatus.<status>.value
llPython[1] = sample color detected, one of SampleRecord.SampleColor.<color>.value,
llPython[2] = ftc_angle of selected sample
llPython[3] = center of selected sample x (pixels)
llPython[4] = center of selected sample y (pixels)
'''

#################################################################
# Main program
#################################################################
def runPipeline(image, llrobot):
    alliance_ordinal = int(llrobot[0])

    match alliance_ordinal:
        case 1:
            alliance = SampleRecognition.Alliance.BLUE
        case 2:
            alliance = SampleRecognition.Alliance.RED
        case _:
            return np.array([[]]), image, [
                SampleRecognition.SampleRecognitionReturn.RecognitionStatus.IDLE.value,
                SampleRecognition.SampleColor.NONE.value]

    try:
        ##!! It can happen that the Limelight runtime calls
        # runPipeline before an image is actually available,
        # probably because of the settable exposure time. So
        # we'll test for an all-black image and return a code
        # to the caller.
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        non_zero_pixel_count = cv2.countNonZero(gray_image)
        if non_zero_pixel_count == 0:
            return np.array([[]]), image, [
                SampleRecognition.SampleRecognitionReturn.RecognitionStatus.IMAGE_NOT_AVAILABLE.value]

        recognition = SampleRecognition(alliance)
        ret_val = recognition.perform_recognition(image)
        print(ret_val.status)

        if ret_val.status == SampleRecognition.SampleRecognitionReturn.RecognitionStatus.FAILURE:
            llpython = [SampleRecognition.SampleRecognitionReturn.RecognitionStatus.FAILURE.value,
                        # the color we were working on at the time of failure
                        ret_val.color_value]
        else:
            # record some custom data to send back to the robot
            # For logging/debugging include target sample center x, y; PickupZonePosition(Enum) value
            llpython = [SampleRecognition.SampleRecognitionReturn.RecognitionStatus.SUCCESS.value,
                        ret_val.color_value,
                        ret_val.ftc_angle,
                        ret_val.selected_sample_center_x,
                        ret_val.selected_sample_center_y]

        # Return the OpenCV contour of the selected sample for the LL crosshair,
        # the modified image, and custom robot data.
        return ret_val.sample_contour, ret_val.drawn_target, llpython
    except Exception as e:
        # For debugging print out information from the exception.
        print(repr(e))

        # For an FTC client send the line number - also prints locally.
        # Get the traceback information
        exc_type, exc_value, exc_traceback = sys.exc_info()

        # Extract the line number from the traceback
        line_number = traceback.extract_tb(exc_traceback)[-1][1]

        # Indicate that our application has crashed.
        return np.array([[]]), image, [
            SampleRecognition.SampleRecognitionReturn.RecognitionStatus.PYTHON_APP_CRASH.value,
            line_number]
