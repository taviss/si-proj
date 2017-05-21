from luma.core.render import canvas
from luma.core.virtual import viewport
from luma.core.sprite_system import framerate_regulator

from luma.led_matrix.device import max7219
from luma.core.serial import spi, noop
from luma.core.render import canvas
from luma.core.virtual import viewport
from luma.core.legacy import text, show_message

import re
import time
import argparse


#IMPORTANT: (Width, Height) = (16, 8), but we're using it as (8, 16), so (0, 0) is (0, 7)

#These are mirrored, thus 0000 1111 is in fact 1111 0000
#and e.g 0001 1110 is 0111 1000(left is right when moving)
PIECES = [
	[0x0F, 0x00, 0x00, 0x00],
	[0x00, 0xF0, 0x30, 0x00],
	[0x00, 0x0F, 0x03, 0x00],
	[0xF0, 0xF0, 0x30, 0x00]
]

PIECES_90 = [
        [0x01, 0x01, 0x01, 0x01],
        [0x30, 0x30, 0x20, 0x20],
        [0x03, 0x03, 0x02, 0x02],
        [0xE0, 0xE0, 0xC0, 0xC0]
]

PIECES_180 = [
        [0x0F, 0x00, 0x00, 0x00],
        [0x30, 0x3C, 0x00, 0x00],
        [0x0C, 0x0F, 0x00, 0x00],
        [0xC0, 0xF0, 0xF0, 0x00]
]

PIECES_270 = [
        [0x01, 0x01, 0x01, 0x01],
        [0x04, 0x04, 0x0C, 0x0C],
        [0x01, 0x01, 0x03, 0x03],
        [0x30, 0x30, 0x70, 0x70]
]

MOVES_TRACE = []

CURRENT_PIECE = []
CURRENT_PIECE_INDEX = 0

ROTATE_INDEX = 0

w, h = 8, 16;
SCREEN = [[0 for x in range(w)] for y in range(h)]


def move_right():
        global CURRENT_PIECE
        i = 0
        #print CURRENT_PIECE
        for line in CURRENT_PIECE:
		if line > 0:
                        if line & 0x80 > 0:
                                print "Move right blocked"
                                return
                        line <<= 1
                        CURRENT_PIECE[i] = line
                        #print "Line " + str(i) + ":" + str(line)
                i += 1
                        
        #print CURRENT_PIECE
        global MOVES_TRACE
        MOVES_TRACE.append(1)
        print "Moved right"

def move_right_raw():
        global CURRENT_PIECE
        i = 0
        #print CURRENT_PIECE
        for line in CURRENT_PIECE:
		if line > 0:
                        if line & 0x80 > 0:
                                print "Move right blocked"
                                return
                        line <<= 1
                        CURRENT_PIECE[i] = line
                        #print "Line " + str(i) + ":" + str(line)
                i += 1

def move_left():
        global CURRENT_PIECE
        i = 0
        for line in CURRENT_PIECE:
		if line > 0:
                        if line & 0x01 > 0:
                                print "Move left blocked"
                                return
                        line >>= 1
                        CURRENT_PIECE[i] = line
                        #print line
                i += 1
                        
        #print CURRENT_PIECE
        global MOVES_TRACE
        MOVES_TRACE.append(-1)
        print "Moved left"

def move_left_raw():
        global CURRENT_PIECE
        i = 0
        for line in CURRENT_PIECE:
		if line > 0:
                        if line & 0x01 > 0:
                                print "Move left blocked"
                                return
                        line >>= 1
                        CURRENT_PIECE[i] = line
                        #print line
                i += 1

def get_total_lines():
	total = 0
	for line in CURRENT_PIECE:
		if line > 0:
			total += 1
			
	return total
	
def get_piece():
	i = 0
	new_piece = []
	for line in CURRENT_PIECE:
		if line > 0:
			new_piece.append(line)
			i += 1
			
	return new_piece
	
def get_line_list(line):
	line_list = [0, 0, 0, 0, 0, 0, 0, 0]
	for i in range(8):
		if line & 0x01 > 0:
			line_list[i] = 1
		line >>= 1
	return line_list

def get_lines_matrix():
        lines = [[0 for x in range(4)] for y in range(4)]
        i = 0
        for line in CURRENT_PIECE:
                k = 0
                for j in range(8):
                        if line & 0x01 > 0:
                                lines[i][k] = 1
                                k += 1
                        line >>= 1
                i += 1
        return lines

def rotate():
        global CURRENT_PIECE
        global ROTATE_INDEX

        if ROTATE_INDEX == 0:
                CURRENT_PIECE = PIECES_90[CURRENT_PIECE_INDEX]
                #print CURRENT_PIECE
                apply_moves()
                ROTATE_INDEX = 1
        elif ROTATE_INDEX == 1:
                #TODO
                CURRENT_PIECE = PIECES_180[CURRENT_PIECE_INDEX]
                apply_moves()
                ROTATE_INDEX = 2
        elif ROTATE_INDEX == 2:
                #TODO
                CURRENT_PIECE = PIECES_270[CURRENT_PIECE_INDEX]
                apply_moves()
                ROTATE_INDEX = 3
        elif ROTATE_INDEX == 3:
                #TODO
                CURRENT_PIECE = PIECES[CURRENT_PIECE_INDEX]
                apply_moves()
                ROTATE_INDEX = 0

def apply_moves():
        print CURRENT_PIECE
        print MOVES_TRACE
        print len(MOVES_TRACE)
        for move in MOVES_TRACE:
                print "MOVE: " + str(move)
                if move == -1:
                        print "Apply left"
                        move_left_raw()
                elif move == 1:
                        print "Apply right"
                        move_right_raw()
        print CURRENT_PIECE
                                
        
	
def draw_piece(virtual, piece, line):

	total_lines = get_total_lines()
	
	new_piece = get_piece()

	global MOVES_TRACE
	
	print("Line: " + str(line) + ", Total lines:" + str(total_lines))
	if line + total_lines == 16:
		y = line
		print("y = " + str(y))
		#draw the current screen
	
		with canvas(virtual) as draw:
			for i in range(h):
				for j in range(w):
					if SCREEN[i][j] > 0:
						#print("Drawing " + str(i) + " " + str(j))
						draw.point((i, 7-j), fill="white")
			for piece_line in new_piece:
				x = 0
				for j in range(8):
					if piece_line & 0x01 > 0:
						#print("Drawing " + str(y) + " " + str(x))
						draw.point((y, 7-x), fill="white")
						#print("Set SCREEN[" + str(y) + "][" + str(x) + "]")
						SCREEN[y][x] = 1
				
							
					x += 1
					piece_line >>= 1
				y += 1
		MOVES_TRACE = []
		return False
		
	not_reached_bottom = True
	with canvas(virtual) as draw:
		#draw the current pieces
		for i in range(h):
			for j in range(w):
				if SCREEN[i][j] > 0:
					#print("Drawing " + str(i) + " " + str(j))
					draw.point((i, 7-j), fill="white")
		#draw the new piece
		y = line
		
		last_line = new_piece[-1]
		last_line_list = get_line_list(last_line)
		last_line_index = y+total_lines
		#print("Last line: " + str(last_line_index))
		#for p in last_line_list: print p
		if last_line_index > 0:
			for i in range(w):
				#print("Screen[" + str(i) + "]=" + str(SCREEN[last_line_index][i]) + "line=" + str(last_line_list[i]))
				if SCREEN[last_line_index][i] == 1 and last_line_list[i] == 1:
					print("Interference (" + str(last_line_index) + ", " + str(i) + ")")
					not_reached_bottom = False
					MOVES_TRACE = []
					break
		
		for piece_line in new_piece:
			x = 0
			for j in range(8):
				if piece_line & 0x01 > 0:
					#print("Drawing " + str(y) + " " + str(x))
					draw.point((y, 7-x), fill="white")
					if not not_reached_bottom:
						#print("Set SCREEN[" + str(y) + "][" + str(x) + "]")
						SCREEN[y][x] = 1
			
						
				x += 1
				piece_line >>= 1
			y += 1
	
	
	time.sleep(1)
	return not_reached_bottom
	#for i in range(virtual.width - device.width):
	#	print(str(i))
	#	virtual.set_position((2-i, 0))
	#	time.sleep(0.5)
		
def test():
    
	serial = spi(port=0, device=0, gpio=noop())
	device = max7219(serial, cascaded=2, block_orientation=90)
	print("Device created")
	print("W:" + str(device.width) + " H:" + str(device.height))
	virtual = viewport(device, width=16, height=8)
	global CURRENT_PIECE
	global CURRENT_PIECE_INDEX
	line = 1
	CURRENT_PIECE = PIECES[2][:]
	CURRENT_PIECE_INDEX = 2
        #print zip(*lines_matrix[::-1])
	while draw_piece(virtual, 0, line):
                if line == 3:
                        move_left()
                        move_right()
                        move_right()
                        #move_right()
                        #move_right()
                if line == 4:
                        rotate()
                        move_right()
                if line == 5:
                        #print "Moves: " + str(MOVES_TRACE)
                        rotate()
                        rotate()
                        rotate()
		line += 1
		
	for p in SCREEN: print p
	line = -3
	CURRENT_PIECE = PIECES[0][:]
	while draw_piece(virtual, 0, line):
		line += 1
	for p in SCREEN: print p
	line = -3
	CURRENT_PIECE = PIECES[1][:]
	while draw_piece(virtual, 1, line):
		line += 1
	for p in SCREEN: print p
	line = -3
	CURRENT_PIECE = PIECES[2][:]
	while draw_piece(virtual, 2, line):
		line += 1
	for p in SCREEN: print p
	print("End draw")
	time.sleep(1)
		
if __name__ == "__main__":
	try:
		while True:
			for i in range(16):
				for j in range(8):
					SCREEN[i][j] = 0
			test()
	except KeyboardInterrupt:
		pass
