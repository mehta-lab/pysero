# bchhun, {2020-03-22}

import os
from copy import copy
import numpy as np

import skimage.io as io
import skimage.util as u

from skimage.color import rgb2grey
from skimage.filters import threshold_minimum
from skimage.transform import hough_circle, hough_circle_peaks
from skimage.feature import canny
from skimage.morphology import binary_closing
from skimage import measure

from .img_processing import get_unimodal_threshold, create_unimodal_mask

"""
method is
1) read_to_grey(supplied images)
# find center of well
2) thresh and binarize from 1
3) find well border from 2
4) crop image from 3

# find center of spots from crop
5) thresh and binarize from 4
6) clean spot binary from 5
7) generate props from 6
8) generate props dict from 7
9) assign props dict to array from 8
"""


def read_to_grey(path_):
    """
    a generator that receives file path and returns the next rgb image as greyscale and its name

    :param path_: path to folder with all images
    :return: next image as greyscale np.ndarray, filename
    """

    images = [file for file in os.listdir(path_) if '.png' in file or '.tif' in file or '.jpg' in file]

    # sort by letter, then by number (with '10' coming AFTER '9')
    images.sort(key=lambda x: (x[0], int(x[1:-4])))

    for image_base_path in images:
        image_path = path_+os.sep+image_base_path
        im = io.imread(image_path)
        i = rgb2grey(im)
        yield i, os.path.basename(image_path)


def thresh_and_binarize(image_, method='rosin'):
    """
    receives greyscale np.ndarray image
        inverts the intensities
        thresholds on the minimum peak
        converts the image into binary about that threshold

    :param image_: np.ndarray
    :param method: str
        'bimodal' or 'unimodal'
    :return: binary threshold_min on this image
    """
    inv = u.invert(image_)
    if method == 'bimodal':
        thresh = threshold_minimum(inv)

        binary = copy(inv)
        binary[inv < thresh] = 0
        binary[inv >= thresh] = 1

        return binary
    elif method == 'rosin':
        thresh = get_unimodal_threshold(inv)

        binary = create_unimodal_mask(inv, str_elem_size=3)
        return binary


def find_well_border(binary_):
    """
    finds the border of the well to motivate future cropping around spots
        hough_radii are potential radii of the well in pixels
            this should be motivated based on magnification
        edge filter
        fit hough circle
        find the peak of the SINGULAR hough circle

    :param binary_: binarized image
    :return: center x, center y, radius of the one hough circle
    """

    hough_radii = [300, 400, 500, 600]

    edges = canny(binary_, sigma=3)
    hough_res = hough_circle(edges, hough_radii)
    aaccums, cx, cy, radii = hough_circle_peaks(hough_res, hough_radii, total_num_peaks=1)

    return cx[0], cy[0], radii[0]


def crop_image(arr, cx_, cy_, radius_, border_=200):
    """
    crop the supplied image to include only the well and its spots

    :param arr: image
    :param cx_: float
    :param cy_: float
    :param radius_:
    :param border_:
    :return:
    """

    crop = arr[
           cy_ - (radius_ - border_): cy_ + (radius_ - border_),
           cx_ - (radius_ - border_): cx_ + (radius_ - border_)
           ]

    return crop


def clean_spot_binary(arr, kx=10, ky=10):
    return binary_closing(arr, selem=np.ones((kx, ky)))


def generate_props(arr, intensity_image_=None):
    """
    converts binarized image into a list of region-properties using scikit-image
        first generates labels for the cleaned (binary_closing) binary image
        then generates regionprops on the remaining

    :param arr: np.ndarray
        binary version of cropped image
    :param intensity_image_: np.ndarray
        intensity image corresponding to this binary
    :return: list
        of skimage region-props object
    """
    labels = measure.label(arr)
    props = measure.regionprops(labels, intensity_image=intensity_image_)
    return props


def filter_props(props_, attribute, condition, condition_value):
    """

    :param props_: RegionProps
    :param attribute: str
        a regionprop attribute
        https://scikit-image.org/docs/dev/api/skimage.measure.html#regionprops
    :param condition: str
        one of "greater_than", "equals", "less_than"
    :param condition_value: int, float
        the value to evaluate around
    :return:
    """

    if condition == 'greater_than':
        out = [p for p in props_ if getattr(p, attribute) > condition_value]
    elif condition == 'equals':
        out = [p for p in props_ if getattr(p, attribute) == condition_value]
    elif condition == 'less_than':
        out = [p for p in props_ if getattr(p, attribute) < condition_value]
    else:
        out = props_

    return out


def generate_props_dict(props_, rows, cols, min_area=100, img_x_max=2048, img_y_max=2048):
    """
    based on the region props, creates a dictionary of format:
        key = (centroid_x, centroid_y)
        value = region_prop object

    :param props_: list of region props
        approximately 36-48 of these, depending on quality of the image
    :param rows: int
    :param cols: int
    :param min_area: int
    :param img_x_max: int
    :param img_y_max: int
    :return: dict
        of format (cent_x, cent_y): prop
    """

    # find minx, miny to "zero center" the array
    minx = img_x_max
    miny = img_y_max
    # find maxx, maxy to scale to array index values
    maxx = 0
    maxy = 0
    for prop in props_:
        if prop.area > min_area:
            if prop.centroid[0] < minx:
                minx = prop.centroid[0]
            if prop.centroid[1] < miny:
                miny = prop.centroid[1]
            if prop.centroid[0] > maxx:
                maxx = prop.centroid[0]
            if prop.centroid[1] > maxy:
                maxy = prop.centroid[1]

    # scaled max-x, max-y
    smaxx = maxx - minx
    smaxy = maxy - miny

    chk_list = []
    cent_map = {}
    for prop in props_:
        if prop.area > min_area:
            cx, cy = prop.centroid
            csx = cx - minx
            csy = cy - miny

            # convert the centroid position to an integer that maps to array indices
            norm_cent_x = int(round((rows-1) * (csx / smaxx)))
            norm_cent_y = int(round((cols-1) * (csy / smaxy)))

            # print(f"\ncentroid = {prop.centroid}\n\tnorm_cent = {norm_cent_x, norm_cent_y}")

            chk_list.append((norm_cent_x, norm_cent_y))
            cent_map[(norm_cent_x, norm_cent_y)] = prop

    if len(chk_list) != len(set(chk_list)):
        print("ERROR, DUPLICATE ENTRIES")
        raise AttributeError("generate props array failed\n"
                             "duplicate spots found in one position\n")

    return cent_map


def generate_region_array(props_):
    # props contains bounding box info
    # this will be useful to fill in NONE array values that have extremely low signal
    pass


def assign_props_to_array(arr, cent_map_):
    """
    takes an empty array and assigns region_property objects to each position, based on print array position

    :param arr: np.ndarray
        of shape = print array shape
    :param cent_map_: dict
        generated by "generate_props_array"
    :return:
    """

    for key, value in cent_map_.items():
        arr[key[0], key[1]] = value

    return arr