import oculusvr as ovr
import numpy as np
import pygame
import pygame.locals as pgl

from OpenGL.GL import *
from cgkit.cgtypes import mat4, vec3, quat
from ctypes import *
from oculusvr import Hmd, ovrGLTexture, ovrPosef, ovrVector3f

class RiftApp():
  def __init__(self):
    ovr.Hmd.initialize()
    self.hmd = ovr.Hmd()
    
    self.hmdDesc = self.hmd.hmd.contents # cast(self.hmd.hmd,POINTER(ovrHmdDesc)).contents
    self.frame = 0
    # Workaround for a race condition bug in the SDK
    import time
    time.sleep(0.1)
    self.hmd.configure_tracking()
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
    self.projections = map(
      lambda pr:
        pr.toList(),
      projections)
    self.eyeTextures = [ ovrGLTexture(), ovrGLTexture() ]
    for eye in range(0, 2):
      size = self.hmd.get_fov_texture_size(
       eye, self.fovPorts[eye])
      eyeTexture = self.eyeTextures[eye]
      eyeTexture.API = ovr.ovrRenderAPI_OpenGL
      header = eyeTexture.Texture.Header;
      header.TextureSize = size
      vp = header.RenderViewport;
      vp.Size = size
      vp.Pos.x = 0
      vp.Pos.y = 0

  def close(self):
    glDeleteFramebuffers(2, self.fbo)
    glDeleteTextures(self.color)
    glDeleteRenderbuffers(2, self.depth)

    self.hmd.destroy()
    self.hmd = None
    ovr.Hmd.shutdown()

  def create_window(self):
    import os
    os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (
      self.hmdDesc.WindowsPos.x,
      self.hmdDesc.WindowsPos.y)
    pygame.init()
    pygame.display.set_mode(
      (
        self.hmdDesc.Resolution.w,
        self.hmdDesc.Resolution.h
      ),
      pgl.HWSURFACE | pgl.OPENGL | pgl.DOUBLEBUF | pgl.NOFRAME)
    window_info = pygame.display.get_wm_info()
    window = c_void_p(window_info['window'])
    ovr.ovrHmd_AttachToWindow(self.hmd.hmd, window, 0, 0)

  def init_gl(self):
    self.fbo = glGenFramebuffers(2)
    self.color = glGenTextures(2)
    self.depth = glGenRenderbuffers(2)

    for eye in range(0, 2):
      self.build_framebuffer(eye)
      self.eyeTextures[eye].OGL.TexId = np.asscalar(self.color[eye])

    rc = ovr.ovrRenderAPIConfig()
    header = rc.Header;
    header.API = ovr.ovrRenderAPI_OpenGL
    header.BackBufferSize = self.hmdDesc.Resolution
    header.Multisample = 1
    for i in range(0, 8):
      rc.PlatformData[i] = 0 #ctypes.cast(, ctypes.c_uint)
    self.eyeRenderDescs = \
      self.hmd.configure_rendering(rc, self.fovPorts)

    self.eyeOffsets = [ ovrVector3f(), ovrVector3f() ]
    for eye in range(0, 2):
      self.eyeOffsets[eye] = self.eyeRenderDescs[eye].HmdToEyeViewOffset
      
    # Bug in the SDK leaves a program bound, so clear it
    glUseProgram(0)

  def build_framebuffer(self, eye):
    size = self.eyeTextures[eye].Texture.Header.TextureSize

    # Set up the color attachement texture
    glBindTexture(GL_TEXTURE_2D, self.color[eye])
    glTexParameteri(GL_TEXTURE_2D,
      GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8,
      size.w, size.h, 0, GL_RGB,
      GL_UNSIGNED_BYTE, None)
    glBindTexture(GL_TEXTURE_2D, 0)

    # Set up the depth attachment renderbuffer
    glBindRenderbuffer(GL_RENDERBUFFER, self.depth[eye])
    glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT,
      size.w, size.h)
    glBindRenderbuffer(GL_RENDERBUFFER, 0)

    # Set up the framebuffer proper
    glBindFramebuffer(GL_FRAMEBUFFER, self.fbo[eye])
    glFramebufferTexture2D(GL_FRAMEBUFFER,
      GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D,
      self.color[eye], 0)
    glFramebufferRenderbuffer(GL_FRAMEBUFFER,
      GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER,
      self.depth[eye])
    fboStatus = glCheckFramebufferStatus(GL_FRAMEBUFFER)
    if (GL_FRAMEBUFFER_COMPLETE != fboStatus):
      raise Exception("Bad framebuffer setup")
    glBindFramebuffer(GL_FRAMEBUFFER, 0)

  def render_frame(self):
    self.frame += 1

    # Fetch the head pose
    poses = self.hmd.get_eye_poses(self.frame, self.eyeOffsets)

    self.hmd.begin_frame(self.frame)
    for i in range(0, 2):
      eye = self.hmdDesc.EyeRenderOrder[i]

      glMatrixMode(GL_PROJECTION)
      glLoadMatrixf(self.projections[eye])

      self.eyeview = mat4(1.0)


      # Apply the head orientation
      rot = poses[eye].Orientation
      # Convert the OVR orientation (a quaternion
      # structure) to a cgkit quaternion class, and
      # from there to a mat4  Coordinates are camera
      # coordinates
      rot = quat(rot.toList())
      rot = rot.toMat4()

      # Apply the head position
      pos = poses[eye].Position
      # Convert the OVR position (a vector3 structure)
      # to a cgcit vector3 class. Position is in camera /
      # Rift coordinates
      pos = vec3(pos.toList())
      pos = mat4(1.0).translate(pos)
      
      pose = pos * rot

      # apply it to the eyeview matrix
      self.eyeview = pose;

      # The subclass is responsible for taking eyeview
      # and applying it to whatever camera or modelview
      # coordinate system it uses before rendering the
      # scene

      # Active the offscreen framebuffer and render the scene
      glBindFramebuffer(GL_FRAMEBUFFER, self.fbo[eye])
      size = self.eyeTextures[eye].Texture.Header.RenderViewport.Size
      glViewport(0, 0, size.w, size.h)
      self.render_scene()
      glBindFramebuffer(GL_FRAMEBUFFER, 0)
    self.hmd.end_frame(poses, self.eyeTextures)
    glGetError()

  def update(self):
    for event in pygame.event.get():
      self.on_event(event)

  def on_event(self, event):
    if event.type == pgl.QUIT:
      self.running = False
      return True
    if event.type == pgl.KEYUP and event.key == pgl.K_ESCAPE:
      self.running = False
      return True
    return False

  def run(self):
    self.create_window()
    self.init_gl()
    self.running = True
    start = ovr.Hmd.get_time_in_seconds()
    last = start
    while self.running:
      self.update()
      self.render_frame()
      #pygame.display.flip()
      now = ovr.Hmd.get_time_in_seconds()
      if (now - last > 10):
        interval = now - start
        fps = self.frame / interval
        print "%f" % fps
        last = now
    self.close()
    pygame.quit()
