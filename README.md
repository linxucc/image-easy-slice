# image-easy-slice (WIP)
A python wheel for easy image slice. Slice one image into multiple parts: vertically, horizontally, or by a given grid.

# What for?
When I was working on one of my projects, I ran into a small feature which requires to slice a given image equally into multiple parts, 
just like using the image slice tool in a image processing software like Photoshop, but programmatically. 

This is a simple and 'standard' task of image processing, but after a few google search, 
I'm surprised there's no simple dedicated wheel for this 'standard' job, maybe because it's too simple. 
That means I have to write my own code snippet to do the image slicing.

So after the job, I decided to extend the snippet into a simple image-slice library and also a standalone tool,
 add some features, make it more generic, so other guys could save some time and enjoy the beautiful life.

# How does it work?
This simple piece of software is built on the 'standard' python image library, PIL (or Pillow, roughly it's the same thing). 

Since image slice is not something very hard to implement, so maybe it's the reason why there's no dedicated wheel when I try to find one.

The whole process is pretty simple: 
* PIL handles all the 'image' things, including all the format things, all the IO things, and all the 'crop' things. 
* This simple wheel mainly just focus on how to crop properly: figure out the right coordinates of each slice, 
and calculate the desired 'width'/'height' of each slice. 
* Finally it will iterate through all the calculated slices and do the crop for you, you will get a list of sliced images at last.

So what PIL supports, it supports; what PIL can't do, it can't. 

It just makes the image slice thing a little easier, 
save you some time from the 'width'/'height' calculations and the crop iterations, 
which always comes boring and sometimes makes people confusing. 

# How to install
Now just download the code, future use PIP.

# Use as a Library
1. Use as a library: send in a image object or a file path, 
output will be a list of PIL Image objects, which contains all the output slices.

# Use as a Standalone Tool
2. Use as a standalone tool: specify the image path, set options, 
output will write to the same directory, name in a pattern of 'original_file_name-1.jpg','original_file_name-2.jpg'.

# How to Slice
1. The Direction: vertical, horizontal, or by a given grid.
2. Desired Output: equally, to a given size, or by a ratio (future, not implemented).

# A Note on the width/height calculations in image slicing
In the digital image world, the minimum composite unit of a image is a Pixel or 1px, 
that means, 1px or a Pixel cannot be divided further into something smaller, there's no such things like '0.5px', '128.7px'. 

It becomes a trouble when you try to slice something like a 500px width image into 3 equal parts, 
the width calculated directly from 500/3 is 166.66666666... which is not a integer. So there's no 'perfect equal' in this case, because
there's no such thing like '0.66666666px' or '166.7px', 1px is the minimum unit and cannot be divided further, 
all we can do is to find a 'approximately equal' way to get the image sliced.

My way is to 'distribute' the 'extra' pixels which cannot be divided into a integer (the positive remainder of the division) into all the leading slices, 
1 Pixel by a slice, until it's all done. 

In the previous example, the output slices will be 127px, 127px, 126px. 
That's because 500 is divided by 3 to 126 with a remainder of 2. (500 = 126*3 + 2) We distribute the extra 2 pixels into the first two slices,
so it's 126+1, 126+1, 126. 

Most modern image has a height/width of hundreds to thousands pixels, the +1px or -1px difference is barely noticeable, 
especially for us human, so these results are still 'equal' enough to be called a 'equal' slice.

Because in 99.9% cases, the image width/height cannot be divided into a simple integer. So this tricky thing happens all the time. 
Note in some 'extreme' cases, for example, try to slice a 150px image into 100 slices, 
the slices generated in this method may not be what you expected, in this case, the first 50 of 100 slices will have 2px, and the last 50 of 100 slices will have 1px, which is a 50% difference.

The flagship software Photoshop takes a similar way (even if it's Photoshop, there's no magic to divide 1px either!), 
but with a more complicated algorithm to distribute the extra pixels more 'evenly' across all the slices. 
In the case of dividing 199px to 100 slices, Photoshop will do it in a way of 1px,2px,1px,2px,1px,2px...... , and it indeed looks more 'equal' than our method. 
This part of Photoshop is really complicated and considering, in some cases, Photoshop takes a method similar to the pivot selection algorithm in quick sort, 
in cases like slice 5px into 3 slices, it will be 1px,2px,1px,2px,1px . It handles the extreme cases very well, to make the result as even as possible. (It's the Photoshop!).


If you are devastatingly expecting to get the exactly same width/height in each slices, what you need is *image resampling* other than *image slicing*. 
Take the examples above, when slicing a 150px image to 100 slices, to get a 'absolutely equal' width of each slices, 
you have to either *upscale resample* the image to 200px, then slice it into 100 slices, so each slide will have a 2px width.
Or you have to *downscale resample* the image to 100px, then slice it into 100 slices, and the result will be a 1px width each slice.

Resampling is another big topic, in most times it will decrease the image quality, and there's no 'universal best way' to do so, 
it's full of 'varies' and 'depends'. So this little tool does not involve any image resampling now. 
But you can still do the resampling yourself and then use this tool to do the slicing job, if you are really in the need to get a 'perfect equal' slice.


# Milestones and plan
1. vertical and horizontal, equally slice to given counts.
2. slice to a given size (vertical size or horizontal size, not both), 'slice each 200px'
3. slice to a given grid.
4. robust improvement.
