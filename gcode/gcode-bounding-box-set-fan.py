# -*- coding: utf-8 -*-
"""
Created on Tue Aug  6 21:03:31 2024

@author: Xiaotian Guan
"""


def GenLineOffset(FILE):
    # Read in the file once and build a list of line offsets
    # Using FILE.tell() is very slow, but only this produces correct offset values
    offset = 0
    line_offset = []
    line_offset.append(offset)
    line = FILE.readline()
    while line:
        offset = FILE.tell()
        line_offset.append(offset)
        line = FILE.readline()
    FILE.seek(0)
    return line_offset


def GetZ(LINE):
    if ("Z:" in LINE):
        z = 0
        try:
            z = float(LINE.split(':')[1])
            return z
        except ValueError:
            print(LINE)
    else:
        return -1


def GetXY(LINE):
    if ("G1" in LINE) or ("G2" in LINE) or ("G3" in LINE):
        x = -1
        y = -1
        try:
            tmp = LINE.split(' ')
            for t in tmp:
                if t[0] == 'X':
                    x = float(t[1::])
                elif t[0] == 'Y':
                    y = float(t[1::])
                else:
                    pass
            return x, y
        except ValueError:
            print(LINE)
    else:
        return -1, -1


def IfM107(LINE):
    if ("M107" in LINE):
        return True
    else:
        return False


def SetFan(GCODE, X_LOW, X_HIGH, Y_LOW, Y_HIGH, Z_LOW, Z_HIGH, FAN_SPEED, OUTPUT = "output.gcode"):
    with open(GCODE) as gcode, open(OUTPUT, "w") as output:
        offset = GenLineOffset(gcode)
        current_z = 0
        i = 0
        for line in gcode:
            z = GetZ(line)
            # check if this line indicates layer change
            if z != -1:
                # layer change, update current_z
                current_z = z
                enter_flag = False
                gcode.seek(offset[i])
                output.write(gcode.readline())
                i += 1
            else:
                # this line is still for layer at height current_z
                if (current_z < Z_LOW or current_z > Z_HIGH):
                    # current_z outside the bounding box, copy
                    gcode.seek(offset[i])
                    output.write(gcode.readline())
                else:
                    # current_z inside the bounding box
                    x, y = GetXY(line)
                    if (not enter_flag) and (x >= X_LOW and x <= X_HIGH and y >= Y_LOW and y <= Y_HIGH):
                        # the last line has not entered the bounding box yet
                        # this line enters the bounding box, turn fan on
                        enter_flag = True
                        output.write('M106 S%.1f\n' %FAN_SPEED)
                        gcode.seek(offset[i])
                        output.write(gcode.readline())
                    elif enter_flag:
                        # the last line is already in the bounding box
                        
                        if IfM107(line):
                            i += 1
                            next
                        
                        if (x < X_LOW or x > X_HIGH or y < Y_LOW or y > Y_HIGH):
                            # this line exits the bounding box, turn fan off
                            gcode.seek(offset[i])
                            output.write(gcode.readline())
                            output.write('M107\n')
                            enter_flag = False
                        else:
                            # this line still ends in the bounging box
                            gcode.seek(offset[i])
                            output.write(gcode.readline())
                    else:
                        # the last line is not in the bounding box
                        # and this line does not enter the bounding box
                        gcode.seek(offset[i])
                        output.write(gcode.readline())
                i += 1
    return 0


if __name__=='__main__':
    gcode = "OMiGaS-top-shell_0.4n_0.15mm_PETG_MINIIS_2h0m.gcode"
    SetFan(gcode, 50, 62, 108-3.5, 108+3.5, 1.6, 8.0, 75, "OMiGaS-top-shell-fan_0.4n_0.15mm_PETG_MINIIS_2h0m.gcode")
