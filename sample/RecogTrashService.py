#!/usr/bin/python
#
#   SIGVerse Client Library
#    Command-line execution utility
#
#   Copyright(C) 2014, Isao Hara, AIST
#   Release under the MIT License.
#
#   Usage:  sigrun.py -f <fname> -n <agent name> [--host <hostname>] [--port <port number>]
#
#
#

import sys
import os

import sigservice

class MyService(sigservice.SigService):
	def __init__(self, name):
		sigservice.SigService.__init__(self, name)

	def onAction(self, evt):
		return 1.0

	def onRecvMsg(self, evt):
		sender = evt.getSender()
		msg = evt.getMsg()
		msg_ar = msg.split(" ")
		print "SENDER = %s, %s" % (sender, msg)

		if msg_ar[0] == "RecognizeTrash" :
			campos=sigservice.Position([float(msg_ar[1]),float(msg_ar[2]), float(msg_ar[3])])
			camdir=sigservice.Position([float(msg_ar[1]),float(msg_ar[2]), float(msg_ar[3])])
			trashpos = self.recognizeTrash(sender, campos, camdir)
			send_text = "%f %f %f" % (trashpos.x(), trashpos.y(), trashpos.z())
			print "sendtext=", send_text
			self.sendMsgToCtrl(sender, send_text)
			pass
		return

	def recognizeTrash(self, sender, cmpos, camdir):
		if sender :
			img = self.captureView(sender)
			fovy = img.getFOVy()
			aspectRatio = img.getAspectRatio()
			buf = img.getBuffer()
                else:
			print "No Sender Name"
		return sigservice.Position([0.0, 52.0, 60.0])

if __name__ == "__main__" :

  host = sys.argv[1]
  port = int(sys.argv[2])

  print "Connect to %s:%d" % (host, port)
  serv=MyService("RecogTrash")
  serv.connect(host,port)
  serv.connectToViewer()
  serv.startLoop()

  

