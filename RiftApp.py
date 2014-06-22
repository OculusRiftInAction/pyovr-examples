#import OpenGL.GLUT as glut
import oculusvr as ovr
import numpy as np
import time
import pygame
from pygame.locals import *

from OpenGL.GL import *
from OpenGLContext.quaternion import Quaternion 
from oculusvr import ovrQuatToTuple

class RiftApp():
  def __init__(self):
    ovr.Hmd.initialize()
    self.hmd = ovr.Hmd()
    self.hmdDesc = self.hmd.get_desc()
    # Workaround for a race condition bug in the SDK
    time.sleep(0.1)
    self.hmd.start_sensor()
    self.fovPorts = (
      self.hmdDesc.DefaultEyeFov[0],
      self.hmdDesc.DefaultEyeFov[1]
    )
    projections = map(
      lambda fovPort:
        (ovr.Hmd.get_perspective(
           fovPort, 0.01, 1000, True)),
      self.fovPorts
    )
    self.projections = map(ovr.ovrMat4ToTuple, projections)
    self.eyeTextures = [ ovr.texture(), ovr.texture() ]
    for eye in range(0, 2):
      size = self.hmd.get_fov_texture_size(
       eye, self.fovPorts[eye])
      eyeTexture = self.eyeTextures[eye]
      eyeTexture.API = ovr.ovrRenderAPI_OpenGL
      eyeTexture.TextureSize = size
      eyeTexture.RenderViewport.Size = size
      eyeTexture.RenderViewport.Pos.x = 0
      eyeTexture.RenderViewport.Pos.y = 0

  def close(self):
    glDeleteFramebuffers(2, self.fbo)
    glDeleteTextures(self.color)
    glDeleteRenderbuffers(2, self.depth)

    self.hmd.stop_sensor()
    self.hmd.destroy()
    self.hmd = None
    ovr.Hmd.shutdown()

  def create_window(self):
    import os
    os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (
      self.hmdDesc.WindowsPos.x,self.hmdDesc.WindowsPos.y)

    pygame.init()
    pygame.display.set_mode(
      (
        self.hmdDesc.Resolution.w,
        self.hmdDesc.Resolution.h
      ),
      HWSURFACE|OPENGL|DOUBLEBUF|NOFRAME)

  def init_gl(self):
    self.fbo = glGenFramebuffers(2)
    self.color = glGenTextures(2)
    self.depth = glGenRenderbuffers(2)

    for eye in range(0, 2):
      self.build_framebuffer(eye)
      tex_id = np.asscalar(self.color[eye]) 
      tex_id = ctypes.cast(tex_id, ctypes.POINTER(ctypes.c_ulong))
      self.eyeTextures[eye].TexId = tex_id

    rc = ovr.ovrRenderAPIConfig()
    rc.API = ovr.ovrRenderAPI_OpenGL
    rc.RTSize = self.hmdDesc.Resolution
    rc.Multisample = 1
    for i in range(0, 8):
      rc.PlatformData[i] = ctypes.cast(0, ctypes.POINTER(ctypes.c_ulong))
    self.eyeRenderDescs = \
      self.hmd.configure_rendering(rc, self.fovPorts)
    # Bug in the SDK leaves a program bound, so clear it
    glUseProgram(0)


  def build_framebuffer(self, eye):
    size = self.eyeTextures[eye].TextureSize

    # Set up the color attachement texture
    glBindTexture(
      GL_TEXTURE_2D, 
      self.color[eye])
    glTexParameteri(
      GL_TEXTURE_2D,
      GL_TEXTURE_MIN_FILTER,
      GL_LINEAR);
    glTexImage2D(
      GL_TEXTURE_2D, 0, GL_RGBA8,
      size.w, size.h, 0, GL_RGB,
      GL_UNSIGNED_BYTE, None);
    glBindTexture(GL_TEXTURE_2D, 0)

    # Set up the depth attachment renderbuffer
    glBindRenderbuffer(
      GL_RENDERBUFFER,
      self.depth[eye])
    glRenderbufferStorage(
      GL_RENDERBUFFER,
      GL_DEPTH_COMPONENT,
      size.w, size.h)
    glBindRenderbuffer(
      GL_RENDERBUFFER, 0)

    # Set up the framebuffer proper
    glBindFramebuffer(
      GL_FRAMEBUFFER,
      self.fbo[eye])
    glFramebufferTexture2D(
      GL_FRAMEBUFFER,
      GL_COLOR_ATTACHMENT0,
      GL_TEXTURE_2D,
      self.color[eye], 0);
    glFramebufferRenderbuffer(
      GL_FRAMEBUFFER,
      GL_DEPTH_ATTACHMENT,
      GL_RENDERBUFFER,
      self.depth[eye])

    fboStatus = glCheckFramebufferStatus(
      GL_FRAMEBUFFER)
    if (GL_FRAMEBUFFER_COMPLETE != fboStatus):
      raise Exception("Bad framebuffer setup")
    glBindFramebuffer(GL_FRAMEBUFFER, 0)

  def render_frame(self):
    glClearColor(1, 0, 0, 1);
    glClear(GL_COLOR_BUFFER_BIT)
    self.hmd.begin_frame()
    for i in range(0, 2):
      eye = self.hmdDesc.EyeRenderOrder[i];

      glMatrixMode(GL_PROJECTION)
      glLoadMatrixf(self.projections[eye])

      glMatrixMode(GL_MODELVIEW)
      glLoadIdentity()

      # Apply the per-eye offset
      eyeOffset = ovr.ovrVec3ToTuple(self.eyeRenderDescs[eye].ViewAdjust)
      glTranslate(eyeOffset[0], eyeOffset[1], eyeOffset[2])

      # Fetch the head pose
      pose = self.hmd.begin_eye_render(eye)

      # Apply the head orientation
      q = ovrQuatToTuple(pose.Orientation);
      orientation = Quaternion(q).inverse()
      orientation = orientation.matrix()
      glMultMatrixf(orientation)

      # Apply the head position
      position = ovr.ovrVec3ToTuple(pose.Position)
      glTranslate(-position[0], -position[1], -position[2])

      # apply the camera position
      glMultMatrixf(self.modelview)

      # Active the offscreen framebuffer and render the scene
      glBindFramebuffer(GL_FRAMEBUFFER, self.fbo[eye])
      size = self.eyeTextures[eye].RenderViewport.Size
      glViewport(0, 0, size.w, size.h)
      self.render_scene()
      glBindFramebuffer(GL_FRAMEBUFFER, 0)

      self.hmd.end_eye_render(eye, self.eyeTextures[eye], pose)
    self.hmd.end_frame()


  def run(self):
    self.create_window()
    self.init_gl()
    running = True
    frame = 0
    start = ovr.Hmd.get_time_in_seconds()
    last = start
    while running:
      for event in pygame.event.get():
        if event.type == QUIT:
          running = False
        if event.type == KEYUP and event.key == K_ESCAPE:
          running = False
      self.render_frame()
      pygame.display.flip()
      frame = frame + 1
      now = ovr.Hmd.get_time_in_seconds()
      if (now - last > 10):
        interval = now - start 
        fps = frame / interval
        print "%f" % fps
        last = now
    self.close()
    pygame.quit()
