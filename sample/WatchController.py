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
    return

  def onAction(self, evt):
    return 1.0 

  def onRecvMsg(self, evt):
    try:
     obj = self.getObj()
     value = evt.getMsg()
     angle = int(value)
     if angle <= 180 and angle >= -180 :
       obj.setAxisAndAngle(0, 1.0, 0, math.radians(angle))
    except:
      print "ERROR"
      pass

    return

  def onCollision(self, evt):
    return

#
#  
#
def createController(name, host, port):
  return WatchController(name, host, port)
