import os
import argparse
from PIL import Image


# return a list, in which contains the calculated width/height of each slice.
def _calculate_slices_size(image_height_or_width, slice_count, step_size, ratio):
    """helper function, calculates the width/height of each output slices, return a list of them.

    Args:
        image_height_or_width: positive int
        slice_count: positive int
        step_size: positive int
        ratio: a string separated by ':', like '2:1:3'

    Returns:
        A list of int, represents the width or height of each output slices.
        So the caller can directly iterate through the list regardless of how the size is calculated.
        Future if someone is going to provide a better calculation algorithm, just modify here.

    Raises:
        AssertionError: if one of the impossible happens.

    """

    # arguments parsing
    # all numeric arguments should be numeric,
    assert isinstance(image_height_or_width, int)
    assert isinstance(slice_count, int)
    assert isinstance(step_size, int)
    # and they are all greater than 0.
    assert image_height_or_width > 0
    assert slice_count >= 0
    assert step_size >= 0

    # Ratio string should be a str
    assert isinstance(ratio, str)

    # slice_count, step_size and ratio, one of the 3 should be True, all the others should be False (0 or '')
    # this is done in each case below.

    slices_size = []
    # equal slice
    if slice_count:
        # equal slice, the step_size should be zero, ratio should be an empty string, or it's a invalid invoke.
        assert step_size == 0
        assert not ratio
        # begin the calculation.
        base_size = int(image_height_or_width // slice_count)
        remainder = image_height_or_width - base_size * slice_count
        for img_slice in range(slice_count):
            if remainder > 0:
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

        while image_height_or_width > 0:
            if image_height_or_width >= step_size:
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
        ratio_sum = 0
        # sum all the ratio numbers
        for ratio_number in ratio_list:
            ratio_sum += ratio_number
        # calculate the base size
        base_size = int(image_height_or_width // ratio_sum)
        remainder = image_height_or_width - base_size * ratio_sum

        # distribute the remainder to all the parts.
        remainder_each = int(remainder // parts_count)
        remainder_of_remainder = remainder - remainder_each * parts_count

        # final distribute
        for part in range(parts_count):
            each_ratio_size = ratio_list[part] * base_size + remainder_each
            if remainder_of_remainder > 0:
                each_ratio_size += 1
                remainder_of_remainder -= 1
            slices_size.append(each_ratio_size)

    # make sure the list is not empty
    assert slices_size
    return slices_size


def _slice_image_one_direction(
        image,
        slice_vertical_yn=False,
        slice_horizontal_yn=False,
        slice_count_vertical=0,
        slice_count_horizontal=0,
        equal_slice_yn=False,
        step_slice_yn=False,
        step_horizontal=0,
        step_vertical=0,
        ratio_slice_yn=False,
        ratio_horizontal='',
        ratio_vertical=''):
    """The main function to do the slice

    This function should not be called directly, use proxy API functions instead, unless you have a reason to.
    This function only does one-direction image slice, for grid slice, check the grid proxy API functions.
    The grid slice is implemented in a way of 'slice horizontally first, then for each slice, slice vertically.'

    Args:
        image: a path string or a PIL image object.
        slice_vertical_yn: True if vertical slice.
        slice_horizontal_yn: True if horizontal slice.
        slice_count_vertical: In equal slice mode, how many slices do you want, vertically.
        slice_count_horizontal: In equal slice mode, how many slices do you want, horizontally.
        equal_slice_yn: True if it's equal slice.
        step_slice_yn: True if it's step slice.
        step_horizontal: In step slice mode, how many pixels do you want for each slice, horizontally.
        step_vertical: In step slice mode, how many pixels do you want for each slice, vertically.
        ratio_slice_yn: True if it's ratio slice.
        ratio_horizontal: A ratio string, multiple numbers separated by ':' , like this: 3:2:1.
            tells the program to what ratio the slices should be, horizontally.
        ratio_vertical: A ratio string, multiple numbers separated by ':' , like this: 3:2:1.
            tells the program to what ratio the slices should be, vertically.

    Returns:
        A list of PIL Image objects.
        Each Image object is a output slice.

    Raises:
        TypeError:
            If 'image' is not a string nor a PIL Image object, or other numeric parameters is not a int.
        IOError:
            If 'image' is a string, but PIL cannot open it. PIL will raise it, check the path and the file.
        ValueError:
            If numeric parameters used in current mode is not greater than 0.
            Or it's the equal slice, but expected slices count is smaller than image width (in pixel).
            Or it's the ratio slice, but incoming ratio string is not a valid ratio string.


    """
    # Make sure the arguments are valid #

    # Since this function is not for public use directly, so we assert, and through exceptions.

    # Each time, either slice vertical, or slice horizontal, not both.
    assert slice_vertical_yn != slice_horizontal_yn

    # It's either slice equal, by step, or by ratio. not both.
    # If one of equal_slice or step_slice is true, the other should be false, and ratio_yn should be false.
    if equal_slice_yn or step_slice_yn:
        assert equal_slice_yn != step_slice_yn
        assert not ratio_slice_yn
    # Both equal_slice_yn and step_slice_yn is false, so the ratio_slice_yn should be True.
    else:
        # in this case ratio_slice should be true, or it's something really wrong.
        assert ratio_slice_yn

    # make sure all the numeric parameters are of type of int, or a valueError should be raised to the API users.
    if not isinstance(slice_count_vertical, int):
        raise ValueError('slice_count_vertical should be a int, check the function arguments.')
    elif not slice_count_vertical >= 0:
        raise ValueError('slice_count_vertical should be greater than 0, check the function arguments.')
    else:
        pass
    
    if not isinstance(slice_count_horizontal, int):
        raise ValueError('slice_count_horizontal should be a int, check the function arguments.')
    elif not slice_count_horizontal >= 0:
        raise ValueError('slice_count_horizontal should be greater than 0, check the function arguments.')
    else:
        pass
    
    if not isinstance(step_horizontal, int):
        raise ValueError('step_horizontal should be a int, check the function arguments.')
    elif not step_horizontal >= 0:
        raise ValueError('step_horizontal should be greater than 0, check the function arguments.')
    else:
        pass
    
    if not isinstance(step_vertical, int):
        raise ValueError('step_vertical should be a int, check the function arguments.')
    elif not step_vertical >= 0:
        raise ValueError('step_vertical should be greater than 0, check the function arguments.')
    else:
        pass

    # make sure all the counts and steps are none negative.
    assert slice_count_vertical >= 0
    assert slice_count_horizontal >= 0
    assert step_horizontal >= 0
    assert step_vertical >= 0

    # make sure only one of the two directions has a non-zero value.
    if equal_slice_yn:
        # equal slice, make sure only one direction has a value, the other should be 0
        assert slice_count_horizontal * slice_count_vertical == 0
        # make sure they are not both 0
        assert slice_count_horizontal != slice_count_vertical
    if step_slice_yn:
        # step slice, make sure only one direction hsa a value, the other should be 0
        assert step_vertical * step_horizontal == 0
        # make sure they are not both zero
        assert step_vertical != step_horizontal

    # Ratio slice, make sure 1 and only 1 of horizontal or vertical ratio has proper value.
    if ratio_slice_yn:
        # one of the ratio string should be True, (not empty)
        assert ratio_horizontal or ratio_vertical
        # they cannot both be True.
        assert not (ratio_vertical and ratio_horizontal)
        # if it's horizontal, check if the ratio string is a proper ratio string.
        if ratio_horizontal:
            temp_ratio_list = ratio_horizontal.split(':')
            print(temp_ratio_list)
            # We do not assert, but try and raise a exception,
            # because exception can provide more error message than a assertion, here is input check, not a assert.
            # the list elements should not be empty, so we can exclude the cases like: '1:3:' which will be '1','3',''
            if not all(temp_ratio_list):
                raise ValueError("Ratio string '" + ratio_horizontal + "' is not a valid ratio, check if it's a typo."
                                 + "The ratio numbers should be separated by only one ':' in between, not multiple. "
                                 + "Also check if there are any leading or following ':' in your ratio string. "
                                 + "It should be something like '3:2:1', not something strange.")
            # nor the ratio elements be a non-integer.
            temp_ratio_error_non_int = [s for s in temp_ratio_list if not s.isdigit()]
            if temp_ratio_error_non_int:
                raise ValueError("Ratio string '" + ratio_horizontal + "' is not a valid ratio, '"
                                 + str(temp_ratio_error_non_int) +
                                 "' is not a number, a ratio should consist of pure numbers.")
            # nor the ratio elements be a ZERO or negative.
            temp_ratio_error_zero = [int(s) for s in temp_ratio_list if int(s) <= 0]
            if temp_ratio_error_zero:
                raise ValueError("Ratio string '" + ratio_horizontal +
                                 "' has at least one '0' as a ratio number, "
                                 "a valid ratio should not contain any 0 or negative because it's meaningless. "
                                 "Check if it's a typo.")
        # if it's vertical, check the vertical ratio string, make sure it's a valid ratio.
        elif ratio_vertical:
            temp_ratio_list = ratio_vertical.split(':')
            # We do not assert, but try and raise a exception,
            # because exception can provide more error message than a assertion, here is input check, not a assert.
            # the list elements should not be empty, so we can exclude the cases like: '1:3:' which will be '1','3',''
            if not all(temp_ratio_list):
                raise ValueError("Ratio string '" + ratio_vertical + "' is not a valid ratio, check if it's a typo."
                                 + "The ratio numbers should be separated by only one ':' in between, not multiple. "
                                 + "Also check if there are any leading or following ':' in your ratio string. "
                                 + "It should be something like '3:2:1', not something strange.")
            # nor the ratio elements be a non-integer.
            temp_ratio_error_non_int = [s for s in temp_ratio_list if not s.isdigit()]
            if temp_ratio_error_non_int:
                raise ValueError("Ratio string '" + ratio_vertical + "' is not a valid ratio, '"
                                 + str(temp_ratio_error_non_int) +
                                 "' is not a number, a ratio should consist of pure numbers.")
            # nor the ratio elements be a ZERO or negative.
            temp_ratio_error_zero = [int(s) for s in temp_ratio_list if int(s) <= 0]
            if temp_ratio_error_zero:
                raise ValueError("Ratio string '" + ratio_vertical +
                                 "' has at least one '0' as a ratio number, "
                                 "a valid ratio should not contain any 0 or negative, because it's meaningless. "
                                 "Check if it's a typo.")
        else:
            # This should never be reached.
            raise ValueError("Neither ratio_vertical nor ratio_horizontal is provided, "
                             "previous assertion fails, it's impossible, check the code.")

    # prepare the image object. #

    # Check if image is a Image or a string, if string, try to open it, if image, do nothing.
    if isinstance(image, str):
        # The input is a string, so it should be a path, check if it's a path, then open it.
        try:
            img = Image.open(image)
        except IOError:
            raise IOError('PIL open file error, please check if the image path provided is a valid image file.')
    else:
        if isinstance(image, Image.Image):
            # incoming object is a PIL image, do nothing.
            img = image
        else:
            raise TypeError(
                "Incoming argument 'image' is not a string or a PIL Image, please check the function arguments.")

    # assert internal variable img is a instance of PIL Image.
    assert isinstance(img, Image.Image)

    # Get the metadata of the image, the height, the width.
    img_width, img_height = img.size

    # Slice the image

    output_slices = []

    # vertical case
    if slice_vertical_yn:
        # now it's vertical slice
        # calculate the sizes of each slice.
        # see if it's equal slice or step slice.
        if equal_slice_yn:
            # the expected number of slices should not be greater than the image width/height (in pixels)
            if slice_count_vertical > img_height:
                raise ValueError('In equal slice, the expected number of vertical slices is greater than image height'
                                 '(in pixels), it\'s impossible to slice like this, check your input.')
            slices_heights = _calculate_slices_size(img_height, slice_count=slice_count_vertical, step_size=0, ratio='')
        elif step_slice_yn:
            slices_heights = _calculate_slices_size(img_height, slice_count=0, step_size=step_vertical, ratio='')
        elif ratio_slice_yn:
            slices_heights = _calculate_slices_size(img_height, slice_count=0, step_size=0, ratio=ratio_vertical)
        else:
            # This exception should never be raised.
            raise ValueError('slice mode error, not equal, not step, not ratio, things went very wrong, check it out.')
        # make sure it's not empty.
        assert slices_heights
        # the bounding box variables for crop
        upper = 0
        left = 0
        right = img_width
        bottom = 0
        for slice_height in slices_heights:
            bottom += slice_height
            bbox = (left, upper, right, bottom)
            image_slice = img.crop(bbox)
            output_slices.append(image_slice)
            upper += slice_height

    # horizontal case
    else:
        # now it's horizontal slice
        # make sure it's horizontal slice.
        assert slice_horizontal_yn
        # see if it's equal slice or step slice
        if equal_slice_yn:
            # the expected number of slices should not be greater than the image width/height (in pixels)
            if slice_count_horizontal > img_width:
                raise ValueError('In equal slice, the expected number of horizontal slices is greater than image width'
                                 '(in pixels), it\'s impossible to slice like this, check your input.')
            slices_widths = _calculate_slices_size(img_width, slice_count=slice_count_horizontal, step_size=0, ratio='')
        elif step_slice_yn:
            slices_widths = _calculate_slices_size(img_width, slice_count=0, step_size=step_horizontal, ratio='')
        elif ratio_slice_yn:
            slices_widths = _calculate_slices_size(img_width, slice_count=0, step_size=0, ratio=ratio_horizontal)
        else:
            # This exception should never be raised.
            raise ValueError('slice mode error, not equal, not step, not ratio, things went very wrong, check it out.')
        # make sure it's not empty
        assert slices_widths
        # the bounding box variables for crop
        upper = 0
        left = 0
        right = 0
        bottom = img_height
        for slice_width in slices_widths:
            right += slice_width
            bbox = (left, upper, right, bottom)
            image_slice = img.crop(bbox)
            output_slices.append(image_slice)
            left += slice_width

    # return the result list.
    # make sure it's not empty.
    assert output_slices
    return output_slices

    # if the slice is horizontal/vertical only, the returned list will be a simple 1-level list.
    # if the slice is by grid, the returned list will be a list of list,
    #       each list element of the outer is a list of image in one row.
    # if not specified explicitly, the sequence of the slices is from left to right, from top to bottom.


# Public API: Proxy functions to make it easier to use, add more error proof.

def slice_horizontal_in_equal(image, horizontal_count):
    """Slices a image horizontally into equal parts.

    Slice a given image provided in the 'image' parameter, into 'horizontal_count' equal parts, horizontally.

    Param 'image' is either a path string or a PIL image, if it's is a path string, it will be opened by PIL.
    If it's a PIL Image object, it will be sliced directly.

    For example:
        If the 'image' is a 500*400px image, 'horizontal_count' is 3, three slices will be generated.
        The size of each is approximately 'equal', because in most cases the image height is not divisible by
        the expected 'horizontal_count', the remainders will be distributed to the leading slices 1px for each.
        So the slices will be 167*400, 167*400, 166*400. Because 500 = 166*3 + 2 .

    Args:
        image:
            a string to the image path, or a PIL Image object.
        horizontal_count:
            a int, how many slices you want to produce.

    Returns:
        A List of PIL image objects:
            [Image_object(slice 1), Image_object(slice 1), ... , Image_object(slice N)]

    Raises:
        TypeError:
            If 'image' is not a string nor a PIL Image object, or 'horizontal_count' is not a int.
        IOError:
            If PIL cannot open the image from the path in the 'image'.
        ValueError:
            If 'horizontal_count' is not greater than 0.
            Or if 'horizontal_count' is greater than the width (in pixel) of 'image'

    """
    # slice horizontal
    return _slice_image_one_direction(image, slice_horizontal_yn=True, equal_slice_yn=True,
                                      slice_count_horizontal=horizontal_count)


def slice_vertical_in_equal(image, vertical_count):
    """Slices a image horizontally into equal parts.

    Slice a given image provided in the 'image' parameter, into 'vertical_count' equal parts, vertically.

    Param 'image' is either a path string or a PIL image, if it's is a path string, it will be opened by PIL.
    If it's a PIL Image object, it will be sliced directly.

    For example:
        If the 'image' is a 500*400px image, 'vertical_count' is 3, three slices will be generated.
        The size of each is approximately 'equal', because in most cases the image height is not divisible by
        the expected 'vertical_count', the remainders will be distributed to the leading slices 1px for each.
        So the slices will be 500*134, 500*133, 500*133. Because 400 = 133*3 + 1 .

    Args:
        image:
            a string to the image path, or a PIL Image object.
        vertical_count:
            a int, how many slices you want to produce.

    Returns:
        A List of PIL image objects:
            [Image_object(slice 1), Image_object(slice 1), ... , Image_object(slice N)]

    Raises:
        TypeError:
            If 'image' is not a string nor a PIL Image object, or 'vertical_count' is not a int.
        IOError:
            If PIL cannot open the image from the path in the 'image'.
        ValueError:
            If 'horizontal_count' is not greater than 0.
            Or if 'vertical_count' is greater than the height (in pixel) of 'image'

    """
    # slice vertical
    return _slice_image_one_direction(image, slice_vertical_yn=True, equal_slice_yn=True,
                                      slice_count_vertical=vertical_count)


def slice_horizontal_by_step(image, step_horizontal):
    """Slices a image horizontally every N pixels.

    Slice a given image provided by the 'image' parameter, every 'step_horizontal' px.

    Param 'image' is either a path string or a PIL image, if it's is a path string, it will be opened by PIL.
    If it's a PIL Image object, it will be sliced directly.

    For example:
        If the 'image' is a 500*400px image, 'step_horizontal' is 150, 4 slices will be produced,
        the size of each slice will be: 150*400, 150*400, 150*400, 50*400.

    Args:
        image:
            a string to the image path, or a PIL Image object.
        step_horizontal:
            a int, the exact number of pixels you want in each slices.

    Returns:
        A List of PIL image objects:
            [Image_object(slice 1), Image_object(slice 1), ... , Image_object(slice N)]

    Raises:
        TypeError:
            If 'image' is not a string nor a PIL Image object, or 'vertical_count' is not a int.
        IOError:
            If PIL cannot open the image from the path in the 'image'.
        ValueError:
            If 'step_horizontal' is not a positive integer.

    """
    return _slice_image_one_direction(image, slice_horizontal_yn=True, step_slice_yn=True,
                                      step_horizontal=step_horizontal)


def slice_vertical_by_step(image, step_vertical):
    """Slices a image vertically every N pixels.

    Slice a given image provided by the 'image' parameter, every 'step_horizontal' px.

    Param 'image' is either a path string or a PIL image, if it's is a path string, it will be opened by PIL.
    If it's a PIL Image object, it will be sliced directly.

    For example:
        If the 'image' is a 500*400px image, 'step_vertical' is 150, 3 slices will be produced,
        the size of each slice will be: 500*150, 500*150, 500*100.

    Args:
        image:
            a string to the image path, or a PIL Image object.
        step_vertical:
            a int, the specific number of pixels you want each slice be.

    Returns:
        A List of PIL image objects:
            [Image_object(slice 1), Image_object(slice 1), ... , Image_object(slice N)]

    Raises:
        TypeError:
            If 'image' is not a string nor a PIL Image object, or 'vertical_count' is not a int.
        IOError:
            If PIL cannot open the image from the path in the 'image'.
        ValueError:
            If 'step_vertical' is not a positive integer.

    """
    return _slice_image_one_direction(image, slice_vertical_yn=True, step_slice_yn=True,
                                      step_vertical=step_vertical)


def slice_horizontal_by_ratio(image, ratio_string):
    """Slices a image horizontally by a given ratio.

    Slice a given image provided by the 'image' parameter,
    to a given ratio provided in the 'ratio_string', horizontally.

    Param 'image' is either a path string or a PIL image, if it's is a path string, it will be opened by PIL.
    If it's a PIL Image object, it will be sliced directly.

    For example:
        If the 'image' is a 500*400px image, 'ratio_string' is '3:2', 2 slices will be produced,
        the size of each slice will be: 300*400, 200*400.

        When the image width is not divisible by the sum of ratio numbers, the remainder will be distributed evenly
        to all slices, from left to right, 1px for each, if there still any, repeat it, until it's all clear.

        So if 'image' is a 500*400px image, 'ratio_string' is '2:1', 2 slices will be produced,
        the size of each slice will be: 333*400, 167*400.
        Because 500 = 166*(2+1) + 2 , the first 1 of the remainder 2 is added to the first slice,
        there still has 1 left in the remainder, so it's added to the second slice.
        The final width of each slice is, 166*2+1 = 333, 166*1+1 = 167

    Args:
        image:
            a string to the image path, or a PIL Image object.
        ratio_string:
            a string, in a form of several positive integers separated by ':', like this 3:2:1

    Returns:
        A List of PIL image objects:
            [Image_object(slice 1), Image_object(slice 1), ... , Image_object(slice N)]

    Raises:
        TypeError:
            If 'image' is not a string nor a PIL Image object, or 'vertical_count' is not a int.
            If 'ratio_string' is not a string.
        IOError:
            If PIL cannot open the image from the path in the 'image'.
        ValueError:
            If 'ratio_string' is not in the valid form. It should something be like this: 3:2:1
            No trailing or leading ':'s, no 0s, no negatives, no decimals.

    """
    return _slice_image_one_direction(image, slice_horizontal_yn=True, ratio_slice_yn=True,
                                      ratio_horizontal=ratio_string)


def slice_vertical_by_ratio(image, ratio_string):
    """Slices a image vertically by a given ratio.

    Slice a given image provided by the 'image' parameter, to a given ratio provided in the 'ratio_string', vertically.

    Param 'image' is either a path string or a PIL image, if it's is a path string, it will be opened by PIL.
    If it's a PIL Image object, it will be sliced directly.

    For example:
        If the 'image' is a 500*400px image, 'ratio_string' is '3:2', 2 slices will be produced,
        the size of each slice will be: 500*240, 500*160.

        When the image height is not divisible by the sum of ratio numbers, the remainder will be distributed evenly
        to all slices, from up to bottom, 1px for each, if there still any, repeat it, until it's all clear.

        So if 'image' is a 500*400px image, 'ratio_string' is '2:1', 2 slices will be produced,
        the size of each slice will be: 500*267, 500*133.
        Because 400 = 133*(2+1) + 1 , the remainder 1 is added to the first slice, the height of which is 133*2 + 1


    Args:
        image:
            a string to the image path, or a PIL Image object.
        ratio_string:
            a string, in a form of several positive integers separated by ':', like this 3:2:1

    Returns:
        A List of PIL image objects:
            [Image_object(slice 1), Image_object(slice 1), ... , Image_object(slice N)]

    Raises:
        TypeError:
            If 'image' is not a string nor a PIL Image object, or 'vertical_count' is not a int.
            If 'ratio_string' is not a string.
        IOError:
            If PIL cannot open the image from the path in the 'image'.
        ValueError:
            If 'ratio_string' is not in the valid form. It should something be like this: 3:2:1
            No trailing or leading ':'s, no 0s, no negatives, no decimals.

    """
    return _slice_image_one_direction(image, slice_vertical_yn=True, ratio_slice_yn=True,
                                      ratio_vertical=ratio_string)


# Grid slice is a little different, to make it simple, we slice twice, first horizontal, second vertical.
def slice_to_grid(image, horizontal_mode, horizontal_param, vertical_mode, vertical_param):
    """Slices a given image to a grid

    Slice a given image to a given grid. 'Grid' here means slice it both vertically and horizontally.

    A simple grid is something like '3*2', by saying it, what we actually mean is,
    'horizontally slice it to 3 equal parts, then vertically slice it to 2 equal parts.'

    Since we have 3 different slice mode in each direction, here we 'extend' the meaning of 'grid' a little bit,
    you can separately specify in each direction how you would like the image to be sliced, you can use any combination.

    For example:
        1. Simple grid, slice the image to '3*2' grid.
               Call like this:  slice_to_grid(your_image, 'equal', 3, 'equal', 2)

        2. Slice the image horizontally to 3 equal parts, vertically by every 100px.
               Call like this:  slice_to_grid(your_image, 'equal', 3, 'step', 100)

        3. Slice the image horizontally to a ratio of '2:1', vertically by every 50px.
               Call like this:  slice_to_grid(your_image, 'ratio', '2:1', 'step', 50)

        4. Slice the image to 100px*100px tiles.
               Call like this:  slice_to_grid(your_image, 'step', 100, 'step', 100)

    Grid slice is performed in a way of slicing in each direction consecutively,
    so the 3 slice modes ('equal', 'step', 'ratio') have exactly the same meaning with horizontal/vertical slice.

    For a detailed explanation on each mode, check the docs of horizontal/vertical slice functions.


    Args:
        image:
            a string to the image path, or a PIL Image object.
            If it's is a path string, it will be opened by PIL. If it's a PIL Image object, it will be used directly.
        horizontal_mode:
            a string, the value of which should be either 'equal' or 'step' or 'ratio'.
            it means how you would like the image to be sliced horizontally.
        horizontal_param:
            If 'horizontal_mode' is 'equal', it should be a int, which means 'horizontal_count',
                it's the number of slices you would like to have.
            If 'horizontal_mode' is 'step', it should be a int, which means 'horizontal_step',
                it's the number of pixels you would like each of the slices to have.
            If 'horizontal_mode' is 'ratio', it should be a string, which means 'horizontal_ratio',
                it's the ratio you want the image to be sliced to in horizontal.
        vertical_mode:
            a string, the value of which should be either 'equal' or 'step' or 'ratio'.
            it means how you would like the image to be sliced vertically.
        vertical_param:
            If 'vertical_mode' is 'equal', it should be a int, which means 'vertical_count',
                it's the number of slices you would like to have.
            If 'vertical_mode' is 'step', it should be a int, which means 'vertical_step',
                it's the number of pixels you would like each of the slices to have.
            If 'vertical_mode' is 'ratio', it should be a string, which means 'vertical_ratio',
                it's the ratio you want the image to be sliced to in vertical.


    Returns:
        A List of List of PIL Image objects.
        Each list element stands for a single row of the output image grid.
        If the output slices have N slices in horizontal, M slices in vertical, it would be like this:

            [[Image_row_1_col_1, Image_row_1_col_2, ... , Image_row_1_col_N],
             [Image_row_2_col_1, Image_row_2_col_2, ... , Image_row_2_col_N],
             ...,
             [Image_row_M_col_1, Image_row_M_col_2, ... , Image_row_M_col_N]]

    Raises:
        TypeError:
            If 'image' is not a string nor a PIL Image object.
            If 'vertical_mode' or 'horizontal_mode' is not a string,
            If 'horizontal_param' or 'vertical_param' is not the required type to it's mode.
                When it's 'equal', 'step', it should be int, if it's 'ratio', it should be str.
        IOError:
            If PIL cannot open the image from the path in the 'image'.
        ValueError:
            If 'vertical_mode' or 'horizontal_mode' is not one of 'equal' or 'step' or 'ratio'.
            If 'horizontal_param' or 'vertical_param' is not the proper value according to it's mode.

    """
    # parameter validation
    if not vertical_mode:
        raise ValueError('\'vertical_mode\' should not be empty in grid slice, that\'s how you slice vertically')
    if not isinstance(vertical_mode, str):
        raise TypeError('\'vertical_mode\' should be a string.')
    if vertical_mode not in ['equal', 'step', 'ratio']:
        raise ValueError('\'vertical_mode\' should either be one of the 3 values: equal, step, ratio .')
    
    if not horizontal_mode:
        raise ValueError('\'horizontal_mode\' should not be empty in grid slice, that\'s how you slice horizontally')
    if not isinstance(horizontal_mode, str):
        raise TypeError('\'horizontal_mode\' should be a string.')
    if horizontal_mode not in ['equal', 'step', 'ratio']:
        raise ValueError('\'horizontal_mode\' should either be one of the 3 values: equal, step, ratio .')
    
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
        if not isinstance(vertical_param, int):
            raise TypeError('When \'vertical_mode\' is \'equal\' or \'step\', the \'vertical_param\' should be a int.')
        if not vertical_param > 0:
            raise ValueError('When \'vertical_mode\' is \'equal\' or \'step\','
                             ' the \'vertical_param\' should be greater than 0.')
    else:
        # ratio mode, the param should be a string. other cases is already excluded by previous assert statement
        assert isinstance(vertical_param, str)
    if horizontal_mode in ['equal', 'step']:
        # equal mode, step mode, should be int
        assert isinstance(horizontal_param, int)
    else:
        # ratio mode, should be string.
        assert isinstance(horizontal_param, str)

    # begin vertical slice
    if vertical_mode == 'equal':
        vertical_slices = slice_vertical_in_equal(image, vertical_param)
    elif vertical_mode == 'step':
        vertical_slices = slice_vertical_by_step(image, vertical_param)
    elif vertical_mode == 'ratio':
        vertical_slices = slice_vertical_by_ratio(image, vertical_param)
    else:
        # this should never be reached.
        raise ValueError(
            'vertical slice mode in grid slice unknown, something went very wrong, check the code, fire a issue.')

    # make sure the output list is not empty
    assert vertical_slices

    # output grid slices, it's supposed to be a list of list
    grid_slices = []

    # begin vertical slices, for each image in horizontal slices, slice it vertically.
    for vertical_slice in vertical_slices:
        # it should be a PIL image
        assert isinstance(vertical_slice, Image.Image)

        if horizontal_mode == 'equal':
            horizontal_sub_slices = slice_horizontal_in_equal(vertical_slice, horizontal_param)
        elif horizontal_mode == 'step':
            horizontal_sub_slices = slice_horizontal_by_step(vertical_slice, horizontal_param)
        elif horizontal_mode == 'ratio':
            horizontal_sub_slices = slice_horizontal_by_ratio(vertical_slice, horizontal_param)
        else:
            # this should never be reached.
            raise ValueError(
                'horizontal slice mode in grid slice unknown, something went very wrong, check the code, fire a issue.')
        # make sure it's not empty
        assert horizontal_sub_slices
        # append it to the output list
        grid_slices.append(horizontal_sub_slices)

    # make sure it's not empty
    assert grid_slices
    # return it as a result
    return grid_slices


# Public API: Image slice file I/O helper functions

# helper function to save a list of PIL image to disk. Save to cwd, it's a default behaviour by most programs.
def save_image_list(in_list, out_dir, out_name, out_ext):
    """saves a list of PIL image to a directory

    A helper function to save a image list more easily.

    Args:
        in_list:
            A list of PIL Image objects.
        out_dir:
            A valid path string, to where the files would be written to.
        out_name:
            A String, the file name prefix you would like to save.
            The output file names will be: out_name_1, out_name_2, ...
        out_ext:
            The file extension name, like jpg, png, ...

    Returns:
        All the images in 'in_list' will be saved to 'out_dir', one by one.
        The file names will be 'out_name_1.out_ext', 'out_name_2.out_ext', ...
        for example: my_slice_1.jpg, my_slice_2.jpg, ...

    Raises:
        KeyError:
            If the output format could not be determined from the file name. (from PIL)
            The 'out_ext' may be a invalid value, which cannot be recognized by PIL. Check PIL's document for detail.
        IOError:
            If the file could not be written. The file may have been created, and may contain partial data. (from PIL)

        All the exceptions above is raised from PIL's image.save() method. Check PIL's document for details.

    """
    count = 1
    for working_slice in in_list:
        assert isinstance(working_slice, Image.Image)
        working_slice.save(os.path.join(out_dir, out_name + "_" + str(count) + '.' + out_ext))
        count += 1


# helper function for image grid slice saving.
def save_image_grid(in_list, out_dir, out_name, out_ext):
    """saves a image grid in a form of 'List of List' of PIL image to file system.

    A helper function to save image grid or 'list of list' images to file system, with proper sequence number naming.

    Args:
        in_list:
            A 'list of list', the content of each element list should be PIL image objects.
        out_dir:
            A valid path string, to where the files would be written to.
        out_name:
            A string, the file name prefix you would like to save.
            The output file names will be:
                out_name_1_1, out_name_1_2, ... , out_name_1_N, 
                out_name_2_1, out_name_2_2, ... , out_name_2_N,
                , .... ,
                out_name_M_1, out_name_M_2, ... , out_name_M_N
        out_ext:
            The file extension name, like jpg, png, ...

    Returns:
        All the images in 'in_list' will be saved to 'out_dir', one by one.

        Each list element of the 'list of list' will be treated as a 'row' of images, all the element list will be saved
        'row by row'. In each 'row', the PIL Image objects will be saved one by one, each as a 'column'.

        For example, if 'out_name' is 'my slice', 'out_ext' is 'jpg', the final output files will be:
            my_slice_1_1.jpg, my_slice_1_2.jpg, ... , my_slice_1_N.jpg, 
            my_slice_2_1.jpg, my_slice_2_2.jpg, ... , my_slice_2_N.jpg,
            , .... ,
            my_slice_M_1.jpg, my_slice_M_2.jpg, ... , my_slice_M_N.jpg

    Raises:
        KeyError:
            If the output format could not be determined from the file name. (from PIL)
            The 'out_ext' may be a invalid value, which cannot be recognized by PIL. Check PIL's document for detail.
        IOError:
            If the file could not be written. The file may have been created, and may contain partial data. (from PIL)

        All the exceptions above is raised from PIL's image.save() method. Check PIL's document for details.

    """
    count = 1
    for sub_slice_list in in_list:
        assert sub_slice_list
        assert isinstance(sub_slice_list[0], Image.Image)
        save_image_list(sub_slice_list, out_dir, out_name + '_' + str(count), out_ext)
        count += 1


# helper function to get current working directory
def get_current_cwd():
    """Gets current working directory

    Returns: current working directory returned by os.getcwd()

    """
    return os.getcwd()


# helper function to get the basename separated from the path(if any)
def get_file_basename_without_path(file_name):
    """Gets the basename (pure file name without any path) from a given filename (may contain path)

    Returns: the pure filename of the 'basename' of the file.

    """
    return os.path.basename(file_name)


# helper function to split a file name to a pure file name and a ext name
def split_pure_file_name_from_ext_name(file_name):
    """Splits file_name to a base name (the part without ext) and a ext name (the dot part)

    This helper function helps you to easily extract the bare file name (without ext) from the type name (the ext name)
    The names are determined by this way:
        Find the last dot ('.') ,
        the name to the left of the dot, is the bare name,
        the name to the right of the dot, is the ext name.
    This will work fine in almost all 'normal' cased. If your filename is a 'anomaly', it may not work for you.

    For example:
        split_pure_file_name_from_ext_name("this.is.a.image-file.jpg")
        will return: ("this.is.a.image-file", "jpg")
        you can use the tuple return like this directly:
            my_pure_name, my_ext = split_pure_file_name_from_ext_name("this.is.a.image-file.jpg")

    Args:
        file_name: a string, the file name you want to split.

    Returns:
        A 2-element tuple of string, the first element is the pure file name, the second is the ext name.
        like this: ("this.is.a.image-file", "jpg")

    Raises:
        ValueError:
            If 'file_name' is empty, or does not contain any dot (without dot, the ext name cannot be determined).
        TypeError:
            If 'file_name' is not a string. you can try str(your_arg).

    """
    if not file_name:
        raise ValueError("'filename' is a mandatory field, it cannot be empty.")
    if not isinstance(file_name, str):
        raise TypeError("'filename' should be a string, check the argument, or try str(your_arg)")
    file_name_split = file_name.split('.')
    if len(file_name_split) < 2:
        raise ValueError("'filename' does not contain any '.' (dot), so the ext name cannot be determined.")
    # get the last element of the list, which should be the ext name.
    file_name_ext = str(file_name_split.pop())
    # join remaining elements in the list, if any, in case the original file name contains '.'
    file_name_without_ext = ''.join(file_name_split)
    # return is a tuple
    return file_name_without_ext, file_name_ext


# Standalone sub-command functions for argparse, so it can dispatch accordingly without extra work.

# standalone horizontal
def _standalone_horizontal_slice(arguments):
    print('[Horizontal slice]')
    # equal slice case.
    if getattr(arguments, 'slice_count', False):
        print('Slice method: equal slice.  Slice count: ' + str(arguments.slice_count))
        return slice_horizontal_in_equal(arguments.file_name, arguments.slice_count)
    # step slice
    elif getattr(arguments, 'step_size', False):
        print('Slice method: step slice.  Slice step: every ' + str(arguments.step_size) + "px")
        return slice_horizontal_by_step(arguments.file_name, arguments.step_size)
    # ratio slice
    elif getattr(arguments, 'ratio_string', False):
        print('Slice method: ratio slice.  Slice ratio: ' + str(arguments.ratio_string))
        return slice_horizontal_by_ratio(arguments.file_name, arguments.ratio_string)
    # should never reach this.
    else:
        # this exception should never be raised.
        raise ValueError('-e, -s or -r, one of which should be provided.')


# Standalone vertical
def _standalone_vertical_slice(arguments):
    print('[Vertical slice]')
    # equal slice case.
    if getattr(arguments, 'slice_count', False):
        print('Slice method: equal slice.  Slice count: ' + str(arguments.slice_count))
        return slice_vertical_in_equal(arguments.file_name, arguments.slice_count)
    # step slice
    elif getattr(arguments, 'step_size', False):
        print('Slice method: step slice.  Slice step: every ' + str(arguments.step_size) + "px")
        return slice_vertical_by_step(arguments.file_name, arguments.step_size)
    # ratio slice
    elif getattr(arguments, 'ratio_string', False):
        print('Slice method: ratio slice.  Slice ratio: ' + str(arguments.ratio_string))
        return slice_vertical_by_ratio(arguments.file_name, arguments.ratio_string)
    # should never reach this.
    else:
        # this exception should never be raised.
        raise ValueError('-e, -s or -r, one of which should be provided.')


# standalone grid
def _standalone_grid_slice(arguments):
    print('[Grid slice]')
    # parse the input arguments, get the mode and mode_params for each direction.
    if getattr(arguments, 'grid_string', False):
        # It's the shortcut grid_string case, a grid is provide in a form or 3x2 or 3*2
        grid_string = arguments.grid_string

        # A list for holding grid values

        # Check if it's separated by 'x'
        if 'x' in grid_string:
            # temp list for value check
            temp_grid_values = [int(i) for i in grid_string.split('x') if i.isdigit() and int(i) != 0]
        # or '*' as separator
        elif '*' in grid_string:
            temp_grid_values = [int(i) for i in grid_string.split('*') if i.isdigit() and int(i) != 0]
        else:
            raise ValueError('Grid String invalid. '
                             'A valid grid string should be either "3x2" or "3*2", use "x" or "*" for separator.')
        # a valid grid string should be either 3x2 or 3*2, use x or * for separator.
        # this case, it's a 3x2 style input.

        # there should not be any empty element,
        # this check eliminates the case of multiple 'x' or leading or trailing 'x'
        if all(temp_grid_values):
            pass
        else:
            raise ValueError('Grid String invalid. A valid grid string should be 2 numbers separated by '
                             'either "x" or "*" as separator, like "3x2" or "3*2", check if it\'s a typo.')

        # The length of the list should be 2, all the elements should be a int, the value should not be 0
        if len(temp_grid_values) == 2:
            pass
        else:
            raise ValueError('Grid String invalid. A valid grid string should be 2 numbers separated by '
                             'either "x" or "*" as separator, like "3x2" or "3*2", check if it\'s a typo.')

        # now we have a valid grid.
        grid_values = temp_grid_values
        # set the arguments for grid slice.
        horizontal_mode = 'equal'
        horizontal_param = grid_values[0]
        vertical_mode = 'equal'
        vertical_param = grid_values[1]

    else:
        # horizontal
        if getattr(arguments, 'grid_horizontal_slice_count', False):
            horizontal_mode = 'equal'
            horizontal_param = arguments.grid_horizontal_slice_count
            print("Horizontal mode: equal slice.  Slice count: "+str(horizontal_param))
        elif getattr(arguments, 'grid_horizontal_step_size', False):
            horizontal_mode = 'step'
            horizontal_param = arguments.grid_horizontal_step_size
            print("Horizontal mode: step slice.  Slice step: every " + str(horizontal_param)+"px")
        elif getattr(arguments, 'grid_horizontal_ratio_string', False):
            horizontal_mode = 'ratio'
            horizontal_param = arguments.grid_horizontal_ratio_string
            print("Horizontal mode: ratio slice.  Slice ratio: " + str(horizontal_param))
        else:
            # should never reach this.
            raise ValueError('Grid slice, horizontal mode unknown, '
                             'something went very wrong, check the code, fire a issue.')

        # vertical
        if getattr(arguments, 'grid_vertical_slice_count', False):
            vertical_mode = 'equal'
            vertical_param = arguments.grid_vertical_slice_count
            print("Vertical mode: equal slice.  Slice count: " + str(vertical_param))
        elif getattr(arguments, 'grid_vertical_step_size', False):
            vertical_mode = 'step'
            vertical_param = arguments.grid_vertical_step_size
            print("Vertical mode: step slice.  Slice step: every " + str(vertical_param)+"px")
        elif getattr(arguments, 'grid_vertical_ratio_string', False):
            vertical_mode = 'ratio'
            vertical_param = arguments.grid_vertical_ratio_string
            print("Vertical mode: ratio slice.  Slice ratio: " + str(vertical_param))
        else:
            # should never reach this.
            raise ValueError('Grid slice, vertical mode unknown, '
                             'something went very wrong, check the code, fire a issue.')

    # do the grid slice.
    return slice_to_grid(arguments.file_name, horizontal_mode=horizontal_mode, horizontal_param=horizontal_param,
                         vertical_mode=vertical_mode, vertical_param=vertical_param)


# main function when used as a standalone app.
# mostly it's the argument declarations and parsings. It's like a dispatcher.
def main(argv):
    # Instantiate the parser
    parser = argparse.ArgumentParser(
        description='\'image-slice\' is a tool for easy image slicing:'
                    '\n    You can slice a image in 3 modes: [horizontal], [vertical] and [grid].'
                    '\n    In each mode, it supports 3 slice methods: [Equal] slice to a given count,'
                    '[Step] slice every N pixel, [Ratio] slice to a ratio like 3:2:1.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='\nExamples:'
               '\n* Slice horizontally to 3 equal slices:'
               '\n    %(prog)s horizontal your_image.jpg -e 3'
               '\n* Slice vertically every 200px:'
               '\n    %(prog)s vertical your_image.jpg -s 200'
               '\n* Slice horizontally to a ratio of 3:2:1'
               '\n    %(prog)s horizontal your_image.jpg -r 3:2:1'
               '\n* Slice to a 3*2 grid equally in both direction:'
               '\n    %(prog)s grid your_image.jpg -he 3 -ve 2'
               '\n'
               '\nUsage explained:'
               '\n* Slice mode: '
               '\n    [vertical] slice a image from top to bottom, '
               '\n    [horizontal] slice a image from left to right,'
               '\n    [gird] slice a image to a grid like 3*2, slice horizontal first then vertical.'
               '\n* Slice method: '
               '\n    [equal] -e is for equally slice, following -e you should provide how many slices '
               'you want, \n        For example: \'image-slice vertical -e 3 some_image.jpg\', '
               'means slice the image vertically into 3 slices.'
               '\n    [step] -s is for step slice, which means slice every N px,'
               '\n        For example: '
               '\'image-slice horizontal -s 200 image_file.png\' means slice the image horizontally '
               'every 200px, until it\'s all sliced.'
               '\n    [ratio] -r is for ratio slice, you can specify a ratio, to which the image will be'
               ' sliced.'
               '\n        For example: \'slice-image horizontal -r 3:2:1 image.jpg\' will slice the image '
               'to a ratio of \'3:2:1\',\n        so 3 slices will be generated, each has a size respectively '
               'of the ratio 3:2:1. \n        (roughly, non-divisible pixels are distribute equally to each slice, '
               '1px for each)'
               '\n* Grid slice:'
               '\n    Grid slice is a little different from horizontal and vertical slice, '
               '\nbecause you have to specify the slice method of both method, but it\'s basically the same.'
               '\n    In grid slice, use [-ve -vs -vr] to specify the slice method of the vertical direction,'
               '\neach of which means [Equal slice], [Step slice] or [Ratio slice];'
               '\n    Similarly, you can use -he -hs -hr to specify the slice method of the horizontal direction.'
               '\n    You are free to combine different slice method in different directions, '
               '\nthe image will be sliced as you command.'
    )
    # Define argument patterns.

    # Patterns Explained:
    #   image_slice.py [FILE_NAME] vertical|horizontal| (-e SLICES, -s STEP_SIZE, -r RATIO_STRING)
    #   image_slice.py [FILE_NAME} grid (-ve, -vs, -vr) (-he, -hs, -hr)
    # The file_name is the only global top level argument, it's the image file to be slice.
    # Then we use 3 subprograms to do the vertical, horizontal, grid slice separately.
    # In each subprogram, you provide how to slice.

    # The only global argument to hold the file_name.
    parser.add_argument('file_name', metavar='FILE_NAME', help='File path of the image to be sliced.')

    # Enable the sub command feature.
    subparsers = parser.add_subparsers(dest='mode')

    # Vertical case:

    # Define a vertical sub command parser.
    vertical_sub_parser = subparsers.add_parser(
        'vertical', aliases=['v'],
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
    horizontal_sub_parser = subparsers.add_parser(
        'horizontal', help='Horizontal slice mode, for help use \'image-slice horizontal --help\'',
        aliases=['h'])

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
    # image_slice.py [FILE_NAME] grid
    #       (-ve SLICES_NUM, -vs STEP_SIZE, -vr RATIO_STR) (-he SLICES_NUM, -hs STEP_SIZE, -hr RATIO_STR)
    # Both direction should be specified, because it's a grid.
    # The program will slice the image in each direction accordingly.

    # Define a grid sub command parser.
    grid_parser = subparsers.add_parser('grid', aliases=['g'],
                                        help='Grid slice mode, for help use \'image-slice grid --help\'')
    # # The shortcut for grid equal slice.
    # group_grid_shortcut_or_not = grid_parser.add_mutually_exclusive_group(required = True)
    # # add a short cut command.
    # group_grid_shortcut_or_not.add_argument('grid_string', default='',required=False)
    # # append others

    # Vertical command, define a mutually exclusive argument group.
    group_grid_vertical_e_or_s_or_r = grid_parser.add_mutually_exclusive_group(required=True)
    # 3 cases of slice mode.
    group_grid_vertical_e_or_s_or_r.add_argument(
        '-ve', '--vertical-equal', type=int,
        metavar='VERTICAL_SLICE_COUNT',
        dest='grid_vertical_slice_count',
        default=0,
        help='Grid VERTICAL: Slice equally to VERTICAL_SLICE_COUNT slices in vertical.'
    )
    group_grid_vertical_e_or_s_or_r.add_argument(
        '-vs', '--vertical-step', type=int,
        metavar='VERTICAL_STEP_SIZE',
        dest='grid_vertical_step_size',
        default=0,
        help='Grid VERTICAL: Slice every VERTICAL_STEP_SIZE pixels in vertical.'
    )
    group_grid_vertical_e_or_s_or_r.add_argument(
        '-vr', '--vertical-ratio',
        metavar='VERTICAL_RATIO_STRING', dest='grid_vertical_ratio_string',
        default='',
        help='Grid VERTICAL: Slice by a RATIO_STRING like 3:2:1 in vertical.')

    # Horizontal command, define a mutually exclusive argument group.
    group_grid_horizontal_e_or_s_or_r = grid_parser.add_mutually_exclusive_group(required=True)
    # 3 cases of slice mode.
    group_grid_horizontal_e_or_s_or_r.add_argument(
        '-he', '--horizontal-equal', type=int,
        metavar='HORIZONTAL_SLICE_COUNT',
        dest='grid_horizontal_slice_count',
        default=0,
        help='Grid HORIZONTAL: Slice equally to HORIZONTAL_SLICE_COUNT slices in horizontal.'
    )
    group_grid_horizontal_e_or_s_or_r.add_argument(
        '-hs', '--horizontal-step', type=int,
        metavar='HORIZONTAL_STEP_SIZE',
        dest='grid_horizontal_step_size',
        default=0,
        help='Grid HORIZONTAL: Slice every HORIZONTAL_STEP_SIZE pixels in horizontal.'
    )
    group_grid_horizontal_e_or_s_or_r.add_argument(
        '-hr', '--horizontal-ratio',
        metavar='HORIZONTAL_RATIO_STRING', dest='grid_horizontal_ratio_string',
        default='',
        help='Grid HORIZONTAL: Slice by a RATIO_STRING like 3:2:1 in horizontal.')

    # Set subprogram dispatch functions.
    # argparse will parse the args, and invoke the correspond function.
    vertical_sub_parser.set_defaults(func=_standalone_vertical_slice)
    horizontal_sub_parser.set_defaults(func=_standalone_horizontal_slice)
    grid_parser.set_defaults(func=_standalone_grid_slice)

    # Argument parsing begins

    # Parse the incoming arguments
    # argv is the parameter name of this main(argv) function, default to None, so other program can call it directly.
    if argv:
        # argv is not none, it's the case the main() is called directly from another module, not from command-line.
        arguments = parser.parse_args(argv)
    else:
        # called directly from command-line, it's the case this module is executed directly.
        # parse call with no args will handle the 2 command situation properly, like python image_slice.py
        # otherwise the second command, in this case it's the script name, will be recognized to first real argument.
        arguments = parser.parse_args()
    # print(arguments)
    # arguments should not be empty.
    assert arguments
    # the name of image file to be sliced, should not be empty.
    assert arguments.file_name
    print("[Image File Name]: " + arguments.file_name)

    # dispatch the execution to the sub functions accordingly.
    output_slices = arguments.func(arguments)

    # make sure output_slices is not empty.
    assert output_slices

    # get current working directory as the output dir. later we will pass the it to the file saving functions.
    working_dir = get_current_cwd()
    # get the pure file name of the input file, input may be a path, so we have to make sure path part not there.
    file_name_original = get_file_basename_without_path(arguments.file_name)
    file_name_without_ext, file_name_ext = split_pure_file_name_from_ext_name(file_name_original)

    # save the output slices to current working directory
    if isinstance(output_slices[0], Image.Image):
        # it's a list of Images, save this list.
        save_image_list(output_slices, working_dir, file_name_without_ext, file_name_ext)
    else:
        # it should be a list of list, confirm it, save the list of list.
        assert isinstance(output_slices[0], list)
        save_image_grid(output_slices, working_dir, file_name_without_ext, file_name_ext)

    # everything's done, print success message, return 0.
    print('Slice completed, check current working directory, slices should already be there.')
    return 0


if __name__ == "__main__":
    # When image_slice.py is called directly from the command line, argparse should fetch the args directly.
    # That is because if a command is a 2-word combination, like 'python image_slice.py',
    # it will not be treated as a single 2-word command, but a 1-word command and a argument.
    # But if it's fetched directly, this case will be fine.
    # 'python image_slice.py' will be treated as a whole command in the argv[0],
    # not 'python' in argv[0], 'image_slice.py' in argv[1] as the first argument.
    main(argv=None)
