import sys
import os
import argparse
from PIL import Image

'''helper function, calculate the list of width/height of output slices'''
# return a list, in which contains the calculated width/height of each slice.


def calculate_slices_size(image_height_or_width, slice_count, step_size, ratio):
    # arguments parsing, validation.
    assert image_height_or_width > 0
    assert slice_count >= 0
    assert step_size >= 0
    # one of the step_size or slice_count should be zero, or it's a invalid invoke.
    assert step_size * slice_count == 0
    # make sure they are not both zero, or it's a invalid invoke.
    assert step_size != slice_count
    # make sure ratio is a instance of str, even if it's empty.
    assert isinstance(ratio, str)

    slices_size = []
    # equal slice
    if slice_count:
        # equal slice, the step_size should be zero, ratio should be an empty string, or it's a invalid invoke.
        assert step_size == 0
        assert not ratio
        # begin the calculation.
        base_size = int(image_height_or_width//slice_count)
        remainder = image_height_or_width - base_size*slice_count
        for slice in range(slice_count):
            if remainder>0:
                size = base_size + 1
                remainder -= 1
                slices_size.append(size)
            else:
                slices_size.append(base_size)

    # step slice
    elif step_size:
        # make sure slice_count is zero, ratio is an empty string, or it's a invalid invoke.
        assert slice_count == 0
        assert not ratio

        while(image_height_or_width>0):
            if image_height_or_width>= step_size:
                slices_size.append(step_size)
                image_height_or_width -= step_size
            else:
                # if remaining image height or width is not greater than step_size, so it's the last slice.
                # the size of last slice should be the remaining height or width.
                slices_size.append(image_height_or_width)
                # next iteration, the while statement should exit.
                image_height_or_width -= step_size

    # ratio slice
    else:
        # make sure it's a ratio slice, other 2 arguments should be 0, or it's a invalid invoke.
        assert slice_count == 0
        assert step_size == 0
        # parse the ratio string
        ratio_list = ratio.split(':')
        ratio_list = [int(i) for i in ratio_list]
        # make sure it's a valid ratio. split by ':', the output should be a list.
        # for example, '3:2', will be ['3','2']
        assert ratio_list

        # calculation begins
        # how many parts in this ratio expression
        parts_count = len(ratio_list)
        sum = 0
        # sum all the ratio numbers
        for ratio_number in ratio_list:
            sum += ratio_number
        # calculate the base size
        base_size = int(image_height_or_width//sum)
        remainder = image_height_or_width - base_size*sum

        # distribute the remainder to all the parts.
        remainder_each = int(remainder//parts_count)
        remainder_of_remainder = remainder - remainder_each*parts_count

        # final distribute
        for part in range(parts_count):
            each_ratio_size = ratio_list[part]*base_size + remainder_each
            if remainder_of_remainder>0:
                each_ratio_size += 1
                remainder_of_remainder -=1
            slices_size.append(each_ratio_size)

    # make sure the list is not empty
    assert slices_size
    return slices_size



'''the main function to do the slice'''
# this function should not be called directly, use proxy functions instead, unless you have a strong reason to do so,
# this function only do one-direction image slice, for grid slice you should use the grid proxy functions.
# grid slice is implemented in a way of 'slice horizontal first, then for each slice, do the same vertical slice.'


def slice_image_one_direction(image,
                slice_vertical_yn = False,
                slice_horizontal_yn = False,
                slice_count_vertical = 0,
                slice_count_horizontal = 0,
                equal_slice_yn = False,
                step_slice_yn = False,
                step_horizontal = 0,
                step_vertical = 0,
                ratio_slice_yn = False,
                ratio_horizontal = '',
                ratio_vertical = ''):

    ### Make sure the arguments are valid ###

    # Since this function is not for public use directly, so we assert, and through exceptions.
    # Each time, either slice vertical, or slice horizontal, not both.
    assert slice_vertical_yn != slice_horizontal_yn
    # Either equal slice or step slice, not both, not neither.
    assert equal_slice_yn != step_slice_yn
    # make sure all the counts and steps are none negative.
    assert slice_count_vertical >= 0
    assert slice_count_horizontal >= 0
    assert step_horizontal >= 0
    assert step_vertical >= 0
    # make sure one of the counts is zero
    if equal_slice_yn:
        # equal slice, make sure only one direction has count, the other should be 0
        assert slice_count_horizontal*slice_count_vertical == 0
    if step_slice_yn:
        # step slice, make sure only one direction hsa step, the other should be 0
        assert step_vertical*step_horizontal == 0


    ### prepare the image object. ###

    # Check if image is a Image or a string, if string, try to open it, if image, do nothing.
    if isinstance(image, str):
        # The input is a string, so it should be a path, check if it's a path, then open it.
        try:
            img = Image.open(image)
        except:
            raise Exception('PIL open file error, please check if the image path provided is a valid image file.')
    else:
        if isinstance(image, Image.Image):
            # incoming object is a PIL image, do nothing.
            img = image
        else:
            raise Exception("Incoming argument 'image' is not a string or a PIL Image, please check the function arguments.")

    # assert internal variable img is a instance of PIL Image.
    assert isinstance(img, Image.Image)

    # Get the metadata of the image, the height, the width.
    img_width, img_height = img.size


    ### Slice the image

    output_slices = []

    # vertical case
    if slice_vertical_yn:
        # now it's vertical slice
        # calculate the sizes of each slice.
        slices_heights = []
        # see if it's equal slice or step slice.
        if equal_slice_yn:
            slices_heights = calculate_slices_size(img_height, slice_count=slice_count_vertical, step_size=0, ratio='')
        elif step_slice_yn:
            slices_heights = calculate_slices_size(img_height, slice_count=0, step_size=step_vertical, ratio='')
        elif ratio_slice_yn:
            slices_heights = calculate_slices_size(img_height, slice_count=0, step_size=0, ratio=ratio_vertical)
        else:
            # This exception should never be raised.
            raise Exception('slice mode error, not equal, not step, not ratio, things went very wrong, check it out.')
        # make sure it's not empty.
        assert slices_heights
        # the bounding box variables for crop
        upper = 0; left = 0; right = img_width; bottom = 0
        for slice_height in slices_heights:
            bottom += slice_height
            bbox = (left, upper, right, bottom)
            slice = img.crop(bbox)
            output_slices.append(slice)
            upper += slice_height

    # horizontal case
    else:
        # now it's horizontal slice
        # make sure it's horizontal slice.
        assert slice_horizontal_yn
        slices_widths = []
        # see if it's equal slice or step slice
        if equal_slice_yn:
            slices_widths = calculate_slices_size(img_width, slice_count=slice_count_horizontal, step_size=0, ratio='')
        elif step_slice_yn:
            slices_widths = calculate_slices_size(img_width, slice_count=0, step_size=step_horizontal, ratio='')
        elif ratio_slice_yn:
            slices_widths = calculate_slices_size(img_width, slice_count=0, step_size=0, ratio=ratio_horizontal)
        else:
            # This exception should never be raised.
            raise Exception('slice mode error, not equal, not step, not ratio, things went very wrong, check it out.')
        # make sure it's not empty
        assert slices_widths
        # the bounding box variables for crop
        upper = 0; left = 0; right = 0; bottom = img_height
        for slice_width in slices_widths:
            right += slice_width
            bbox = (left, upper, right, bottom)
            slice = img.crop(bbox)
            output_slices.append(slice)
            left += slice_width

    # return the result list.
    # make sure it's not empty.
    assert output_slices
    return output_slices

    # if the slice is horizontal/vertical only, the returned list will be a simple 1-level list.
    # if the slice is by grid, the returned list will be a list of list, each list element of the outer is a list of image in one row.
    # if not specified explicitly, the sequence of the slices is from left to right, from top to bottom.


# Proxy functions to make it easier to use, add more error proof.

def slice_horizontal_in_equal(image, horizontal_count):
    # slice horizontal
    return slice_image_one_direction(image, slice_horizontal_yn=True, equal_slice_yn=True,
                                     slice_count_horizontal=horizontal_count)

def slice_vertical_in_equal(image, vertical_count):
    # slice vertical
    return slice_image_one_direction(image, slice_vertical_yn=True, equal_slice_yn=True,
                                     slice_count_vertical=vertical_count)

def slice_horizontal_by_step(image, step_horizontal):
    return slice_image_one_direction(image, slice_horizontal_yn=True, step_slice_yn=True,
                                     step_horizontal=step_horizontal)

def slice_vertical_by_step(image, step_vertical):
    return slice_image_one_direction(image, slice_vertical_yn=True, step_slice_yn=True,
                                     step_vertical=step_vertical)

def slice_horizontal_by_ratio(image, ratio_string):
    return slice_image_one_direction(image, slice_horizontal_yn=True, ratio_slice_yn=True,
                                     ratio_horizontal=ratio_string)

def slice_vertical_by_ratio(image, ratio_string):
    return slice_image_one_direction(image, slice_vertical_yn=True, ratio_slice_yn=True,
                                     ratio_vertical=ratio_string)


# Grid slice is a little different, to make it simple, we slice twice, first horizontal, second vertical.
def slice_to_grid(image, vertical_mode, vertical_param, horizontal_mode, horizontal_param):
    # vertical_mode should not be empty.
    assert vertical_mode
    # vertical_mode should be one of the 3 values.
    assert vertical_mode in ['equal', 'step', 'ratio']
    # horizontal_mode should not be empty.
    assert horizontal_mode
    # horizontal_mode should be one of the 3 values.
    assert horizontal_mode in ['equal', 'step', 'ratio']

    # check the param, they should be valid
    if vertical_mode in ['equal', 'step']:
        # equal mode, step mode, the param should be a int.
        assert isinstance(vertical_param, int)
    else:
        # ratio mode, the param should be a string. other cases is already excluded by previous assert statement
        assert isinstance(vertical_param, str)
    if horizontal_mode in ['equal', 'step']:
        # equal mode, step mode, should be int
        assert isinstance(horizontal_param, int)
    else:
        # ratio mode, should be string.
        assert isinstance(horizontal_param, str)


    # begin horizontal slice
    horizontal_slices = []
    if horizontal_mode == 'equal':
        horizontal_slices = slice_horizontal_in_equal(image, horizontal_param)
    elif horizontal_mode == 'step':
        horizontal_slices = slice_horizontal_by_step(image, horizontal_param)
    elif horizontal_mode == 'ratio':
        horizontal_slices = slice_horizontal_by_ratio(image, horizontal_param)
    else:
        # this should never be reached.
        raise Exception('Horizontal slice mode in grid slice unknown, something went very wrong, check the code, fire a issue.')

    # make sure the output list is not empty
    assert horizontal_slices

    # output grid slices, it's supposed to be a list of list
    grid_slices = []

    # begin vertical slices, for each image in horizontal slices, slice it vertically.
    for horizontal_slice in horizontal_slices:
        # it should be a PIL image
        assert isinstance(horizontal_slice, Image.Image)

        vertical_sub_slices = []
        if vertical_mode == 'equal':
            vertical_sub_slices = slice_vertical_in_equal(image, vertical_param)
        elif vertical_mode == 'step':
            vertical_sub_slices = slice_vertical_by_step(image, vertical_param)
        elif vertical_mode == 'ratio':
            vertical_sub_slices = slice_vertical_by_ratio(image, vertical_param)
        else:
            # this should never be reached.
            raise Exception('Vertical slice mode in grid slice unknown, something went very wrong, check the code, fire a issue.')
        # make sure it's not empty
        assert vertical_sub_slices
        # append it to the output list
        grid_slices.append(vertical_sub_slices)

    # make sure it's not empty
    assert grid_slices
    # return it as a result
    return grid_slices



# Image slice file I/O functions

# helper function to save a list of PIL image to disk. Save to cwd, it's a default behaviour by most programs.
def save_image_list(in_list, out_dir, out_name, out_ext):
    count = 1
    for working_slice in in_list:
        assert isinstance(working_slice, Image.Image)
        working_slice.save(os.path.join(out_dir, out_name + "_" + str(count) + '.' + out_ext))
        count += 1

# helper function for image grid slice saving.
def save_image_grid(in_list, out_dir, out_name, out_ext):
    count = 1
    for sub_slice_list in in_list:
        assert sub_slice_list
        assert isinstance(sub_slice_list[0], Image.Image)
        save_image_list(sub_slice_list, out_dir, out_name + '_' + str(count), out_ext)
        count += 1


# Standalone sub-command functions for argparse, so it can dispatch accordingly directly without extra work.

# standalone horizontal
def standalone_horizontal_slice(arguments):
    print('horizontal')
    # equal slice case.
    if getattr(arguments, 'slice_count', False):
        print('Equal slice,' + str(arguments.slice_count))
        return slice_horizontal_in_equal(arguments.file_name, arguments.slice_count)
    # step slice
    elif getattr(arguments, 'step_size', False):
        print('STEP slice', +str(arguments.step_size))
        return slice_horizontal_by_step(arguments.file_name, arguments.step_size)
    # ratio slice
    elif getattr(arguments, 'ratio_string', False):
        print('RATIO_STRING', +str(arguments.ratio_string))
        return slice_horizontal_by_ratio(arguments.file_name, arguments.ratio_string)
    # should never reach this.
    else:
        # this exception should never be raised.
        raise Exception('-e, -s or -r, one of which should be provided.')


# Standalone vertical
def standalone_vertical_slice(arguments):
    print('vertical')
    # equal slice case.
    if getattr(arguments, 'slice_count', False):
        print('Equal slice,' + str(arguments.slice_count))
        return slice_vertical_in_equal(arguments.file_name, arguments.slice_count)
    # step slice
    elif getattr(arguments, 'step_size', False):
        print('STEP slice,' + str(arguments.step_size))
        return slice_vertical_by_step(arguments.file_name, arguments.step_size)
    # ratio slice
    elif getattr(arguments, 'ratio_string', False):
        print('RATIO_STRING,' +str(arguments.ratio_string))
        return slice_vertical_by_ratio(arguments.file_name, arguments.ratio_string)
    # should never reach this.
    else:
        # this exception should never be raised.
        raise Exception('-e, -s or -r, one of which should be provided.')


# standalone grid
def standalone_grid_slice(arguments):
    print('grid')
    # parse the input arguments, get the mode and mode_params for each direction.
    # horizontal
    if getattr(arguments, 'grid_horizontal_slice_count', False):
        horizontal_mode = 'equal'
        horizontal_param = arguments.grid_horizontal_slice_count
    elif getattr(arguments, 'grid_horizontal_step_size', False):
        horizontal_mode = 'step'
        horizontal_param = arguments.grid_horizontal_step_size
    elif getattr(arguments, 'grid_horizontal_ratio_string', False):
        horizontal_mode = 'ratio'
        horizontal_param = arguments.grid_horizontal_ratio_string
    else:
        # should never reach this.
        raise Exception('Grid slice, horizontal mode unknown, something went very wrong, check the code, fire a issue.')

    # vertical
    if getattr(arguments, 'grid_vertical_slice_count', False):
        vertical_mode = 'equal'
        vertical_param = arguments.grid_vertical_slice_count
    elif getattr(arguments, 'grid_vertical_step_size', False):
        vertical_mode = 'step'
        vertical_param = arguments.grid_vertical_step_size
    elif getattr(arguments, 'grid_vertical_ratio_string', False):
        vertical_mode = 'ratio'
        vertical_param = arguments.grid_vertical_ratio_string
    else:
        # should never reach this.
        raise Exception('Grid slice, vertical mode unknown, something went very wrong, check the code, fire a issue.')

    # do the grid slice.
    return slice_to_grid(arguments.file_name, horizontal_mode=horizontal_mode, horizontal_param=horizontal_param,
                                vertical_mode=vertical_mode, vertical_param=vertical_param)



# main function when used as a standalone app.
# mostly it's the argument declarations and parsings. It's like a dispatcher.
def main(argv):
    # Instantiate the parser
    parser = argparse.ArgumentParser(
                                     description='\'image-slice\' is a tool for easy image slice:'
                                                 ' horizontally, vertically, or by a grid.'
                                                 '\nYou can slice a image equally to a given number of slices,'
                                                 'or slice it by every N pixel, or to a given ratio like 3:2:1.',
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog = 'Usage explained:'
                                              '\n* direction: '
                                              '\n    -v or -h is for vertical or horizontal slice, one and only one should be provided.'
                                              '\n* slice mode: '
                                              '\n    -e is for equally slice, following -e you should provide how many slices '
                                              'you want, \n        For example: \'image-slice -v -e 3 someimage.jpg\', '
                                              'means slice the image vertically into 3 slices.'
                                              '\n    -s is for step slice, which means slice every N px,'
                                              '\n        For example: '
                                              '\'image-slice -h -s 200 imagefile.png\' means slice the image horizontally '
                                              'every 200px, until it\'s all sliced.'
                                              '\n    -r is for ratio slice, you can spcify a ratio, to which the image will be'
                                              ' sliced.'
                                              '\n        For example: \'slice-image -h -r 3:2:1 image.jpg\' will slice the image '
                                              'to a ratio of \'3:2:1\',\n        so 3 slices will be generated, each has a size respectively '
                                              'of the ratio 3:2:1. \n        (roughly, non-divisible pixels are distribute equally to each slice, '
                                              '1px for each)'
                                     )
    # Define argument patterns.

    # Patterns Explained:
    #   image-slice.py [FILE_NAME] vertical|horizontal| (-e SLICES, -s STEP_SIZE, -r RATIO_STRING)
    #   image-slice.py [FILE_NAME} grid (-ve, -vs, -vr) (-he, -hs, -hr)
    # The file_name is the only global top level argument, it's the image file to be slice.
    # Then we use 3 subprograms to do the vertical, horizontal, grid slice separately.
    # In each subprogram, you provide how to slice.

    # The only global argument to hold the file_name.
    parser.add_argument('file_name', metavar='FILE_NAME', help='File path of the image to be sliced.')


    # Enable the sub command feature.
    subparsers = parser.add_subparsers(dest='mode')


    # Vertical case:

    # Define a vertical sub command parser.
    vertical_sub_parser = subparsers.add_parser('vertical', aliases=['v'],
                                                help='Vertical slice mode, for help use \'image-slice vertical --help\'')
    
    # The 3 mutually exclusive arguments, indicate for 3 different slice mode.
    vertical_mode_group = vertical_sub_parser.add_mutually_exclusive_group(required=True)

    # equal slice
    vertical_mode_group.add_argument('-e', type=int, metavar='SLICE_COUNT', dest='slice_count', default=0,
                                   help='Slice equally to SLICE_COUNT parts.')
    # step slice
    vertical_mode_group.add_argument('-s', type=int, metavar='STEP_SIZE', dest='step_size', default=0,
                                   help='Slice every STEP_SIZE pixels.')
    # ratio slice
    vertical_mode_group.add_argument('-r', metavar='RATIO_STRING', dest='ratio_string', default='',
                                   help='Slice by a RATIO_STRING like 3:2:1')
    

    # Horizontal case:

    # Define vertical sub command parser. 
    horizontal_sub_parser = subparsers.add_parser('horizontal', aliases=['h'],
                                                help='Horizontal slice mode, for help use \'image-slice horizontal --help\'')

    # The 3 mutually exclusive arguments, indicate for 3 different slice mode.
    horizontal_mode_group = horizontal_sub_parser.add_mutually_exclusive_group(required=True)

    # equal slice
    horizontal_mode_group.add_argument('-e', type=int, metavar='SLICE_COUNT', dest='slice_count', default=0,
                                     help='Slice equally to SLICE_COUNT parts.')
    # step slice
    horizontal_mode_group.add_argument('-s', type=int, metavar='STEP_SIZE', dest='step_size', default=0,
                                     help='Slice every STEP_SIZE pixels.')
    # ratio slice
    horizontal_mode_group.add_argument('-r', metavar='RATIO_STRING', dest='ratio_string', default='',
                                     help='Slice by a RATIO_STRING like 3:2:1')



    # Grid case:

    # Grid slice has a totally different argument rule.
    # In the grid case, the sub command takes arguments like this:
    # image-slice.py [FILE_NAME] grid (-ve SLICES_NUM, -vs STEP_SIZE, -vr RATIO_STR) (-he SLICES_NUM, -hs STEP_SIZE, -hr RATIO_STR)
    # Both direction should be specified, because it's a grid.
    # The program will slice the image in each direction accordingly.

    # Define a grid sub command parser.
    grid_parser = subparsers.add_parser('grid', aliases = ['g'],
                                        help='Grid slice mode, for help use \'image-slice grid --help\'')

    # Vertical command, define a mutually exclusive argument group.
    group_grid_vertical_e_or_s_or_r = grid_parser.add_mutually_exclusive_group(required=True)
    # 3 cases of slice mode.
    group_grid_vertical_e_or_s_or_r.add_argument('-ve', '--vertical-equal', type=int,
                                                 metavar='VERTICAL_SLICE_COUNT',
                                                 dest='grid_vertical_slice_count',
                                                 default=0,
                                                 help='Grid VERTICAL: Slice equally to VERTICAL_SLICE_COUNT slices in vertical.'
                                                 )
    group_grid_vertical_e_or_s_or_r.add_argument('-vs', '--vertical-step', type=int,
                                                 metavar = 'VERTICAL_STEP_SIZE',
                                                 dest = 'grid_vertical_step_size',
                                                 default=0,
                                                 help='Grid VERTICAL: Slice every VERTICAL_STEP_SIZE pixels in vertical.'
                                                 )
    group_grid_vertical_e_or_s_or_r.add_argument('-vr', '--vertical-ratio',
                                                 metavar='VERTICAL_RATIO_STRING', dest='grid_vertical_ratio_string',
                                                 default='',
                                                 help='Grid VERTICAL: Slice by a RATIO_STRING like 3:2:1 in vertical.')

    # Horizontal command, define a mutually exclusive argument group.
    group_grid_horizontal_e_or_s_or_r = grid_parser.add_mutually_exclusive_group(required=True)
    # 3 cases of slice mode.
    group_grid_horizontal_e_or_s_or_r.add_argument('-he', '--horizontal-equal', type=int,
                                                 metavar='HORIZONTAL_SLICE_COUNT',
                                                 dest='grid_horizontal_slice_count',
                                                 default=0,
                                                 help='Grid HORIZONTAL: Slice equally to HORIZONTAL_SLICE_COUNT slices in horizontal.'
                                                 )
    group_grid_horizontal_e_or_s_or_r.add_argument('-hs', '--horizontal-step', type=int,
                                                 metavar='HORIZONTAL_STEP_SIZE',
                                                 dest='grid_horizontal_step_size',
                                                 default=0,
                                                 help='Grid HORIZONTAL: Slice every HORIZONTAL_STEP_SIZE pixels in horizontal.'
                                                 )
    group_grid_horizontal_e_or_s_or_r.add_argument('-hr', '--horizontal-ratio',
                                                 metavar='HORIZONTAL_RATIO_STRING', dest='grid_horizontal_ratio_string',
                                                 default='',
                                                 help='Grid HORIZONTAL: Slice by a RATIO_STRING like 3:2:1 in horizontal.')


    # Set subprogram dispatch functions.
    # Argparser will parse the args, and invoke the correspond function.
    vertical_sub_parser.set_defaults(func=standalone_vertical_slice)
    horizontal_sub_parser.set_defaults(func=standalone_horizontal_slice)
    grid_parser.set_defaults(func = standalone_grid_slice)


    # Argument parsing begins

    # Parse the incoming arguments
    # argv is the parameter name of this main(argv) function, default to None, so other program can call it directly.
    if argv:
        # argv is not none, it's the case the main() is called directly from another module, not from command-line.
        arguments = parser.parse_args(argv)
    else:
        # called directly from command-line, it's the case this module is executed directly.
        # parse call with no args will handle the 2 command situation properly, like python imageslice.py
        # otherwise the second command, in this case it's the script name, will be recognized to first real argument.
        arguments = parser.parse_args()
    print(arguments)
    # arguments should not be empty.
    assert arguments
    # the name of image file to be sliced, should not be empty.
    assert arguments.file_name
    print(arguments.file_name)


    # dispatch the execution to the sub functions accordingly.
    output_slices = arguments.func(arguments)

    # make sure output_slices is not empty.
    assert output_slices

    # get current working directory as the output dir. later we will pass the it to the file saving functions.
    working_dir = os.getcwd()
    # get the pure file name of the input file, input may be a path, so we have to make sure path part not there.
    file_name_original = os.path.basename(arguments.file_name)
    # split the original file name to a list, separated by '.'
    file_name_splitted = file_name_original.split('.')
    # get the last element of the list, which should be the ext name.
    file_name_ext = str(file_name_splitted.pop())
    # join remaining elements in the list, if any, in case the original file name contains '.'
    file_name_without_ext = ''.join(file_name_splitted)

    # save the output slices to current working directory
    if isinstance(output_slices[0], Image.Image):
        # it's a list of Images, save this list.
        save_image_list(output_slices, working_dir, file_name_without_ext, file_name_ext)
    else:
        # it should be a list of list, confirm it, save the list of list.
        assert isinstance(output_slices[0], list)
        save_image_grid(output_slices, working_dir, file_name_without_ext, file_name_ext)

    # everything's done, print success message, return 0.
    print('Slice completed, check current directory, slices should already be there.')
    return 0




if __name__ == "__main__":
    # When image-slice.py is called directly from the command line, argparse should fetch the args directly.
    # That is because if a command is a 2-word combination, like 'python image-slice.py',
    # it will not be treated as a single 2-word command, but a 1-word command and a argument.
    # But if it's fetched directly, this case will be fine.
    # 'python image-slice.py' will be treated as a whole command in the argv[0],
    # not 'python' in argv[0], 'image-slice.py' in argv[1] as the first argument.
    main(argv=None)

























