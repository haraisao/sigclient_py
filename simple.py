#
#  Communication Adaptor for SIGVerse
#

import sys
import os
import time
import sig
import math

#
#  Sample controller for SIGVerse
#
class SimpleController(sig.SigController):
  def onInit(self, evt):
    print "===> Call onInit"
    self.simobj = self.getObj()
    self.Colli = False
    self.Colli_cnt = 0

    self.vel = 5
    print "<=== Call onInit"
    return

  def onCollision(self, evt):
    print "===>Call onCollision " , self.getCurrentTime()
    if self.Colli == False and self.Colli_cnt == 0:
      wname = evt.getWith()
      wparts = evt.getWithParts()
      mparts = evt.getMyParts()

      for i in range(len(wname)) :
        qy = self.simobj.qy()
        theta = 2 * math.asin(qy)
        dy = theta - 3.1415926535
        if dy <= - 3.1415926535 :
          dy = -dy - 3.1415926535
        self.simobj.setAxisAndAngle(0, 1.0, 0, dy)
        self.Colli = True
        self.Colli_cnt = 3

    return

  def onAction(self, evt):
    print "===>Call onAction " , self.getCurrentTime()
    try:
      x = self.simobj.x()
      y = self.simobj.y()
      z = self.simobj.z()

      qy = self.simobj.qy()
      theta = 2 * math.asin(qy)

      dx = math.sin(theta) * self.vel
      dz = math.cos(theta) * self.vel

      self.simobj.setPosition(x+dx, y, z+dz)
      if self.Colli_cnt > 0 :
        self.Colli_cnt -= 1
        if self.Colli_cnt <= 0:
          self.Colli = False

    except:
      print "[ERR] in  onAction " 
      self.simobj = self.getObj()
      pass

    return 0.5

  def onRecvMsg(self, evt):
    print "===>Call onRecvMsg from %s msg=%s" % (evt.getSender(), evt.getMsg())
    return

#
# Dummy viewer for test
#
class SigViewer(sig.SigClient):
  def __init__(self):
    SigClient.__init__(self, "viewer")

  def connect(self):
    SigClient.connect(self)
    self.sendInit()

  def sendInit(self):
    self.sendCmd("SIGViewer,SIGViewer,")
    self.sendData("SIGMESSAGE,SIGViewer,")

  def eixt(self):
    SigClient.exit(self)


if __name__ == "__main__":
  ctrl = SimpleController("robot_000")
  ctrl.attach()

  
