import pygame as pg
import numpy as np

# Define the colors we will use in RGB format
BLACK = (  0,   0,   0)
WHITE = (255, 255, 255)
BLUE =  (  0,   0, 255)
GREEN = (  0, 255,   0)
MEDIUM_GREEN = (0, 125, 0)
DARK_GREEN = (  0, 55,   0)
RED =   (255,   0,   0)
YELLOW = (255, 255, 0)
MEDIUM_YELLOW = (125, 125, 0)
DARK_YELLOW = (55, 55, 0)

# Game constants
vox_h = 12.5 # tile height
vox_w = 50 # tile width/length

world_w = 20
world_l = 20
world_h = 20

SCREEN_HEIGHT = 500

SELECTED = 2
PLAYER_SELECTED = 3

def get_screen_coords(i, j, k):
	X = (i * vox_w / 2) + (j * vox_w / 2)
	Y = (j * vox_w / 4) - (i * vox_w / 4) + (-k + 20) * vox_h
	return X, Y

def get_voxel_coords(x, y, z):

	y = y - SCREEN_HEIGHT/2
	i = int((x - 2*y) / vox_w + 0.5)
	j = int((x + 2*y) / vox_w + 0.5)
	return i, j

def draw_voxel(vox_type, pos, voxel_set, display_surf):
	# vox_type: an enum describing the type of voxel
	# pos = (i, j, k)
	edge_width = 2


	if vox_type == 0:
		return
	elif vox_type == 1:
		tile_color = GREEN
		edge_color = DARK_GREEN
		side_color = MEDIUM_GREEN
	elif vox_type == SELECTED:
		tile_color = WHITE
		edge_color = WHITE
		side_color = BLACK
	elif vox_type == PLAYER_SELECTED:
		tile_color = YELLOW
		edge_color = DARK_YELLOW
		side_color = MEDIUM_YELLOW

	i = pos[0]
	j = pos[1]
	k = pos[2]

	i_b = i - 1
	j_n = j + 1
	k_n = k + 1

	X, Y = get_screen_coords(i, j, k)

	
	corner_left = np.array((X - vox_w/2, Y))
	corner_up = np.array((X, Y + vox_w/4))
	corner_right = np.array((X + vox_w/2, Y))
	corner_down = np.array((X, Y - vox_w/4))

	top_tile = (corner_left, corner_up, corner_right, corner_down, corner_left)
	edge_down = np.array((0, vox_h))
	left_tile = (corner_left, corner_left + edge_down, corner_up + edge_down, corner_up)
	right_tile = (corner_up, corner_up + edge_down, corner_right + edge_down, corner_right)

	# draw the top tile
	if k_n < world_h:
		if voxel_set[i][j][k_n] == 0:
			
			pg.draw.polygon(display_surf, tile_color, top_tile)

	
	# draw the sides of the voxel
	if i_b >= 0:
		if voxel_set[i_b][j][k] == 0:	
			pg.draw.polygon(display_surf, side_color, left_tile)
	else:
		pg.draw.polygon(display_surf, side_color, left_tile)

	if j_n < world_l:
		if voxel_set[i][j_n][k] == 0:
			
			pg.draw.polygon(display_surf, side_color, right_tile)
			
	#
	#pg.draw.polygon(display_surf, tile_color, right_tile)

	# draw the wireframe
	if k_n < world_h:
		if voxel_set[i][j][k_n] == 0:
			pg.draw.lines(display_surf, edge_color, False, top_tile, edge_width)

	if i_b > 0:
		if voxel_set[i_b][j][k] == 0:
			pg.draw.lines(display_surf, edge_color, False, left_tile, edge_width)

	if j_n < world_l:
		if voxel_set[i][j_n][k] == 0:
			pg.draw.lines(display_surf, edge_color, False, right_tile, edge_width)
	
	#pg.draw.line(display_surf, edge_color, corner_left, corner_left + edge_down , edge_width)
	#pg.draw.line(display_surf, edge_color, corner_up, corner_up + edge_down, edge_width)
	#pg.draw.line(display_surf, edge_color, corner_right, corner_right + edge_down, edge_width)
	#bot_edge = (corner_left + edge_down, corner_up + edge_down, corner_right + edge_down)
	#pg.draw.lines(display_surf, edge_color, False, bot_edge, edge_width)
	
def raycast_mouse(voxel_set, display_surf):
	# use some algorithm to determine which voxel the mouse is seeing

	return