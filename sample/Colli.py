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
class AgentController(sig.SigController):
  def onInit(self, evt):
    self.simobj = self.getObj()
    self.Colli = False
    self.Colli_cnt = 0
    self.vel = 0.

    if self.name.find("000") >= 0:
      self.vel = 1.
    elif self.name.find("001") >= 0:
      self.vel = 2.

    return

  def onCollision(self, evt):
    if self.Colli == False and self.Colli_cnt == 0:
      wname = evt.getWith()
      wparts = evt.getWithParts()
      mparts = evt.getMyParts()

      for i in range(len(wname)) :
        qy = self.simobj.qy()
        theta = 2 * math.asin(qy)
        dy = theta-math.pi
        if dy <= -math.pi :
          dy = -dy-math.pi
        self.simobj.setAxisAndAngle(0, 1.0, 0, dy)
        self.Colli = True
        self.Colli_cnt = 3

    return

  def onAction(self, evt):
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

    return 0.1

  def onRecvMsg(self, evt):
    return

#
#  
#
def createController(name, host, port):
  return AgentController(name, host, port)
