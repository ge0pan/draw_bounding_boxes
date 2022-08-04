import json
import sys

from argparse import ArgumentParser
from typing import Optional, Any
from pathlib import Path
from PIL import ImageDraw, Image
from settings import logger

Vector = list[int]
final_path = "/home/twist/edited_screenshots"  # your folder where we will save the modified screenshots


def bounding_boxes_drawer(value: Vector, img: Optional[Any]):
    """ Draws rectangles based on bounds coordinates
    Keyword arguments:
        value -- Two points to define the bounding box. Sequence of [x0, y0, x1, y1], where x1 >= x0 and y1 >= y0.
        img -- screenshot file which is already opened
    """
    width, height = img.size
    # The next 4 lines of code adjust the size of the rectangle to the size of the image. In json files of Rico
    # dataset the bounds property specifies an element's bounding box within a 1440x2560 screen window.
    value[0] = value[0] / 1440 * width
    value[1] = value[1] / 2560 * height
    value[2] = value[2] / 1440 * width
    value[3] = value[3] / 2560 * height
    cur_image = ImageDraw.Draw(img)
    cur_image.rectangle(value, fill=None, outline=(255, 0, 255), width=2)


def json_file_walker(dictionary: dict, img_file: Optional[Any]):
    """ Founds all bounds coordinates in one json-file
    Keyword arguments:
            dictionary -- value of root node: ["activity"]["root"]
            img_file -- screenshot file which is already opened
     """
    if 'bounds' in dictionary:
        if dictionary['visible-to-user'] and dictionary['visibility'] == "visible":
            bounding_boxes_drawer(dictionary['bounds'], img_file)
    if 'children' in dictionary:
        for child in dictionary['children']:
            json_file_walker(child, img_file)  # recursion to visit all children


def jpegs_walker(cur_path: Optional[Any]):
    """ Main function which executes the remaining functions for all json and jpeg files
    in our folder and saves the result
    Keyword arguments:
        cur_path -- path to folder with json and jpeg files
    """
    for all_files in list(Path(cur_path).glob('*.json')):
        cur_name = all_files.name
        image_name = cur_name.rpartition('.')[0] + '.jpg'
        image_root = Path(cur_path, image_name)
        with open(all_files) as file:
            current_dictionary = json.load(file)
        # All elements in the UI can be accessed by traversing the view hierarchy starting
        # at the root node: ["activity"]["root"]
        current_dictionary = current_dictionary['activity']['root']
        img = Image.open(image_root)
        json_file_walker(current_dictionary, img)
        img.save(f"{final_path}/{image_name}")  # saving edited image


def parser_creator() -> ArgumentParser:
    """Parses elements and contains path to our folder"""
    parser = ArgumentParser()
    parser.add_argument('path', nargs='?')
    return parser


if __name__ == '__main__':
    # Parsing command line arguments
    my_parser = parser_creator()
    namespace = my_parser.parse_args()
    # Checking path validity
    if namespace.path:
        current_path = namespace.path
    else:
        logger.error('You must pass the path to the dataset')
        sys.exit()
    [f.unlink() for f in Path(final_path).glob("*") if f.is_file()]  # cleaning folder where you save edited screenshots
    jpegs_walker(current_path)
    logger.info('Execution has finished successfully')
