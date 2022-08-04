import json
import sys

from argparse import ArgumentParser
from typing import Optional, Any
from pathlib import Path
from PIL import ImageDraw, Image
from settings import logger

BBox = [int, int, int, int]
a: BBox = [1, 2, 3]
Vector = list[int]
# ^-- not a very common practice for such simple types, but bearable
# if it's a bbox type a better name would be `BBox` and a better typing would be
# BBox = [int, int, int, int]

final_path = "/home/twist/edited_screenshots"  # your folder where we will save the modified screenshots
# ^-- should be an argparse option obviously


#       it's a common practice to name functions/methods with verbs (e.g. `draw_bounding_boxes`)
#       in such case a function call in code is more readable:
#       ```
#       ...do some stuff
#       draw_bounding_boxes()
#       ```
#                         v-- not a very good parameter name (it's better be called such that no documentation is needed, e.g. `bbox` or `bounding_box`)
def bounding_boxes_drawer(value: Vector, img: Optional[Any]):
    """ Draws rectangles based on bounds coordinates
    Keyword arguments:
        value -- Two points to define the bounding box. Sequence of [x0, y0, x1, y1], where x1 >= x0 and y1 >= y0.
        img -- screenshot file which is already opened
    """
    width, height = img.size

    # v-- When you need to document something, mb it's a sign that it's complex enough to be moved to a separate function

    # The next 4 lines of code adjust the size of the rectangle to the size of the image. In json files of Rico
    # dataset the bounds property specifies an element's bounding box within a 1440x2560 screen window.
    value[0] = value[0] / 1440 * width
    value[1] = value[1] / 2560 * height
    value[2] = value[2] / 1440 * width
    value[3] = value[3] / 2560 * height
    # ^-- modifying parameter data often is a bad practice
    # some of the other code may be using that same data that it didn't know is modified in current method
    # (causing this function to have non documented "side-effects")
    cur_image = ImageDraw.Draw(img)
    cur_image.rectangle(value, fill=None, outline=(255, 0, 255), width=2)

#                    v-- `view_tree`?  v-- `img` (at least that's the name of this parameter in the previous function)
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
            # ^-- recursion becomes a bad thing in python on scale (these trees can be very big in depth)
            # (see/google recursion depth limit in python)


def jpegs_walker(cur_path: Optional[Any]):
    """ Main function which executes the remaining functions for all json and jpeg files
    in our folder and saves the result
    Keyword arguments:
        cur_path -- path to folder with json and jpeg files
    """
    for all_files in list(Path(cur_path).glob('*.json')):
        cur_name = all_files.name
        image_name = cur_name.rpartition('.')[0] + '.jpg'
        #                     ^-- see `pathlib.PurePath.stem` 
        # v-- mb `image_path` is a better name (may be misleading what a "root" of an "image" is)
        image_root = Path(cur_path, image_name)
        #                     ^-- just a syntax sugar but same as `Path(cur_path) / image_name`
        with open(all_files) as file:
        #                        ^-- file is builtin python word, so you're shadowing it with a file object's name
            # v-- `view_tree`?
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
    # by the code below seems like this argument is required (not `?`)
    # see argparse docs for this
    # also argparse allows to parse the input as python `Path` (google it or investigate the sources)
    parser.add_argument('path', nargs='?')
    return parser


if __name__ == '__main__':
    # Parsing command line arguments
    my_parser = parser_creator()
    # ^-- simply `parser` would do

    namespace = my_parser.parse_args()
    # Checking path validity
    if namespace.path:
        current_path = namespace.path
    else:
        logger.error('You must pass the path to the dataset')
        sys.exit()
    [f.unlink() for f in Path(final_path).glob("*") if f.is_file()]  # cleaning folder where you save edited screenshots
    # ^-- usually we use list comprehenions when we need the result, so using list comprehension here instead of a loop may be a bit misleading

    jpegs_walker(current_path)
    logger.info('Execution has finished successfully')
