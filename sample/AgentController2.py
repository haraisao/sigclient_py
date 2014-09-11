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
    try:
      obj = self.getObj()
      if not obj.dynamics() :
        obj.setJointAngle("LARM_JOINT2", math.radians(-90))
        obj.setJointAngle("RARM_JOINT2", math.radians(90))
    except:
      pass
    return

  def onAction(self, evt):
    return 10.0 

  def onRecvMsg(self, evt):
    try:
      obj = self.getObj()
      msg = evt.getMsg()
      if msg == "Hello" :
#        obj.setJointAngle("WAIST_JOINT1", math.radians(45))
        obj.setJointQuaternion("WAIST_JOINT1", 0.707, 0.707, 0.0, 0.0)
      else:
        print msg
      
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
  return AgentController(name, host, port)
