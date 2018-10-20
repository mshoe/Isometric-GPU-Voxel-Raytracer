import pygame as pg
import numpy as np
from isometric import *

EAST = 0
WEST = 1
NORTH = 0
SOUTH = 1

STANDING_S = 0
STANDING_N = 1
WALKING_S = 2
WALKING_N = 3


class Actor:
	def __init__(self, strips):
		self.strips = strips
		self.state = STANDING_S
		self.pos = np.array([100, 200])
		self.dest_pos = np.array([100, 200])
		self.direction = np.zeros(shape=(2))
		self.movement = np.zeros(shape=(2))
		self.facing = (SOUTH, WEST)
		self.dir_mag = 0
		self.speed = 125
		self.voxel_pos = (0, 0)
		return

	def update_facing(self):
		horizontal = 0
		vertical = 0
		
		horizontal = EAST if self.direction[0] > 0 else WEST
		vertical = NORTH if self.direction[1] < 0 else SOUTH
		self.facing = (vertical, horizontal)
		return

	def update_voxel_pos(self, voxel_set):
		i, j = get_voxel_coords(self.pos[0], self.pos[1], 0)
		out_of_bounds = False
		if i < 0 or i >= 20 or j < 0 or j >= 20:
			out_of_bounds = True
			
		i = 0 if i < 0 else i
		i = 19 if i >= 20 else i
		j = 0 if j < 0 else j
		j = 19 if j >= 20 else j

		self.voxel_pos = (i, j)
		return self.voxel_pos


	def update_dest_pos(self, voxel_set, dest_pos):

		i, j = get_voxel_coords(dest_pos[0], dest_pos[1], 0)
		out_of_bounds = False
		if i < 0 or i >= 20 or j < 0 or j >= 20:
			out_of_bounds = True
			
		i = 0 if i < 0 else i
		i = 19 if i >= 20 else i
		j = 0 if j < 0 else j
		j = 19 if j >= 20 else j
		'''
		if voxel_set[i][j][0] == 1:
			print("collision tile")
		if out_of_bounds:
			X, Y = get_3D_coords(i, j, 0)
			self.dest_pos = np.array([X - 40, Y - 70])
		else:
			'''
		self.dest_pos = np.array([dest_pos[0], dest_pos[1]])
		
		self.direction = self.dest_pos - self.pos

		# keep track of either x or y coordination magnitude of direction
		# because if we keep subtracting ab(dx) from dest_x, we will know
		# when we have passed the destination when it goes negative
		self.dest_x = abs(self.direction[0])

		self.dir_mag = np.linalg.norm(self.direction)
		self.unit_dir = self.direction/self.dir_mag
		self.update_facing()
		if self.dir_mag != 0:
			self.state = WALKING_S if self.facing[0] == SOUTH else WALKING_N

		#print(i, j)
		return

	def update_pos(self, voxel_set, dt):
		if self.state == WALKING_N or self.state == WALKING_S:
			
			movement = self.unit_dir * self.speed * dt / 1000

			# subtract distance squared instead of distance?
			self.dest_x -= abs(movement[0])

			if self.dest_x <= 0:
				new_pos = self.dest_pos
				self.state = STANDING_S if self.facing[0] == SOUTH else STANDING_N
				self.dest_mag = 0
			else:
				new_pos = self.pos + movement
			#if i < 0 or i >= 20 or j < 0 or j >= 20:
			#	self.dest_pos = self.pos
			#elif voxel_set[i][j][0] == 1:
			#	self.dest_pos = self.pos
			#else:
			self.pos = new_pos
		
		return self.pos

	def update_image(self):
		image = self.strips[self.state].next()
		if self.facing[1] ==  EAST:
			image = pg.transform.flip(image, True, False)
		return image