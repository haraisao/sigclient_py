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
class RobotController(sig.SigController):
  def onInit(self, evt):
    self.kp = 5.0
    self.fmax = 5000000.0

    self.jmap={}
    self.jmap['WAIST_JOINT0']=0.0
    self.jmap['WAIST_JOINT1']=0.0
    self.jmap['WAIST_JOINT2']=0.0
    self.jmap['ROOT_JOINT0']=0.0
    self.jmap['ROOT_JOINT1']=0.0
    self.jmap['ROOT_JOINT2']=0.0
    self.jmap['HEAD_JOINT0']=0.0
    self.jmap['HEAD_JOINT1']=0.0
    self.jmap['HEAD_JOINT2']=0.0

    self.jmap['RLEG_JOINT2']=-0.34
    self.jmap['RLEG_JOINT4']=0.45
    self.jmap['RLEG_JOINT6']=-0.16
    self.jmap['LLEG_JOINT2']=-0.34
    self.jmap['LLEG_JOINT4']=0.45
    self.jmap['LLEG_JOINT6']=-0.16

    self.jmap['LARM_JOINT0']=0.0
    self.jmap['LARM_JOINT1']=0.0
    self.jmap['LARM_JOINT2']=0.0
    self.jmap['LARM_JOINT3']=0.0
    self.jmap['LARM_JOINT4']=0.0
    self.jmap['LARM_JOINT5']=0.0
    self.jmap['LARM_JOINT6']=0.0
    self.jmap['LARM_JOINT7']=0.0

    self.jmap['RARM_JOINT0']=0.0
    self.jmap['RARM_JOINT1']=0.0
    self.jmap['RARM_JOINT2']=0.0
    self.jmap['RARM_JOINT3']=0.0
    self.jmap['RARM_JOINT4']=0.0
    self.jmap['RARM_JOINT5']=0.0
    self.jmap['RARM_JOINT6']=0.0
    self.jmap['RARM_JOINT7']=0.0

    return

  def onAction(self, evt):
    try:
      my = self.getObj()
      allJoints = my.getAllJointAngles()
      for jname in allJoints.keys():
        currentAngle = allJoints[jname]
        targetAngle = self.jmap[jname]
        vel = self.kp * (targetAngle - currentAngle) 
        my.setJointVelocity(jname, vel, self.fmax)
    except:
      print "ERROR"
      pass

    return 0.1

  def onRecvMsg(self, evt):
    try:
      my = self.getObj()
      msg = evt.getMsg()
      if msg.find(" ") > 0 :
        pos = msg.find(" ")
        msg_j = msg[:pos]
        if msg_j.find("-") :
          msg_j = msg_j.replace("-", "_")
        msg_j = msg_j.upper()
        if msg_j in self.jmap.keys() :
          self.jmap[msg_j] = math.radians(float(msg[pos:]))
        else:
          print "No such joint:",msg_j
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
  return RobotController(name, host, port)
