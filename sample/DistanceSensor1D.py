#
#  Sample Controlller for SIGVerse
#

import sys
import os
import time
import sig
import math
import random

#
#  Sample controller for SIGVerse
#
class RobotController(sig.SigController):
  def onInit(self, evt):
    self.view = self.connectToService("SIGViewer")
    self.vel = 1.0
    random.seed() 
    return

  def onAction(self, evt):
    try:
      my = self.getObj()
      pos = my.getPosition()
      rot = my.getRotation()

      qy = rot.qy()
      qw = rot.qw()
      tmp = qy * qw
      if tmp < 0:
        qy = -qy

      theta = 2.0 * math.asin(qy)
      dx = dz = 0.0

      dx = math.sin(theta) * self.vel
      dz = math.cos(theta) * self.vel

      my.setPosition(pos.x() + dx, pos.y(), pos.z() + dz)

      fovy = my.getCamFOV() * math.pi / 180.0
      ar = my.getCamAS() 

      fovx = 2 * math.atan(math.tan(fovy * 0.5) * ar) * 180.0 / math.pi

      distance = 255
      if self.view :
        img = self.view.distanceSensor1D()
        buf = img.getBuffer()
        length = img.getBufferLength()
        theta = 0.0

        for i in  range(length) :
          tmp_distance = ord(buf[i])
          if tmp_distance < distance:
             theta = fovx * i / 319.0 - fovx / 2.0
             distance = tmp_distance

      if distance < 100:
        my.setAxisAndAngle(0.0, 1.0, 0.0, random.random() * 2 * math.pi, 1)
      
    except:
      print "ERROR in onAction"

    return 0.1 

  def onRecvMsg(self, evt):
    return

  def onCollision(self, evt):
    return

#
#  
#
def createController(name, host, port):
  return RobotController(name, host, port)
