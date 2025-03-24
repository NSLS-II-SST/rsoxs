import numpy as np
from matplotlib import pyplot as plt
from PIL import Image


## Just copied from Eliot's code for now
def stitch_sample(images, step_size, y_off, from_image=None, flip_file=False):
    global sample_image_axes

    if isinstance(from_image, str):
        im_frame = Image.open(from_image)
        result = np.array(im_frame)
        if flip_file:
            result = np.flipud(result)
    else:
        pixel_step = int(step_size * (1760) / 25)
        pixel_overlap = 2464 - pixel_step
        result = images[0][0]
        i = 0
        for imageb in images[1:]:
            image = imageb[0]
            i += 1
            if y_off > 0:
                result = np.concatenate((image[(y_off * i) :, :], result[:-(y_off), pixel_overlap:]), axis=1)
            elif y_off < 0:
                result = np.concatenate((image[: (y_off * i), :], result[-(y_off):, pixel_overlap:]), axis=1)
            else:
                result = np.concatenate((image[:, :], result[:, pixel_overlap:]), axis=1)
        # result = np.flipud(result)

    fig, ax = plt.subplots()
    ax.imshow(result, extent=[-210, 25, -14.5, 14.5])
    sample_image_axes = ax
    #fig.canvas.mpl_connect("button_press_event", plot_click) ## For now, want to keep simple and not do clicking here.
    #fig.canvas.mpl_connect("key_press_event", plot_key_press)
    plt.show()
    return result


