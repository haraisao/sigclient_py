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
class SendController(sig.SigController):
  def onInit(self, evt):
    try:
      obj = self.getObj()
      if not obj.dynamics() :
        obj.setJointAngle("LARM_JOINT2", math.radians(-90))
        obj.setJointAngle("RARM_JOINT2", math.radians(90))
        obj.setAxisAndAngle(0, 1.0, 0, math.radians(180))
    except:
      pass
    return

  def onAction(self, evt):
    try:
      obj = self.getObj()
      pos = obj.getPosition()

      obj.setPosition(pos.x(), pos.y(), pos.z()  +20)
      msg = "Hello!!"
    #  self.sendMsg("robot_000", msg)
      self.broadcastMsg(msg, 300.0)

    except:
      pass

    return 1.0 

  def onRecvMsg(self, evt):
    return

  def onCollision(self, evt):
    return

#
#  
#
def createController(name, host, port):
  return SendController(name, host, port)
