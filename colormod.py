#!/usr/bin/env python3
import sys
import fileinput
import argparse

def get_col_range(curr, nextcol, res):
    if curr[0] == "#":
        curr = curr[1:]
    rc, gc, bc = rgb_to_int(curr)
    if nextcol[0] == "#":
        nextcol = nextcol[1:]
    rn, gn, bn = rgb_to_int(nextcol)
    stepR = (rn - rc)/res
    stepG = (gn - gc)/res
    stepB = (bn - bc)/res
    currR = rc
    currG = gc
    currB = bc
    for _ in range(res):
        # print out the current color:
        currR += stepR
        currG += stepG
        currB += stepB
        R = hex(int(currR))[2:]
        G = hex(int(currG))[2:]
        B = hex(int(currB))[2:]
        while len(R) < 2:
            R = "0"+R
        while len(G) < 2:
            G = "0"+G
        while len(B) < 2:
            B = "0"+B
        print(R+G+B)

def fade_colors(cols, amt, res):
    """Fades a color to white by amt.
    :param: 0 leq amt leq 1.
    1 is fully white, and 0 is unchanged.
    """
    for col in cols:
        high_point = fade(col, amt)
        get_col_range(col, high_point, res)

def fade(color, scalar):
    """returns a color renormalized up by scalar"""
    newcol = []
    for col in rgb_to_int(color):
        if not col:
            col += 1
        fade = (255 - col) * scalar
        newcol.append(int(clamp(col + fade)))
    return rgb_to_str(*tuple(newcol))

def darken_colors(cols, amt, res):
    """Darkens a color to black by amt.
    :param: 0 leq amt leq 1.
    1 is fully white, and 0 is unchanged.
    """
    for col in cols:
        low_point = fade(col, amt)
        get_col_range(col, low_point, res)

def darken(color, scalar):
    """returns a color renormalized down by scalar"""
    newcol = []
    for col in rgb_to_int(color):
        if not col:
            col += 1
        darken = col * scalar
        newcol.append(int(clamp(col - darken)))
    return rgb_to_str(*tuple(newcol))

def clamp(n):
    if n > 255:
        return 255
    if n < 0:
        return 0
    return n

def rgb_to_int(colstring):
    if colstring[0] == "#":
        colstring = colstring[1:]
    return (int(colstring[0:2],16),int(colstring[2:4],16),int(colstring[4:6],16))

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

def mix_colors(colors, res):
    i = 0
    for i in range(len(colors)-1):
        curr = colors[i]
        nextcol= colors[i+1]
        get_col_range(curr, nextcol, res)
        i += 1
    get_col_range(colors[-1], colors[0], res)

if __name__ == "__main__":
    # Parse arguments:
    parser = argparse.ArgumentParser(description='opts')
    parser.add_argument('-f',
                        dest='fade_amt',
                        type=float,
                        nargs='?',
                        default=0,
                        help='amount to fade (0 is none at all and 1 is entirely white)')
    parser.add_argument('-d',
                        dest='darken_amt',
                        type=float,
                        nargs='?',
                        default=0,
                        help='amount to darken (0 is none at all and 1 is entirely black)')
    parser.add_argument('-r',
                        dest='res',
                        type=int,
                        nargs='?',
                        default=1,
                        help='number of output colors generated per input color')
    parser.add_argument(dest='colors',
                        nargs='+',
                        help='list of colors to form the sequence.')
    args = parser.parse_args()
    colors = []
    for line in args.colors:
        colors.append(line)
    if args.fade_amt:
        fade_colors(colors, args.fade_amt, args.res)
    elif args.darken_amt:
        darken_colors(colors, args.darken_amt, args.res)
    else:
        mix_colors(colors, args.res)
