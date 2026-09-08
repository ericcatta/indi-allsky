"""Five RGB samples at the configured center offset, before display colormap."""
from operator import index


def longterm_keogram_pixels(image, offset_x=0, offset_y=0):
    shape = getattr(image, 'shape', ())
    if len(shape) != 3 or shape[2] < 3:
        raise ValueError('Long-term sampling requires a BGR image')
    height, width = shape[:2]
    x = int(width / 2) + index(offset_x)
    y = int(height / 2) - index(offset_y)
    if x < 0 or x >= width or y < 0 or y + 5 > height:
        raise ValueError('Long-term sample offset places the five pixels outside the image')
    return [[int(image[y + row, x][2]), int(image[y + row, x][1]),
             int(image[y + row, x][0])] for row in range(5)]
