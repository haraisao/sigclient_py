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
      if not self.view is None :
        ent = []
        b = self.view.detectEntities(ent, 1)
        if b and len(ent) > 0 :
          for name in ent:
            if name == "orange_0" :
              my.setJointAngle("LARM_JOINT2", math.radians(180)) 
              self.raise_hand = True
    except:
      print "ERROR in anAction"
      pass
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
