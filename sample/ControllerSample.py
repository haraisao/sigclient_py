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
    obj = self.getObj()
    obj.addForce(0, 0, 500)
    return 1.0 

  def onRecvMsg(self, evt):
    return

  def onCollision(self, evt):
    return

#
#  
#
def createController(name, host, port):
  return MyController(name, host, port)
