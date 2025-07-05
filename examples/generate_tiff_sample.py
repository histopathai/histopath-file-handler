import numpy as np
import tifffile as tiff


def main():

    size = (2000, 2000)
    ## create CMYK image cheeseboard pattern
    cmyk = np.zeros((4, *size), dtype=np.uint8)
    cmyk[0, ::2, ::2] = 255  # C
    cmyk[1, 1::2, ::2] = 255  # M
    cmyk[2, ::2, 1::2] = 255  # Y
    cmyk[3, 1::2, 1::2] = 255  # K


    ## CMYK to RGB conversion
    # Convert CMYK to RGB using the formula:
    # R = 255 * (1 - C) * (1 - K)
    # G = 255 * (1 - M) * (1 - K)
    # B = 255 * (1 - Y) * (1 - K)
    r = 255 * (1 - cmyk[0] / 255)
    g = 255 * (1 - cmyk[1] / 255)
    b = 255 * (1 - cmyk[2] / 255)
    rgb = np.stack((r, g, b), axis=-1).astype(np.uint8)

    ## save RGB image as TIFF
    tiff.imwrite('temp.tiff', rgb, photometric='rgb')
if __name__ == '__main__':
    main()