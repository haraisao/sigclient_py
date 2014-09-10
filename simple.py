#
#  Communication Adaptor for SIGVerse
#

import sys
import os
import time
import sig

#
#  Sample controller for SIGVerse
#
class SimpleController(sig.SigController):
  def onInit(self, evt):
    print "===> Call onInit"
    self.simobj = self.getObj()
    print "<=== Call onInit"
    return

  def onAction(self, evt):
    print "===>Call onAction " , self.getCurrentTime()
    try:
      pos = self.simobj.getPosition()
      print pos
    except:
      self.simobj = self.getObj()
      pass
    return 1.0

  def onRecvMsg(self, evt):
    print "===>Call onRecvMsg from %s msg=%s" % (evt.getSender(), evt.getMsg())
    return

#
# Dummy viewer for test
#
class SigViewer(sig.SigClient):
  def __init__(self):
    SigClient.__init__(self, "viewer")

  def connect(self):
    SigClient.connect(self)
    self.sendInit()

  def sendInit(self):
    self.sendCmd("SIGViewer,SIGViewer,")
    self.sendData("SIGMESSAGE,SIGViewer,")

  def eixt(self):
    SigClient.exit(self)


if __name__ == "__main__":
  ctrl = SimpleController("robot_000")
  ctrl.attach()

  
