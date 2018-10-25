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
from imgui.integrations.pygame import PygameRenderer
import imgui

RESOLUTION_X = 500
RESOLUTION_Y = 500
RESOLUTION = (RESOLUTION_X, RESOLUTION_Y)

CHUNK_W = 50
CHUNK_H = 10

# World generation

voxel_set = np.zeros(shape=(CHUNK_W, CHUNK_H, CHUNK_W), dtype=np.uint32)
for i in range(CHUNK_W):
    for k in range(CHUNK_W):
        voxel_set[i][0][k] = 1
for blah in range(int(0.5 * CHUNK_W * CHUNK_W)):
    i = random.randint(0, CHUNK_W-1)
    k = random.randint(0, CHUNK_W-1)
    voxel_set[i][0][k] = 0

'''    
blah = 0
while blah < 50:
    i = random.randint(0, world_w-1)
    j = random.randint(0, world_l-1)
    if voxel_set[i][j][0] != 0:
        voxel_set[i][j][1] = 1
        blah += 1
'''
chunk = voxel_set.flatten()



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

cur_fps_font = pg.font.Font(None, 100)
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

class Camera():
    def __init__(self, camera_from_, camera_to_, world_up_ = np.array([0.0, 1.0, 0.0])):
        # vectors in the form of a numpy array
        self.camera_from = camera_from_
        self.camera_to = camera_to_
        self.world_up = world_up_

        self.construct_lookat()
        return

    def construct_lookat(self):
        fv = self.camera_from - self.camera_to
        fvl = np.sqrt(np.dot(fv, fv));
        if fvl == 0.0:
            self.forward = np.array([0.0, 0.0, 0.0])
        else:
            self.forward = fv / fvl

        self.right = np.cross(self.world_up, self.forward)
        self.up = np.cross(self.forward, self.right)
        self.world_forward = np.cross(self.world_up, self.right)
        return

    def horizontal_move(self, move):
        self.camera_from += self.right * move
        self.camera_to += self.right * move
        return

    def forward_move(self, move):
        self.camera_from += self.world_forward * move
        self.camera_to += self.world_forward * move
        return

    def vertical_move(self, move):
        self.camera_from += self.world_up * move
        self.camera_to += self.world_up * move
        return

    def rotate_Y_around_to(self, angle):

        angle = math.radians(angle)
        rotation = np.array([[math.cos(angle), 0.0, math.sin(angle)], 
                             [0.0, 1.0, 0.0],
                             [-math.sin(angle), 0.0, math.cos(angle)]])
        self.camera_from -= self.camera_to
        self.camera_from = np.dot(rotation, self.camera_from)
        self.camera_from += self.camera_to
        self.construct_lookat()
        return

    def export_mat4(self):
        # for the glsl uniform

        return tuple(self.right) + tuple([0.0]) + tuple(self.up) + tuple([0.0]) \
             + tuple(self.forward) + tuple([0.0]) + tuple(self.camera_from) + tuple([1.0])

class render_engine():
    def __init__(self, camera_mat4):
        self.ctx = moderngl.create_context()

        self.prog = self.ctx.program(
            vertex_shader = v_shader, 
            fragment_shader = f_shader)

        #for key in self.prog:
        #    print(key)
        self.iResolution = self.prog['iResolution']
        self.iMouse = self.prog['iMouse']
        self.iTime = self.prog['iTime']
        self.camera = self.prog['iCamera']

        self.iResolution.value = RESOLUTION
        self.iMouse.value = (0.0, 0.0, 0.0, 0.0)
        self.iTime.value = 0.0
        self.camera.value = camera_mat4

        vertices = np.array([
                            -1.0, -1.0, 
                            -1.0, 1.0,
                             1.0, -1.0, 
                             1.0, 1.0])
        self.vbo = self.ctx.buffer(vertices.astype('f4').tobytes())
        self.vao = self.ctx.simple_vertex_array(self.prog, self.vbo, 'vert')

        self.chunk_data = self.ctx.buffer(  data = chunk.astype('u4').tobytes() );
        return

    def update_uniforms(self, mouse_pos, left_click, right_click, itime_):
        #self.iResolution.value = res_
        self.iMouse.value = (float(mouse_pos[0]), RESOLUTION_Y-float(mouse_pos[1]), left_click, right_click)
        self.iTime.value = itime_

        return

    def update_camera(self, camera_mat4):
        self.camera.value = camera_mat4
        return

    def render(self):
        #self.wnd.fill(BLACK)
        cur_time = pg.time.get_ticks() / 1000.0
        self.ctx.viewport = (0, 0, 500.0, 500.0)
        self.ctx.clear(0.0, 0.0, 0.0)
        self.ctx.enable(moderngl.BLEND)
        self.vao.render(moderngl.TRIANGLE_STRIP)

        

        return

camera = Camera(np.array([1000.0, 730.0, 1000.0]), np.array([0.0, -100.0, 0.0]))
print(camera.export_mat4())
renderer = render_engine(camera.export_mat4())#DISPLAYSURF)
pg.key.set_repeat(1, 16)

io = imgui.get_io()
io.fonts.add_font_default()
io.display_size = RESOLUTION
imgui_renderer = PygameRenderer()

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

            if event.type == KEYDOWN:
                if event.key == K_RIGHT:
                    camera.rotate_Y_around_to(45.0 * dt)
                elif event.key == K_LEFT:
                    camera.rotate_Y_around_to(-45.0 * dt)
                if event.key == K_d:
                    camera.horizontal_move(1000.0 * dt)
                elif event.key == K_a:
                    camera.horizontal_move(-1000.0 * dt)
                if event.key == K_w:
                    camera.forward_move(1000.0 * dt)
                elif event.key == K_s:
                    camera.forward_move(-1000.0 * dt)
                if event.key == K_SPACE:
                    camera.vertical_move(1000 * dt)
                elif event.key == K_TAB:
                    camera.vertical_move(-1000 * dt)

                renderer.update_camera(camera.export_mat4())

                    

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

        # pos = Player.update_pos(voxel_set, dt)

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

        
        
        
        # Flip display
        pg.display.flip()
        '''


        renderer.update_uniforms(m_pos, 0, 0, pg.time.get_ticks() / 1000.0)
        renderer.render()

        '''
        # FPS
        fps_counter += dt
        if fps_counter > 250:
            cur_fps = cur_fps_font.render(str(int(clock.get_fps())), True, WHITE)
            fps_counter = 0
        DISPLAYSURF.blit(cur_fps, (250, 250))
        '''
        # start new frame context
        imgui.new_frame()

        imgui.show_test_window()

        # open new window context
        imgui.begin("Your first window!", True)

        # draw text label inside of current window
        imgui.text("Hello world!")

        # close current window context
        imgui.end()

        # pass all drawing comands to the rendering pipeline
        # and close frame context
        imgui.render()


        pg.display.flip()
        dt = clock.tick(FPS) / 1000.0
