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
class MobileController(sig.SigController):
  def onInit(self, evt):
    self.maxForce=500.0
    return

  def onAction(self, evt):
    return 10.0 

  def onRecvMsg(self, evt):
    try:
      my = self.getObj()
      msg = evt.getMsg()

      pos = msg.find(" ") 
      if pos > 0:
        lvel = float(msg[:pos])
        rvel = float(msg[pos:])
        
        my.setJointVelocity("JOINT_LWHEEL", lvel, self.maxForce)
        my.setJointVelocity("JOINT_RWHEEL", rvel, self.maxForce)
        pass
      else:
        pass
    except:
      print "ERROR in RecvMsg"
      pass

    return

  def onCollision(self, evt):
    return

#
#  
#
def createController(name, host, port):
  return MobileController(name, host, port)
