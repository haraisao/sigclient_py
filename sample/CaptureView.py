#
#  Sample Controlller for SIGVerse
#

import sys
import os
import time
import sig
import math

#
#  Sample controller for SIGVerse
#
class RobotController(sig.SigController):
  def onInit(self, evt):
    self.vel=10.0
    self.view = self.connectToService("SIGViewer")
    self.iImage = 0
    return

  def onAction(self, evt):
    return 10.0 

  def onRecvMsg(self, evt):
    try:
     if evt is None:
        print "evt is None"
        return

     msg = evt.getMsg()

     if msg == "capture" :
       if not self.view  is None :
         img = self.view.captureView(2, 'RGB24', '320x240')
         if img :
           buf = img.getBuffer()
           fname = "view%03d.bmp" % self.iImage
           self.iImage += 1
           print "save image to %s" % fname
           img.saveAsWindowsBMP(fname)

     elif msg == "rotation" :
       my = self.getObj()
       qy = my.qy()
       theta = 2.0 * math.asin(qy)
       y = theta + math.radians(45.)

       if y >= math.pi :
         y = y - 2*math.pi

       my.setAxisAndAngle(0, 1.0, 0, y)

     elif msg == "move" :
       my = self.getObj()
       pos = my.getPosition()
       qy = my.qy()
       theta = 2.0 * math.asin(qy)
       dx = 0.0
       dz = 0.0
       dx = math.sin(theta) * self.vel
       dz = math.cos(theta) * self.vel
       my.setPosition(pos[0] + dx, pos[1], pos[2] + dz)

     else:
       pass

    except:
      print "ERROR in onRecvMsg"
      pass

    return

  def onCollision(self, evt):
    return

#
#  
#
def createController(name, host, port):
  return RobotController(name, host, port)
