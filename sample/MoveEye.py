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
class MyController(sig.SigController):
  def onInit(self, evt):
    return

  def onAction(self, evt):
    return 1.0

  def onRecvMsg(self, evt):
    try:
      msg = evt.getMsg()
      obj = self.getObj()
      sender = evt.getSender()
      pos = msg.find(" ")

      if pos > 0 :
        n = 0
        phi = float(msg[:pos])
        theta = float(msg[pos:])
    
        obj.setJointAngle("LEYE_JOINT1", math.radians(phi))
        obj.setJointAngle("REYE_JOINT1", math.radians(phi))
        obj.setJointAngle("LEYE_JOINT0", math.radians(theta))
        obj.setJointAngle("REYE_JOINT0", math.radians(theta))

    except:
      pass

    return

  def onCollision(self, evt):
    return

#
#  
#
def createController(name, host, port):
  return MyController(name, host, port)
