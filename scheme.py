#!/usr/bin/env python3
import argparse
import re
import sys

# TWEAK HERE: If the command line doesn't give you enough customization,
# You can mess with the constants here to get an even finer level of control.

# This is used to ensure that dark colors aren't
# affected by light colors and vice versa.
THRESHOLD = 0x1550

# Only investigae this if you get colors
# that blend in with your background.
COL_FIX_AMT = 5

# These are terminal color schemes expressed from color 0 to color 15.
# Feel free to add your own! Just change COLORSCHEME
# Default color scheme gotten from terminal.sexy
default = ["282a2e", "a54242", "8c9440", "de935f",
           "5f819d", "85678f", "5e8d87", "707880",
           "373b41", "cc6666", "b5bd68", "f0c674",
           "81a2be", "b294bb", "8abeb7", "c5c8c6"]

# ***YOUR COLOR SCHEMES HERE ***

COLORSCHEME = default

# This is your assumed foreground and background. You can use some of the
# util files to ensure that colors stand out from these.
BACKGROUND = "0d191d"
FOREGROUND = "d9e6f2"


def lum(col):
    """Returns color brightness as usable for comparison.
    The proper calculation would use the norm, but if we're
    just comparing not squaring saves time."""
    r, g, b = rgb_to_int(col)
    return r + g + b


def match_brightness(fixed, moving):
    """returns moving renormalized to have fixed's norm"""
    rf, gf, bf = rgb_to_int(fixed)
    rm, gm, bm = rgb_to_int(moving)
    # No squaring because negative colors don't exist.
    fnorm = rf + gf + bf
    rnorm = rm + gm + bm
    if rnorm == 0:
        return moving
    slope = fnorm / rnorm
    return rgb_to_str(clamp(int(rm * slope)),
                      clamp(int(gm * slope)), clamp(int(bm * slope)))


def lum_dist(col1, col2):
    r1, g1, b1 = rgb_to_int(col1)
    r2, g2, b2 = rgb_to_int(col2)
    return (lum(col1) - lum(col2)) ** 2


def coldist(col1, col2):
    """Computes the distance between 2 colors"""
    r1, g1, b1 = rgb_to_int(col1)
    r2, g2, b2 = rgb_to_int(col2)
    return (r1 - r2)**2 + (g1 - g2) ** 2 + (b1 - b2) ** 2


def average_cols(col1, col2, weight):
    """Takes the average of col1 and col2,
    with weight of weight given to col2"""
    r1, g1, b1 = rgb_to_int(col1)
    r2, g2, b2 = rgb_to_int(col2)
    weight_c = 1 - weight
    r_avg = (int((r1 * weight_c) + weight * r2)) % 255
    g_avg = (int((g1 * weight_c) + weight * g2)) % 255
    b_avg = (int((b1 * weight_c) + weight * b2)) % 255
    return rgb_to_str(r_avg, g_avg, b_avg)


def colratio(col):
    """Calculates the ratio of R, G, and B
    in a color. Useful for comparing hue."""
    r1, g1, b1 = rgb_to_int(col)
    sum = r1 + g1 + b1
    if sum == 0:
        return 0, 0, 0
    return (r1/sum, g1/sum, b1/sum)


def colratio_dist(col1, col2):
    """Compare the hues between 2 colors"""
    hue1 = colratio(col1)
    hue2 = colratio(col2)
    return (hue1[0] - hue2[0])**2 + \
           (hue1[1] - hue2[1])**2 + (hue1[2] - hue2[2])**2


# Utils:
def rgb_to_int(color):
    return (int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16))


def rgb_to_str(R, G, B):
    if R < 0x10:
        Rstr = "0"+hex(R)[2:]
    else:
        Rstr = hex(R)[2:]
    if G < 0x10:
        Gstr = "0"+hex(G)[2:]
    else:
        Gstr = hex(G)[2:]
    if B < 0x10:
        Bstr = "0"+hex(B)[2:]
    else:
        Bstr = hex(B)[2:]
    return Rstr + Gstr + Bstr


def remove_hashes(colors):
    rv = []
    for color in colors:
        if color[0] == "#":
            rv.append(color[1:])
        else:
            rv.append(color)
    return rv


def clamp(n):
    if n > 255:
        return 255
    if n < 0:
        return 0
    return n


def three_min(array, key):
    array = array[:]
    min1 = min(array, key=key)
    array.remove(min1)
    min2 = min(array, key=key)
    array.remove(min2)
    min3 = min(array, key=key)
    array.remove(min3)
    return (min1, min2, min3)


def n_min(array, key, n):
    array = array[:]
    array.sort(key=key)
    return array[:n]


def _ratio_dist(x, y, threshold):
    """Helper function to be passed as a key to n_min.
    returns the difference in hue between x and y if their
    luminance is within threshold."""
    if lum_dist(x, y) > threshold:
        return 2048
    else:
        return colratio_dist(x, y)


def mix_colors(colors, weights, num_adj):
    """Takes is an array of strings [AABBCC, 123456, ...]
    and outputs them overlaid on COLORSCHEME."""
    colors = remove_hashes(colors)
    results = []
    for base in COLORSCHEME:
        closecols = n_min(colors,
                          lambda x: _ratio_dist(x, base, THRESHOLD),
                          num_adj)
        newcol = base
        for i in range(num_adj):
            newcol = average_cols(closecols[i], newcol, min(1, weights[i]
                                  * colratio_dist(base, closecols[i])))
            newcol = match_brightness(base, newcol)
        results.append(newcol)
    for col in results:
        print("#"+col)


# Appendix: unused scripts which would otherwise
# have some use in matching up colors:

def affect_color(col1, colors, threshold):
    """Iterates through colors and averages color with
    any colors that are within threshold of it."""
    for col2 in colors:
        if colratio_dist(col1, col2) < threshold:
            # To prevent that "Mixing paint until brown" effect.
            col1 = average_cols(col1, col2, .5)
    return col1


def ensure_contrast(color):
    """Ensures that the color is at least threshold away from the background
    and moves it COL_FIX_AMT in the opposite direction if it isn't.
    Useful if you're getting too dark/ too light of colors"""
    r1, g1, b1 = rgb_to_int(BACKGROUND)
    r2, g2, b2 = rgb_to_int(color)
    if coldist(color, BACKGROUND) <= THRESHOLD:
        return separate_colors(BACKGROUND, color, COL_FIX_AMT)
    return color


def separate_colors(fixed, moving, distance):
    """Moves the color moving distance away from fixed.
    This entails finding the slope between the 2 colors
    in each dimension and following it."""
    rf, gf, bf = rgb_to_int(fixed)
    rm, gm, bm = rgb_to_int(moving)
    dx = (rm - rf) * distance
    dy = (gm - gf) * distance
    dz = (bm - bf) * distance
    return rgb_to_str(clamp(int(rm + dx)),
                      clamp(int(gm + dy)), clamp(int(bm + dz)))


def to_xresorces(colors):
    for i in range(len(colors)):
        print("*color{}\t#{}".format(i, colors[i]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='opts')
    parser.add_argument('-n',
                        dest='num_adj',
                        metavar='a',
                        type=int,
                        nargs='?',
                        default=3,
                        help='Number of colors averaged with each color in the saved color scheme')
    parser.add_argument('-d',
                        dest='decay',
                        metavar='d',
                        type=int,
                        nargs='?',
                        default=3,
                        help='The rate at which far colors cease to affect each color')
    parser.add_argument('-f',
                        dest='filename',
                        metavar='f',
                        type=str,
                        nargs='?',
                        default=None,
                        help='Name path to a file that contains a valid 16 color color scheme in xrdb format.\
                        \nNote that if you have a go-to colorscheme it is easy to hard code it at the top of this script.')
    parser.add_argument(dest='colors',
                        nargs=argparse.REMAINDER,
                        type=str,
                        help='List of colors to overlay on the image')
    args = parser.parse_args()
    weights = [15 + args.decay * i for i in range(args.num_adj)]
    if args.filename:
        with open(args.filename) as f:
            lines = f.read().split("\n")
            scheme_lines = []
            for i in range(16):
                pattern = re.compile(".*color{}:".format(i))
                matches = [line for line in lines if pattern.match(line)]
                if not matches:
                    print("Incomplete color scheme. Make sure your file has all 16 colors in valid format.")
                    exit(0)
                scheme_lines.append(matches[0])
            # Filter out empty lines:
            scheme_lines = [line for line in scheme_lines if line]
            COLORSCHEME = [color[::-1][:6][::-1] for color in scheme_lines]
    colors = [line for line in args.colors]
    mix_colors(colors, weights, args.num_adj)
