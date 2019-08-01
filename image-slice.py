from PIL import Image

'''helper function, calculate the list of width/height of output slices'''
# return a list, in which contains the calculated width/height of each slice.
def calculate_slices_size(image_height_or_width, slice_count, step_size):
    # arguments parsing, validation.
    assert image_height_or_width>0
    assert slice_count>=0
    assert step_size>=0
    # one of the step_size or slice_count should be zero, or it's a invalid invoke.
    assert step_size*slice_count == 0
    # make sure they are not both zero, or it's a invalid invoke.
    assert step_size != slice_count

    if slice_count:
        # equal slice, the step_size should be zero.
        assert step_size == 0
        #



'''the main function to do the slice'''
# this function should not be called directly, use proxy functions instead, unless you have a strong reason to do so,
# this function only do one-direction image slice, for grid slice you should use the grid proxy functions.
# grid slice is implemented in a way of 'slice horizontal first, then for each slice, do the same vertical slice.'
def slice_image_one_direction(image,
                slice_vertical_yn,
                slice_horizontal_yn,
                slice_count_vertical,
                slice_count_horizontal,
                equal_slice_yn,
                step_slice_yn,
                step_horizontal,
                step_vertical):

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
            slices_heights = calculate_slices_size(img_height, slice_count=slice_count_vertical, step_size=0)
        if step_slice_yn:
            slices_heights = calculate_slices_size(img_height, slice_count=0, step_size=step_vertical)
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
            slices_widths = calculate_slices_size(img_width, slice_count=slice_count_horizontal, step_size=0)
        if step_slice_yn:
            slices_widths = calculate_slices_size(img_width, slice_count=0, step_size=step_horizontal)
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
    return slice_image_one_direction(image, False, True, 0, horizontal_count, True, False, 0, 0)

def slice_vertical_in_equal(image, vertical_count):
    # slice vertical
    return slice_image_one_direction(image, True, False, vertical_count, 0, True, False, 0, 0)

def slice_horizontal_by_step(image, step_horizontal):
    return slice_image_one_direction(image, False, True, 0, 0, False, True, step_horizontal, 0)

def slice_vertical_by_step(image, step_vertical):
    return slice_image_one_direction(image, True, False, 0, 0, False, True, 0, step_vertical)

# grid slice is performed in this way: slice horizontally first, then for each horizontal slice, perform the vertical slice.
def slice_to_grid_in_equal(image, vertical_count, horizontal_count):
    horizontal_slices = slice_horizontal_in_equal(image, horizontal_count)
    # make sure it's not empty
    assert horizontal_slices
    # slice each horizontal slice vertically.
    grid_slices = []

    for horizontal_slice in horizontal_slices:
        vertical_sub_slices = slice_vertical_in_equal(horizontal_slice, vertical_count)
        # make sure it's not empty
        assert vertical_sub_slices
        grid_slices.append(vertical_sub_slices)

    # make sure it's not empty
    assert grid_slices
    return grid_slices

def slice_to_grid_by_step(image, vertical_step, horizontal_step):
    horizontal_slices = slice_horizontal_by_step(image, horizontal_step)
    # make sure it's not empty
    assert horizontal_slices
    grid_slices = []

    for horizontal_slice in horizontal_slices:
        vertical_sub_slices = slice_vertical_by_step(horizontal_slice, vertical_step)
        # make sure it's not empty
        assert vertical_sub_slices
        grid_slices.append(vertical_sub_slices)

    # make sure it's not empty
    assert grid_slices
    return grid_slices



# Future

def slice_horizontal_by_ratio(image, ratio_string):
    pass

def slice_vertical_by_ratio(image, ratio_string):
    pass

# In the pro mode, you can combine a equal horizontal slice with a step vertical slice.
# Since it's not something usual, we call it the pro mode, so this complexity will not affect other simple situations.
# Ratio is also supported.
def slice_by_grid_professional(image, options):
    pass




# todo: add a main