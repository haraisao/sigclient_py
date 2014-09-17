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
    self.grasp_obj=None
    self.Colli=False

    self.grasp_parts="RARM_LINK7"
    return

  def onAction(self, evt):
    return 10.0 

  def onRecvMsg(self, evt):
    try:
     if evt is None:
        print "evt is None"
        return

     my = self.getObj()
     msg = evt.getMsg()

     if msg.find(" ") > 0 :
       pos = msg.find(" ")
       msg_j = msg[:pos]
       if msg_j.find("-") :
         msg_j = msg_j.replace("-", "_") 
         
       angle = float(msg[pos:])
       my.setJointAngle(msg_j.upper(), math.radians(angle))
       pass

     elif msg == "rotation" :
       dy = 45.
       rot = my.getRotation() 

       print rot
       theta = 2.0 * math.asin(rot.qy())
       y = theta + math.radians(dy)

       if y >= math.pi :
         y = y - 2*math.pi

       my.setAxisAndAngle(0, 1.0, 0, y)

     elif msg == "move" :
       my = self.getObj()

       pos = my.getPosition()
       rot = my.getRotation() 

       theta = 2.0 * math.asin(rot.qy())
       dx = 0.0
       dz = 0.0
       vel = 10

       dx = math.sin(theta) * vel
       dz = math.cos(theta) * vel

       my.setPosition(pos.x() + dx, pos.y(), pos.z() + dz)

     elif msg == "release" :
       parts = my.getParts(self.grasp_parts)
       parts.releaseObj()

     elif msg == "reset" :
       self.Colli = False

     else:
       pass

    except:
      print "ERROR in onRecvMsg"
      pass

    return

  def onCollision(self, evt):

    if self.Colli is False:
      with_obj = evt.getWith()
      mparts = evt.getMyParts()

      for i in range(len(with_obj)):
       if mparts[i] in ("RARM_LINK7", "RARM_LINK4") :
         my = self.getObj()
         parts = my.getParts(self.grasp_parts)
         parts.graspObj(with_obj[i])
         print "Grasp Object[%s]" % with_obj[i]
         self.Colli = True
    else:
      pass

    return

#
#  
#
def createController(name, host, port):
  return RobotController(name, host, port)
