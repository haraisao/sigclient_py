#
#  Sample Controlller for SIGVerse
#

import sys
import os
import time
import sig
import random
import math

#
#  Sample controller for SIGVerse
#
class RobotController(sig.SigController):
  def onInit(self, evt):
    self.my = self.getObj()
    self.initpos = self.my.getPosition()
    self.radius = 10.0
    self.distance = 10.0
    self.my.setWheel(self.radius, self.distance)

    self.trashes=['can_0', 'can_1', 'petbottle_0']
    self.vel = 0.3
    self.jvel = 0.6
    self.state = 0
    self.tname = None
    self.tpos = None

    self.grasp = False
    self.recogSrv = None
    self.sended = False
    return

  def onAction(self, evt):
#    try:
      if self.state == 0 :
        if self.recogSrv == None :
          if self.checkService("RecogTrash") :
            self.recogSrv = self.connectToService("RecogTrash")
        else:
          if self.recogSrv and self.sended == False:
            lnk = self.my.getCameraLinkName()
            lpos = self.my.getParts(lnk).getPosition()
            cpos = sig.Position(self.my.getCamPos())

            campos = sig.Position(lpos[0]+cpos.x(), lpos[1]+cpos.y(), lpos[2]+cpos.z())
            cdir = sig.Position(self.my.getCamDir())
            msg = "RecognizeTrash %f %f %f %f %f %f" % (campos.x(), campos.y(),
                   campos.z(), cdir.x(), cdir.y(), cdir.z())
            self.recogSrv.sendMsgToSrv(msg)
            self.sended=True

      elif self.state == 1:
          self.time = self.rotateTowardObj(self.tpos, self.vel, evt.time())
          self.state = 2
   
      elif self.state == 2:     
        if evt.time() > self.time :
          self.my.setWheelVelocity(0.0, 0.0)
          self.my.setJointVelocity("RARM_JOINT1", -self.jvel, 0.0)
          self.time = math.radians(50) / self.jvel + evt.time()
          self.state = 3
        
      elif self.state == 3:     
        if evt.time() > self.time :
          self.my.setJointVelocity("RARM_JOINT1", 0, 0)

          if self.grasp :
            trashBox = self.getObj("trashbox_1")
            pos = trashBox.getPosition()
            self.time = self.rotateTowardObj(pos, self.vel, evt.time())
            self.state = 4
          else:
            self.broadcastMsgToSrv("I cannot grasp trash")

      elif self.state == 4:     
        if evt.time() > self.time :
          trashBox = self.getObj("trashbox_1")
          pos = trashBox.getPosition()
     
          self.time = self.goToObj(pos, self.vel * 4, 40.0, evt.time())
          self.state = 5

        pass
      elif self.state == 5:     
        if evt.time() > self.time :
          self.my.setWheelVelocity(0, 0)
          part = self.my.getParts("RARM_LINK7")
          part.releaseObj()

          time.sleep(1)

          self.grasp = False
  
#          self.trashes.remove(self.tname)
          self.my.setJointVelocity("RARM_JOINT1", self.jvel, 0)
          self.time = math.radians(50)/self.jvel +  evt.time() + 1.0
          self.state = 6

      elif self.state == 6:     
        if evt.time() > self.time :
          self.my.setJointVelocity("RARM_JOINT1", 0, 0)
          self.time = self.rotateTowardObj(self.initpos, self.vel, evt.time())
          self.state = 7

      elif self.state == 7:     
        if evt.time() > self.time :
          self.my.setWheelVelocity(0, 0)
          self.time  = self.goToObj(self.initpos, self.vel * 4, 5.0, evt.time())
          self.state = 8

      elif self.state == 8:     
        if evt.time() > self.time :
          self.my.setWheelVelocity(0, 0)
          self.time = self.rotateTowardObj(sig.Position([0,0,1000]), self.vel, evt.time())
          self.state = 9

      elif self.state == 9:     
        if evt.time() > self.time :
          self.my.setWheelVelocity(0, 0)
          self.state = 0
          self.sended = False

      else:
        pass

#    except:
#      print "ERROR in onAction"

      return 0.1 

  def onRecvMsg(self, evt):
    sender = evt.getSender()
    if sender == "RecogTrash" :
      msg = evt.getMsg()
      pos_str = msg.split(" ")
      x =  float(pos_str[0])
      y =  float(pos_str[1])
      z =  float(pos_str[2])
      self.tpos=sig.Position(x, y, z)
      self.state =  1
    return

  def onCollision(self, evt):
    if self.grasp == False:
      with_obj = evt.getWith()
      mparts = evt.getMyParts()

      for i in range(len(with_obj)):
        if mparts[i] == "RARM_LINK7" :
          parts = self.my.getParts("RARM_LINK7")
          parts.graspObj(with_obj[i])
          self.grasp = True
    return

  def rotateTowardObj(self, pos, velocity, now):
    myPos = self.my.getPosition()
    pos -= myPos
    pos.y(0)

    myRot = self.my.getRotation()
    qw = myRot.qw() 
    qy = myRot.qy() 
    theta = 2.0* math.acos(math.fabs(qw))

    if qw * qy < 0:
      theta = -theta
    
    tmp = pos.angle([0.0, 0.0, 1.0])

    targetAngle = math.acos(tmp)
    if pos.x() > 0:
      targetAngle = -targetAngle
    targetAngle += theta

    if targetAngle == 0:
      return 0.0
    else:
      distance = self.distance * math.fabs(targetAngle) * 0.5
      vel = self.radius * velocity
      tm = distance / vel
      if targetAngle > 0 :
        self.my.setWheelVelocity(velocity, -velocity)
      else:
        self.my.setWheelVelocity(-velocity, velocity)
  
      return now + tm

  def goToObj(self, pos, velocity, range, now):
    myPos = self.my.getPosition()
    pos -= myPos
    pos.y(0)
    distance = pos.length() - range
    vel = self.radius * velocity
    self.my.setWheelVelocity(velocity, velocity)

    tm = distance / vel

    return now + tm


#
#  
#
def createController(name, host, port):
  return RobotController(name, host, port)
