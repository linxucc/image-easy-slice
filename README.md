# image-easy-slice (WIP)
A python wheel for easy image slice. Slice one image into multiple parts: vertically, horizontally, or by a given grid.

# What for?
When I'm working on one of my projects, which needs to slice some images into even parts. After some searching, I'm suprised there's no simple dedicated wheel for this 'standard' job. 

So after the job, I deciced to exetend my little image-slice code snippet into a simple library, also make it a standalone tool. 

# How does it work?
This simple piece of software is built on the 'standard' python image library, PIL (or Pillow, roughly it's the same thing). 

Since image slice is not something very hard to implement, so maybe it's the reason why there's no dedicated wheel when I try to find one.

The whole process is pretty simple, PIL handles all the 'image' things, including all the format things, all the IO things, and the 'crop' things. This simple wheel mainly just calcualtes how to crop each slice: the right coodinares, 'width' and 'height'. Then it iterate through the image for you, and do the crops.

So what PIL supports, it supports; what PIL can't do, it can't. 

It makes it easy when you need to slice a image, free you from the 'widht' and 'height' calculations and the crop iterations, which always comes boring, tedius and sometimes confusing. 

# How to install
Now just download the code, future use PIP.

# How to use
1. Use as a library: send the image object or file path, output a list of PIL Image objects, which contains all the output slices.
2. Use as a standalone tool: specify the image path, set options, output will write to the same directory, name in a pattern of 'original_file_name-1.jpg','original_file_name-2.jpg'.

# Slice mode and options.
1. vertical
2. horizental
3. grid, x by y (future)

# Milestones and plan
1. vertical and horizontal, equally slice to given counts.
2. slice to a given size (vertical size or horizontal size, not both), 'slice each 200px'
3. slice to a given grid.
4. robust improvement.
