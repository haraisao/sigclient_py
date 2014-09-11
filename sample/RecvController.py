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
class RecvController(sig.SigController):
  def onInit(self, evt):
    self.raise_hand = False
    return

  def onAction(self, evt):
    try:
      obj = self.getObj()
      if self.raise_hand :
        obj.setJointAngle("LARM_JOINT2", math.radians(0))
    except:
      pass

    return 0.5

  def onRecvMsg(self, evt):
    try:
      obj = self.getObj()
      sender = evt.getSender()
      msg = evt.getMsg()
      if msg == "Hello!!" :
        obj.setJointAngle("LARM_JOINT2", math.radians(180))
        self.raise_hand = True
    except:
      pass

    return

  def onCollision(self, evt):
    return

#
#  
#
def createController(name, host, port):
  return RecvController(name, host, port)
