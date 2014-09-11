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
class AgentController(sig.SigController):
  def onInit(self, evt):
    return

  def onAction(self, evt):
    try:
      obj = self.getObj()
      if not obj.dynamics() :
        obj.setJointAngle("LARM_JOINT2", math.radians(45))
    except:
      print "ERROR"
      pass

    return 5.0 

  def onRecvMsg(self, evt):
    return

  def onCollision(self, evt):
    return

#
#  
#
def createController(name, host, port):
  return AgentController(name, host, port)
