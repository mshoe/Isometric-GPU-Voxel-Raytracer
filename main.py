import pygame as pg
import sys
import numpy as np
import math
from spritesheet import *
from sprite_strip_anim import SpriteStripAnim
from isometric import *
from actors import *
# some useful constants
from pygame.locals import *
import random

import moderngl

RESOLUTION_X = 500
RESOLUTION_Y = 500
RESOLUTION = (RESOLUTION_X, RESOLUTION_Y)
# World generation
voxel_set = np.zeros(shape=(world_w, world_l, world_h))
for i in range(world_w):
    for j in range(world_l):
        voxel_set[i][j][0] = 1
for blah in range(100):
    i = random.randint(0, world_w-1)
    j = random.randint(0, world_l-1)
    voxel_set[i][j][0] = 0
blah = 0
while blah < 50:
    i = random.randint(0, world_w-1)
    j = random.randint(0, world_l-1)
    if voxel_set[i][j][0] != 0:
        voxel_set[i][j][1] = 1
        blah += 1

# initialize pygame module
pg.init()

# create new drawing surface
DISPLAYSURF = pg.display.set_mode((RESOLUTION_X, RESOLUTION_Y), DOUBLEBUF | OPENGL)

# give the window a caption
pg.display.set_caption('HARDCORE ROGUELIKE')

FPS = 120
frames = FPS/12

# characters
#ss = spritesheet('Amelit.png')

Amelit_strips = [ \
    SpriteStripAnim('Amelit.png', (0, 0, 80, 93), 8, colorkey = (0, 114, 188), loop = True, frames=frames),
    SpriteStripAnim('Amelit.png', (0, 93, 80, 93), 8, colorkey = (0, 114, 188), loop = True, frames=frames),
    SpriteStripAnim('Amelit.png', (0, 186, 80, 93), 6, colorkey = (0, 114, 188), loop = True, frames=frames),
    SpriteStripAnim('Amelit.png', (0, 279, 80, 93), 6, colorkey = (0, 114, 188), loop = True, frames=frames),
]


Player = Actor(Amelit_strips)
#pos = [100, 100]

cur_fps_font = pg.font.Font(None, 12)
cur_fps = cur_fps_font.render('0', True, WHITE)
fps_counter = 1
dt = 0

f_shader = ""
v_shader = ""
with open('shader.fs', 'r') as fd:
    f_shader = fd.read()

with open('shader.vs', 'r') as fd:
    v_shader = fd.read()
#print(v_shader)
#print(f_shader)

class render_engine():
    def __init__(self):
        self.ctx = moderngl.create_context()

        self.prog = self.ctx.program(
            vertex_shader = v_shader, 
            fragment_shader = f_shader)



        #for key in self.prog:
        #    print(key)
        self.iResolution = self.prog['iResolution']
        self.iMouse = self.prog['iMouse']
        self.iTime = self.prog['iTime']
        

        self.iResolution.value = RESOLUTION
        self.iMouse.value = (0.0, 0.0, 0.0, 0.0)
        self.iTime.value = 0.0
        

        vertices = np.array([
                            -1.0, -1.0, 
                            -1.0, 1.0,
                             1.0, -1.0, 
                             1.0, 1.0])
        self.vbo = self.ctx.buffer(vertices.astype('f4').tobytes())
        self.vao = self.ctx.simple_vertex_array(self.prog, self.vbo, 'vert')
        return

    def update_uniforms(self, mouse_pos, left_click, right_click, itime_):
        #self.iResolution.value = res_
        self.iMouse.value = (float(mouse_pos[0]), RESOLUTION_Y-float(mouse_pos[1]), left_click, right_click)
        self.iTime.value = itime_

        return

    def render(self):
        #self.wnd.fill(BLACK)
        cur_time = pg.time.get_ticks() / 1000.0
        self.ctx.viewport = (0, 0, 500.0, 500.0)
        self.ctx.clear(0.0, 0.0, 0.0)
        self.ctx.enable(moderngl.BLEND)
        self.vao.render(moderngl.TRIANGLE_STRIP)

        pg.display.flip()

    
        return



renderer = render_engine()#DISPLAYSURF)
if __name__ == '__main__':
    clock = pg.time.Clock()
    while True:
        for event in pg.event.get():

            if event.type == QUIT:
                pg.quit()
                sys.exit()

            if event.type == MOUSEBUTTONDOWN:
                dest_pos = pg.mouse.get_pos()
                print(dest_pos)
                dest_pos = np.array([dest_pos[0], dest_pos[1]])
                
                Player.update_dest_pos(voxel_set, dest_pos)

        # drawing the world
        
        #DISPLAYSURF.fill(BLACK)
        '''
        for k in range(voxel_set.shape[2]):
            for j in range(voxel_set.shape[1]):
                for i in range(voxel_set.shape[0]):
                    draw_voxel(voxel_set[i][j][k], (i,j,k), voxel_set, DISPLAYSURF)
        
        #pygame.draw.rect(DISPLAYSURF, GREEN, (100, 50, 20, 20))
        '''
        # Tile highlighter/selecter
        m_pos = pg.mouse.get_pos()
        
        '''
        i, j = get_voxel_coords(m_pos[0], m_pos[1], 0)
        if i >= 0 and i < 20 and j >= 0 and j < 20:
            draw_voxel(2, (i, j, 0), voxel_set, DISPLAYSURF)
        '''
        pos = Player.update_pos(voxel_set, dt)

        '''
        # DEBUGGING CODE, see where player is on
        i, j = Player.update_voxel_pos(voxel_set)
        draw_voxel(PLAYER_SELECTED, (i, j, 0), voxel_set, DISPLAYSURF)
        i -= 1
        if i >= 0 and i < 20 and j >= 0 and j < 20:
            if voxel_set[i][j][0] != 0:
                draw_voxel(PLAYER_SELECTED, (i, j, 0), voxel_set, DISPLAYSURF)
        i += 2
        if i >= 0 and i < 20 and j >= 0 and j < 20:
            if voxel_set[i][j][0] != 0:
                draw_voxel(PLAYER_SELECTED, (i, j, 0), voxel_set, DISPLAYSURF)
        i -= 1
        j -= 1
        if i >= 0 and i < 20 and j >= 0 and j < 20:
            if voxel_set[i][j][0] != 0:
                draw_voxel(PLAYER_SELECTED, (i, j, 0), voxel_set, DISPLAYSURF)
        j += 2
        if i >= 0 and i < 20 and j >= 0 and j < 20:
            if voxel_set[i][j][0] != 0:
                draw_voxel(PLAYER_SELECTED, (i, j, 0), voxel_set, DISPLAYSURF)

        '''
        # finally draw player
        '''
        image = Player.update_image()
        DISPLAYSURF.blit(image, (pos[0] - 40, pos[1] - 70))

        
        # FPS
        fps_counter += dt
        if fps_counter > 250:
            cur_fps = cur_fps_font.render(str(int(clock.get_fps())), True, WHITE)
            fps_counter = 0
        DISPLAYSURF.blit(cur_fps, (15, 15))
        
        # Flip display
        pg.display.flip()
        '''
        renderer.update_uniforms(m_pos, 0, 0, pg.time.get_ticks() / 1000.0)
        renderer.render()

        dt = clock.tick(FPS)
