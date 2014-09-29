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
    return

  def onAction(self, evt):
    try:
      if self.state == 0 :
        res = self.recognizeTrash()
        if res is None:
          self.broadcastMsgToSrv("I cann't find trash")
          self.state = 8
        else:
          self.tname, self.tpos = res
          self.time = self.rotateTowardObj(self.tpos, self.vel, evt.time())
          self.state = 1

      elif self.state == 1:     
        if evt.time() > self.time :
          self.my.setWheelVelocity(0.0, 0.0)
          self.my.setJointVelocity("RARM_JOINT1", -self.jvel, 0.0)
          self.time = math.radians(50) / self.jvel + evt.time()
          self.state = 2
        pass
      elif self.state == 2:     
        if evt.time() > self.time :
          self.my.setJointVelocity("RARM_JOINT1", 0, 0)
          part = self.my.getParts("RARM_LINK7")
          part.graspObj(self.tname)

          trashBox = self.getObj("trashbox_1")
          pos = trashBox.getPosition()

          self.time = self.rotateTowardObj(pos, self.vel, evt.time())
          self.state = 3
        pass

      elif self.state == 3:     
        if evt.time() > self.time :
          trashBox = self.getObj("trashbox_1")
          pos = trashBox.getPosition()
     
          self.time = self.goToObj(pos, self.vel * 4, 40.0, evt.time())
          self.state = 4

        pass
      elif self.state == 4:     
        if evt.time() > self.time :
          self.my.setWheelVelocity(0, 0)
          self.my.setJointVelocity("RARM_JOINT1", 0, 0)
          part = self.my.getParts("RARM_LINK7")
          part.releaseObj()

          time.sleep(1)
  
          self.trashes.remove(self.tname)
          self.my.setJointVelocity("RARM_JOINT1", self.jvel, 0)
          self.time = math.radians(50)/self.jvel +  evt.time() + 1.0
          self.state = 5
        pass
      elif self.state == 5:     
        if evt.time() > self.time :
          self.my.setJointVelocity("RARM_JOINT1", 0, 0)
          self.time = self.rotateTowardObj(self.initpos, self.vel, evt.time())
          self.state = 6
        pass
      elif self.state == 6:     
        if evt.time() > self.time :
          self.my.setWheelVelocity(0, 0)
          self.time  = self.goToObj(self.initpos, self.vel * 4, 5.0, evt.time())
          self.state = 7
        pass
      elif self.state == 7:     
        if evt.time() > self.time :
          self.my.setWheelVelocity(0, 0)
          self.time = self.rotateTowardObj(sig.simobj.Position([0,0,1000]), self.vel, evt.time())
          self.state = 0

        pass
      elif self.state == 8:     
        if evt.time() > self.time :
          self.my.setWheelVelocity(0, 0)
          self.state = 0
        pass
      else:
        pass

    except:
      print "ERROR in onAction"

    return 0.1 

  def onRecvMsg(self, evt):
    return

  def onCollision(self, evt):
    return

  def recognizeTrash(self):
    if len(self.trashes) == 0:
      return None
    idx = int(random.random() * len(self.trashes)) 
    name = self.trashes[idx]
    obj = self.getObj(name)
    return [name, obj.getPosition()]

  def rotateTowardObj(self, pos, velocity, now):
    myPos = self.my.getPosition()
    pos = sig.simobj.Position(pos - myPos)
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
    pos = sig.simobj.Position(pos - myPos)
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
