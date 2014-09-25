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
class WatchController(sig.SigController):
  def onInit(self, evt):
    self.raise_hand = False
    self.view = self.connectToService("SIGViewer")
    return

  def onAction(self, evt):
    try:
      my = self.getObj()
      if self.raise_hand :
        my.setJointAngle("LARM_JOINT2", math.radians(0)) 
      if self.view :
        ent = self.view.detectEntities(1)
        if ent and "orange_0" in ent:
          my.setJointAngle("LARM_JOINT2", math.radians(180)) 
          self.raise_hand = True
    except:
      print "ERROR in anAction"

    return 1.0 

  def onRecvMsg(self, evt):
    try:
     obj = self.getObj()
     value = evt.getMsg()
     angle = int(value)
     if angle <= 180 and angle >= -180 :
       obj.setAxisAndAngle(0, 1.0, 0, math.radians(angle))
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
  return WatchController(name, host, port)
