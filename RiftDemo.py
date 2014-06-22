#! /usr/bin/env python
from RiftApp import *

def draw_color_cube(size=1.0):
    p = size / 2.0
    n = -p
    glBegin(GL_QUADS)

    # front
    glColor3f(1, 1, 0)
    glVertex3f(n, n, n)
    glVertex3f(p, n, n)
    glVertex3f(p, p, n)
    glVertex3f(n, p, n)
    # back
    glColor3f(0.2, 0.2, 1)
    glVertex3f(n, n, p)
    glVertex3f(p, n, p)
    glVertex3f(p, p, p)
    glVertex3f(n, p, p)
    # right
    glColor3f(1, 0, 0)
    glVertex3f(p, n, n)
    glVertex3f(p, n, p)
    glVertex3f(p, p, p)
    glVertex3f(p, p, n)
    # left
    glColor3f(0, 1, 1)
    glVertex3f(n, n, n)
    glVertex3f(n, n, p)
    glVertex3f(n, p, p)
    glVertex3f(n, p, n)
    # top
    glColor3f(0, 1, 0)
    glVertex3f(n, p, n)
    glVertex3f(p, p, n)
    glVertex3f(p, p, p)
    glVertex3f(n, p, p)
    # bottom
    glColor3f(1, 0, 1)
    glVertex3f(n, n, n)
    glVertex3f(p, n, n)
    glVertex3f(p, n, p)
    glVertex3f(n, n, p)
    glEnd()


class RiftDemo(RiftApp):
    def __init__(self):
      RiftApp.__init__(self)
      self.cube_size = self.hmd.get_float(ovr.OVR_KEY_IPD, ovr.OVR_DEFAULT_IPD)

    def init_gl(self):
      RiftApp.init_gl(self)
      glEnable(GL_DEPTH_TEST)
      self.camera = mat4(1.0)
      self.camera.translate(vec3(0, 0, 0.5))
      glClearColor(0.1, 0.1, 0.1, 1)

    def update(self):
      import pygame.locals as pgl
      RiftApp.update(self)
      pressed = pygame.key.get_pressed()

      rotation = 0.0
      if pressed[pgl.K_q]:
          rotation = +1.0
      if pressed[pgl.K_e]:
          rotation = -1.0
      self.camera = self.camera * mat4.rotation(rotation * 0.01, vec3(0, 1, 0))

      # Modify direction vectors for key presses
      translation = vec3()
      if pressed[pgl.K_r]:
          self.hmd.reset_sensor()
      if pressed[pgl.K_w]:
          translation.z = -1.0
      elif pressed[pgl.K_s]:
          translation.z = +1.0
      if pressed[pgl.K_a]:
          translation.x = -1.0
      elif pressed[pgl.K_d]:
          translation.x = +1.0
      self.camera.translate(translation * 0.005)


    def render_scene(self):
      glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
      # apply the camera position

      modelview = self.eyeview * self.camera.inverse()
      glMatrixMode(GL_MODELVIEW)
      glLoadMatrixf(modelview.toList())

      glMultMatrixf(self.camera.inverse().toList())
      draw_color_cube(self.cube_size)


RiftDemo().run();


