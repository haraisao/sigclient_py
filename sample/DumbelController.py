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
class DumbelController(sig.SigController):
  def onInit(self, evt):
    self.my = self.getObj()
    self.state = 'STATE_INIT'
    self.time = 0
    self.TIME0 = 0
    self.TIME1 = 15
    self.TIME2 = 30
    return

  def onAction(self, evt):
    self.time += 1
 
    if self.state == 'STATE_INIT' :
      self.setWheelProperty("LINK_LWHEEL", 0.0, 1000.0, 0.0001, 0.0, 0.0, 100.0,
                            "LINK_RWHEEL", 0.0, 1000.0, 0.0001, 0.0, 0.0, 100.0)

      self.state = 'STATE_STEP1'

    elif self.state == 'STATE_STEP1' :
      self.differentialWheelsSetSpeed(5.0,5.0)
      self.state = 'STATE_STEP2'

    elif self.state == 'STATE_STEP2' :
      if self.time > self.TIME1 :
        self.state = 'STATE_STEP3'

    elif self.state == 'STATE_STEP3' :
      self.differentialWheelsSetSpeed(-5.0,-5.0)
      self.state = 'STATE_STEP4'

    elif self.state == 'STATE_STEP4' :
      if self.time > self.TIME2 :
        self.state = 'STATE_STEP1'
        self.time = 0
    return 1.0 

  def onRecvMsg(self, evt):
    return

  def onCollision(self, evt):
    return

#
#  
#
def createController(name, host, port):
  return DumbelController(name, host, port)
