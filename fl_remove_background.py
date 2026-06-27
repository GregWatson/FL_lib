import cv2
import numpy as np
from rembg import remove
from fl_core import show_image
from pre_proc_image import pre_process_image

# given a BGR image, remove the background and return a cleaned up image with just the pieces. 
# We can use the REMBG library to do this, which is a pre-trained model for background removal. 
# We can then apply a mask to the original image to get the cleaned up image. 
# This will help us ensure that the line detection and rotation estimation works well even for smaller images.
def fl_remove_background(img, debug=False, image_type="normal"):

    if (image_type == "normal"):
        
        # Images of the normal type can be more complex, with pieces that have patterns and colors, 
        # and backgrounds that may not be perfectly solid.
        # Use the REMBG lib to remove the background and return a mask.
        # Mask is returns an array (entry per pixel) of a 4-tuple: BGR and alpha. 
        # The alpha channel is 0 for background and 255 for foreground (pieces).
        mask = remove(img, mask=True)
        print(f"mask shape: {mask.shape}, mask dtype: {mask.dtype}, unique values in mask: {np.unique(mask)}")

        # convert the alpha channel to a greyscale image and save it to disk for debugging.
        # mask_as_grey = mask[:, :, 3]  # alpha channel
        # cv2.imwrite("mask.png", mask_as_grey)
        # show_image(mask_as_grey, str="Mask Alpha Channel", max=1000, wait_for_key=True)

        if debug:
            show_image(img, str="Background removed", max=1000, wait_for_key=True)

    else:
        mask = img.copy()

    # Now do normal pre-proc on the image
    return pre_process_image(mask, debug=debug)


    