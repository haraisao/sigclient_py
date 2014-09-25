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

      if self.view :
        distance = self.view.distanceSensor()
        print "Distance = %d" % distance

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
