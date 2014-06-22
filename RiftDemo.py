#! /usr/bin/env python
from OpenGL.GLU import gluLookAt

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
        gluLookAt(
          0, 0, 0.5,
          0, 0, 0,
          0, 1, 0)
        self.modelview = glGetFloatv(GL_MODELVIEW_MATRIX)

    def render_scene(self):
        glClearColor(0.1, 0.1, 0.1, 1)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        draw_color_cube(self.cube_size)


RiftDemo().run();


