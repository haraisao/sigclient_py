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
class MoveController(sig.SigController):
  def onInit(self, evt):
    return

  def onAction(self, evt):
    try:
      my = self.getObj()
      #my.addJointTorque("JOINT2", 50000.0)
      my.setJointVelocity("JOINT2", 1.57, 50000.0)
    except:
      print "ERROR"
      pass

    return 0.1

  def onRecvMsg(self, evt):
    return

  def onCollision(self, evt):
    return

#
#  
#
def createController(name, host, port):
  return MoveController(name, host, port)
