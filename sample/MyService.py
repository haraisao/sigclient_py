#! /usr/bin/python

from sigservice import *

class MyService(SigService):
  def onAction(self, evt=None):
    return 1.0 

  def onRecvMsg(self, evt):
    sender = evt.getSender()
    msg = evt.getMsg()

    if msg == "Hello" :
      self.sendMsgToCtrl(sender, "Hello! this is MyService")
    return 

if __name__ == "__main__" :

  srv = MyService("MyService")
  srv.connect("localhost", 9000)
  srv.startLoop()

