#
#  SIGVerse Client Library
#   SimObj in SIGVerse
#
#   Copyright(C) 2014, Isao Hara, AIST
#   Release under the MIT License.
#

import sys
import os
import time
import types
import math
#from Quat import *
import Quat
#from sigcomm import *
import sigcomm
#from sig import *
import sig

#
#   Attribute for SimObj
#      sigcomm.SigMarshaller <--- SigObjAttribute
#
class SigObjAttribute(sigcomm.SigMarshaller):
  def __init__(self, data=''):
    sigcomm.SigMarshaller.__init__(self, data)
    self.name=''
    self.value=None
    self.valueType=None
    self.group=None

  def parse(self):
    datalen,self.name, self.group, vallen, self.valueType = self.unmarshal('HSSHH')

    if self.valueType == sigcomm.typeValue['VALUE_TYPE_BOOL']:
      self.valueType = 'VALUE_TYPE_BOOL'
      value, = self.unmarshal('H')
      if value : self.value=True
      else : self.value=False

    elif self.valueType == sigcomm.typeValue['VALUE_TYPE_DOUBLE']:
      self.valueType = 'VALUE_TYPE_DOUBLE'
      self.value, = self.unmarshal('d')

    elif self.valueType == sigcomm.typeValue['VALUE_TYPE_STRING']:
      self.valueType = 'VALUE_TYPE_STRING'
      self.value, = self.unmarshal('S')
    else:
      pass

#
#  CParts for SimObj
#      sigcomm.SigMarshaller <--- SigObjPart
#
class SigObjPart(sigcomm.SigMarshaller):
  def __init__(self, owner, data):
    sigcomm.SigMarshaller.__init__(self, data)
    self.name = ''
    self.owner = owner
    self.id=None
    self.type=None
    self.pos=[0,0,0]
    self.quaternion=[0,0,0,0]
    self.partsValue=None

  #
  #
  #
  def controller(self):
    return self.owner.controller
  
  #
  #
  #
  def parse(self):
    datalen,self.id,type,self.name = self.unmarshal('HIHS')      

    self.pos = self.unmarshal('ddd')

    rtype, = self.unmarshal('H')
    if rtype == 0:  # ROTATION_TYPE_QUATERNION
      self.quaternion = self.unmarshal('dddd')

      extlen, = self.unmarshal('H')

      if type == sigcomm.partType['PARTS_TYPE_BOX'] :
        self.type = 'PARTS_TYPE_BOX'
        self.partsValue = self.unmarshal('ddd')

      elif type == sigcomm.partType['PARTS_TYPE_CYLINDER'] :
        self.type = 'PARTS_TYPE_CYLINDER'
        self.partsValue = self.unmarshal('dd')

      elif type == sigcomm.partType['PARTS_TYPE_SPHERE'] :
        self.type = 'PARTS_TYPE_SPHERE'
        self.partsValue = self.unmarshal('d')

      else:
        self.type = 'PARTS_TYPE_UNKNOWN'
        self.partsValue = None

  #
  #
  #
  def giveSize(self) :
    return self.partsValue

  #
  #  Position
  #
  def setPos(self, x, y, z):
    self.pos=[x,y,z]
    return

  def getPos(self):
    return self.pos

  def givePosition(self) :
    return self.pos

  def pos_val(self, idx, val=None):
    if idx in (0, 1, 2):
      if type(val) in (types.IntType, types.FloatType) :
        self.pos[idx] = val
      return self.pos[idx]
    else:
      raise NameError, idx

  def x(self, val=None):
    return self.pos_val(0, val)

  def y(self, val=None):
    return self.pos_val(1, val)

  def z(self, val=None):
    return self.pos_val(2, val)

  #
  #  Rotation
  #
  def setQuaternion(self, qw, qx, qy, qz):
    self.quaternion=[qw, qx, qy, qz]
    return

  def getQuaternion(self):
    return self.quaternion

  def quaternion_val(self, idx, val=None):
    if idx in (0, 1, 2, 3):
      if type(val) in (types.IntType, types.FloatType) :
        self.quaternion[idx] = val
      return self.quaternion[idx]
    else:
      raise NameError, idx

  def qw(self, val=None):
    return self.quaternion_val(0, val)

  def qx(self, val=None):
    return self.quaternion_val(1, val)

  def qy(self, val=None):
    return self.quaternion_val(2, val)

  def qz(self, val=None):
    return self.quaternion_val(3, val)

  def graspObj(self, objname):
    msg = "%s,%s,%s," % (self.owner.getName(), self.name, objname)
    controller = self.controller()
    marshaller = self.controller().getMarshaller()
    marshaller.createMsgCommand('REQUEST_GRASP_OBJECT', msg)
    controller.sendData(marshaller.getEncodedDataCommand())


  def releaseObj(self):
    msg = "%s,%s," % (self.owner.getName(), self.name)
    controller = self.controller()
    marshaller = self.controller().getMarshaller()
    marshaller.createMsgCommand('REQUEST_RELEASE_OBJECT', msg)
    controller.sendData(marshaller.getEncodedDataCommand(), 0)

#
#  SimObj
#
class SigSimObj:
  def __init__(self, name, ctrl):
    self.cmdbuf = sigcomm.SigDataCommand()
    self.name=name
    self.parts = {}
    self.attributes = {}
    self.joints={}
    self.updateTime=0.0
    self.controller = ctrl
    self.cameraIds = None

    self.responseObj = None

  #
  # Attach SimObj 
  # 
  def getObj(self):
    self.cmdbuf.setHeader('COMM_REQUEST_GET_ENTITY', name=self.name)
    self.controller.sendCmd(self.cmdbuf.getEncodedCommand())

  #
  #  Parse attribute from simserve
  #
  def setAttributes(self, data):
    bufsize = len(data)
    attr = sigcomm.SigMarshaller(data)

    attrlen, = attr.unmarshal('H')
    offset=attr.offset

    while bufsize > offset :
      attr.offset = offset
      datalen, = attr.unmarshal('H')

      attribute = SigObjAttribute(data[offset:offset+datalen])
      attribute.parse()
      self.attributes[attribute.name] = attribute

      offset = offset+datalen 
  #
  #
  #
  def getName(self):
    return self.name

  #
  #  Parse parts info from  simserver
  #
  def setParts(self, data):
    body = sigcomm.SigMarshaller(data)
    bodylen, = body.unmarshal('H')      

    offset=body.offset
    bufsize = len(data)

    while bufsize > offset :
      body.offset = offset
      datalen, = body.unmarshal('H')      

      part = SigObjPart(self, data[offset:offset+datalen])
      part.parse()
      self.parts[part.name] = part

      offset = offset+datalen
  #
  #
  def getParts(self, name):
    try:
      return self.parts[name]
    except:
      pass
    return None
  #
  #
  #
  def isAttr(self, name):
    return name in self.attributs.keys()

  #
  #
  #
  def dynamics(self):
    try:
      return self.attributes['dynamics'].value
    except:
      return False

  def getDynamicsMode(self):
    return self.dynamics()

  def setDynamicsMode(self, val):
    self.attributes['dynamics'].value = val
    
    self.cmdbuf.setHeader('COMM_REQUEST_SET_DYNAMICS_MODE', name=self.name)
    self.cmdbuf.marshal('B', val)
    self.controller.sendCmd(self.cmdbuf.getEncodedCommand())
    return 

  def getGravityMode(self):
    self.responseObj = None
    self.cmdbuf.setHeader('COMM_REQUEST_GET_GRAVITY_MODE', name=self.name)
    self.controller.sendData(self.cmdbuf.getEncodedCommand())
    self.controller.waitForReply()
    if self.responseObj is None:
      print "ERROR in getGravityMode"
    else:
      vel = self.responseObj
    return vel

  def setGravityMode(self, val):
    self.cmdbuf.setHeader('COMM_REQUEST_SET_GRAVITY_MODE', name=self.name)
    self.cmdbuf.marshal('B', val)
    self.controller.sendCmd(self.cmdbuf.getEncodedCommand())
    return 

  def setCollisionEnable(self, flag):
    name = self.name+','
    self.cmdbuf.createMsgCommand('REQUEST_SET_COLLISIONABLE', name, ('B', flag))
    self.controller.sendData(self.cmdbuf.getEncodedCommand(), 0)
    return 

  #
  #  isGrasped
  #
  def getIsGrasped(self):
    self.responseObj = None
    name = self.name+','
    self.cmdbuf.createMsgCommand('REQUEST_GET_ISGRASPED', name)
    self.controller.sendData(self.cmdbuf.getEncodedCommand())
    self.controller.waitForReply()

    if self.responseObj is None:
      print "ERROR in getIsGrasped"

    return  self.responseObj

  #
  #  Position
  #
  def getPosition(self):
    self.updatePosition()
    self.controller.waitForReply()
    return Position(self.parts['body'].getPos())

  def setCurrentPosition(self, x, y, z):
    self.parts['body'].setPos(x, y, z)
    return 

  def setPosition(self, x, y, z):
    self.parts['body'].setPos(x, y, z)
    name = self.name+','
    self.cmdbuf.createMsgCommand('REQUEST_SET_ENTITY_POSITION', name,
                                 ('d', x), ('d', y), ('d', z))
    self.controller.sendData(self.cmdbuf.getEncodedDataCommand(), 0)
    return 

  def updatePosition(self):
    name = self.name+','
    self.cmdbuf.createMsgCommand('REQUEST_GET_ENTITY_POSITION', name)
    self.controller.sendData(self.cmdbuf.getEncodedDataCommand())
    return

  def setCurrentRotation(self, qw, qx, qy, qz):
    self.parts['body'].setQuaternion(qw, qx, qy, qz)
    return 

  def x(self, val=None):
    return self.parts['body'].x(val)

  def y(self, val=None):
    return self.parts['body'].y(val)

  def z(self, val=None):
    return self.parts['body'].z(val)

  #
  #  Rotation
  #
  def getRotation(self):
    self.updateRotation()
    self.controller.waitForReply()
    return Rotation(self.parts['body'].getQuaternion())

  def setRotation(self, qw, qx, qy, qz, abs=1):
    self.parts['body'].setQuaternion(qw, qx, qy, qz)
    name = self.name+','
    self.cmdbuf.createMsgCommand('REQUEST_SET_ENTITY_ROTATION', name,
                                 ('H', abs), ('d', qw), ('d', qx), ('d', qy), ('d', qz))

    self.controller.sendData(self.cmdbuf.getEncodedDataCommand(), 0)
    return 

  def setAxisAndAngle(self, x, y, z, ang, dir=1):
    if self.dynamics() :
      return

    if dir :
      quat = Quat.Quat(x, y, z, ang)
    else:
      quat1 = Quat.Quat(x, y, z, ang)
      quat = self.getRotation().rot * quat1
       
    self.setRotation(quat.w, quat.x, quat.y, quat.z)

    return

  def updateRotation(self):
    name = self.name+','
    self.cmdbuf.createMsgCommand('REQUEST_GET_ENTITY_ROTATION', name)
    self.controller.sendData(self.cmdbuf.getEncodedDataCommand())
    return

  def qw(self, val=None):
    return self.parts['body'].qw(val)

  def qx(self, val=None):
    return self.parts['body'].qx(val)

  def qy(self, val=None):
    return self.parts['body'].qy(val)

  def qz(self, val=None):
    return self.parts['body'].qz(val)

  #
  #  Force/Accel/Torque
  #
  def setForce(self, fx, fy, fz):
    if self.dynamics() :
      self.attributes['fx'].value=fx
      self.attributes['fy'].value=fy
      self.attributes['fz'].value=fz
    else:
      print "setForce : dynamics is off..."
    return 

  def addForce(self, dfx, dfy, dfz):
    self.cmdbuf.setHeader('COMM_REQUEST_ADD_FORCE', name=self.name)
    self.cmdbuf.marshal('dddB', dfx, dfy, dfz, 0)
    self.controller.sendCmd(self.cmdbuf.getEncodedCommand())
    return 

  def addRelForce(self, dfx, dfy, dfz):
    self.cmdbuf.setHeader('COMM_REQUEST_ADD_FORCE', name=self.name)
    self.cmdbuf.marshal('dddB', dfx, dfy, dfz, 1)
    self.controller.sendCmd(self.cmdbuf.getEncodedCommand())
    return 

  def addForceAtPos(self, fx, fy, fz, px, py, pz):
    self.cmdbuf.setHeader('COMM_REQUEST_ADD_FORCE_ATPOS', name=self.name)
    self.cmdbuf.marshal('ddddddBB', fx, fy, fz, px, py, pz, 0, 0)
    self.controller.sendCmd(self.cmdbuf.getEncodedCommand())
    return 

  def addForceAtRelPos(self, fx, fy, fz, px, py, pz):
    self.cmdbuf.setHeader('COMM_REQUEST_ADD_FORCE_ATPOS', name=self.name)
    self.cmdbuf.marshal('ddddddBB', fx, fy, fz, px, py, pz, 1, 0)
    self.controller.sendCmd(self.cmdbuf.getEncodedCommand())
    return 

  def addRelForceAtPos(self, fx, fy, fz, px, py, pz):
    self.cmdbuf.setHeader('COMM_REQUEST_ADD_FORCE_ATPOS', name=self.name)
    self.cmdbuf.marshal('ddddddBB', fx, fy, fz, px, py, pz, 0, 1)
    self.controller.sendCmd(self.cmdbuf.getEncodedCommand())
    return 

  def addRelForceAtRelPos(self, fx, fy, fz, px, py, pz):
    self.cmdbuf.setHeader('COMM_REQUEST_ADD_FORCE_ATPOS', name=self.name)
    self.cmdbuf.marshal('ddddddBB', fx, fy, fz, px, py, pz, 1, 1)
    self.controller.sendCmd(self.cmdbuf.getEncodedCommand())
    return 

  def getMass(self):
    return self.attributes['mass'].value

  def setMass(self, val):
    self.attributes['mass'].value = val
    return

  def setAccel(self, ax, ay, az):
    mass = getMass()
    setForce(mass * ax, mass * ay, mass * az)
    return 

  def setTorque(self, x, y, z):
    if self.dynamics() :
      self.attributes['tqx'].value=x
      self.attributes['tqy'].value=y
      self.attributes['tqz'].value=z
    else:
      print "setTorque : dynamics is off..."
    return 
  #
  #
  #
  def getPartsPosition(self, part_name):
    self.responseObj = None
    msg = "%s,%s," %( self.name, joint_name)
    self.cmdbuf.createMsgCommand('REQUEST_GET_PARTS_POSITION', msg)
    self.controller.sendData(self.cmdbuf.getEncodedCommand())
    self.controller.waitForReply()

    if self.responseObj is None:
      print "ERROR in getJointAngle"
    return  self.responseObj

  def getPointingVector(self, joint1, joint2):
    self.responseObj = None
    msg = "%s,%s,%s," %( self.name, joint1, joint2)
    self.cmdbuf.createMsgCommand('REQUEST_GET_POINTING_VECTOR', msg)
    self.controller.sendData(self.cmdbuf.getEncodedCommand())
    self.controller.waitForReply()

    if self.responseObj is None:
      print "ERROR in getJointAngle"
    return  self.responseObj

  def getPointingVectorWithArm(self, lrFlag):
    if lrFlag == 0:
      return getPointingVector("LARM_JOINT4", "LARM_JOINT7")
    else:
      return getPointingVector("RARM_JOINT4", "RARM_JOINT7")
  
  
  def getPointedObject(self, speakerName, lrFlag, lineID, typicalType):
    if not speakerName:
      print "ERROR in getPointedObject, no speakerName" 
    elif not lrFlag in (0 ,1) :
      print "ERROR in getPointedObject, invalid lrFlag" 
    elif not lineID in (1 ,2) :
      print "ERROR in getPointedObject, invalid lineID" 
    elif not typicalType in (0 ,1, 2) :
      print "ERROR in getPointedObject, invalid typicalType" 
    else:
      if lrFlag == 0:
        if lineID == 1:
          partName0 = "LEYE_LINK"
        elif lineID == 2:
          partName0 = "LARM_LINK4"
        else:
          pass
        partName1 = "LARM_LINK7"
      elif lrFlag == 1:
        if lineID == 1:
          partName0 = "REYE_LINK"
        elif lineID == 2:
          partName0 = "RARM_LINK4"
        else:
          pass
        partName1 = "RARM_LINK7"
      else:
        pass

       self.cmdbuf.setHeader('COMM_REQUEST_GET_POINTED_OBJECT', name=self.name)
       self.cmdbuf.marshal('SSS', partName0, partName1, "%d" % typicalType)
       self.controller.sendData(self.cmdbuf.getEncodedCommand())

    return None

  #
  # Joint...
  #    Ummm... Which is the newer version?
  #  
  def setJointAngle(self, joint_name, angle):
    self.cmdbuf.setHeader('COMM_REQUEST_SET_JOINT_ANGLE', name=self.name)
    self.cmdbuf.marshal('SdB', joint_name, angle, 0)
    self.controller.sendCmd(self.cmdbuf.getEncodedCommand())
    return 

  def getJointAngle(self, joint_name):
    self.responseObj = None
    msg = "%s,%s," %( self.name, joint_name)
    self.cmdbuf.createMsgCommand('REQUEST_GET_JOINT_ANGLE', msg)
    self.controller.sendData(self.cmdbuf.getEncodedCommand())
    self.controller.waitForReply()

    if self.responseObj is None:
      print "ERROR in getJointAngle"
    return  self.responseObj

  def getJointPosition(self, joint_name):
    self.responseObj = None
    msg = "%s,%s," %( self.name, joint_name)
    self.cmdbuf.createMsgCommand('REQUEST_GET_JOINT_POSITION', msg)
    self.controller.sendData(self.cmdbuf.getEncodedCommand())
    self.controller.waitForReply()

    if self.responseObj is None:
      print "ERROR in getJointPosition"
    return  self.responseObj

  def setJointQuaternion(self, joint_name, qw, qx, qy, qz, offset=0):
    msg = self.name + ',' + joint_name + ','
    if offset :
      msg += '1,'
    else:
      msg += '0,'

    self.cmdbuf.createMsgCommand('REQUEST_SET_JOINT_QUATERNION', msg,
                                 ('d', qw), ('d', qx), ('d', qy), ('d', qz))
    self.controller.sendData(self.cmdbuf.getEncodedDataCommand(), 0)
    return 

  def addJointTorque(self, joint_name, torque):
    if self.dynamics() :
      self.cmdbuf.setHeader('COMM_REQUEST_ADD_JOINT_TORQUE', name=self.name)
      self.cmdbuf.marshal('Sd', joint_name, torque)
      self.controller.sendCmd(self.cmdbuf.getEncodedCommand())
    else:
      print "addJointTorque : dynamics is off..."
    return

  def getJointForce(self, joint_name):
    if self.dynamics() :
      self.responseObj = None
      self.cmdbuf.setHeader('COMM_REQUEST_GET_JOINT_FORCE', name=self.name)
      self.cmdbuf.marshal('S', joint_name)
      self.controller.sendData(self.cmdbuf.getEncodedCommand())
      if self.responseObj is None:
        print "ERROR in getJointPosition"
      return  self.responseObj


    else:
      print "getJointForce : dynamics is off..."
    return

  def setJointVelocity(self, joint_name, vel, mx):
    self.setAngularVelocityToJoint(joint_name, vel, mx)
    return

  def setAngularVelocityToJoint(self, joint_name, vel, mx):
    msg = "%s,%s," % (self.name, joint_name)
    self.cmdbuf.createMsgCommand('REQUEST_SET_JOINT_VELOCITY', msg, ('d', vel), ('d', mx))
    self.controller.sendData(self.cmdbuf.getEncodedDataCommand(), 0)
    return

  def setAngularVelocityToParts(self, name, vel, maxf) :
    self.cmdbuf.setHeader('COMM_REQUEST_SET_ANGULAR_VELOCITY_PARTS', name=self.name)
    self.cmdbuf.marshal('Sdd', name, vel, maxf)
    self.controller.sendCmd(self.cmdbuf.getEncodedCommand())
    return 

  def setAngularVelocity(self, x, y, z) :
    if self.dynamics() :
      self.attributs['avx'].value = x
      self.attributs['avy'].value = x
      self.attributs['avz'].value = x
    return

  def getAngularVelocity(self) :
    vel=[0,0,0]

    self.responseObj = None
    self.cmdbuf.setHeader('COMM_REQUEST_GET_ANGULAR_VELOCITY', name=self.name)
    self.controller.sendData(self.cmdbuf.getEncodedCommand())
    self.controller.waitForReply()
    if self.responseObj is None:
      print "ERROR in getAngularVelocity"
    else:
      vel = self.responseObj
    return vel
  #
  #
  #
  def getAllJointAngles(self):
    msg = "%s," % (self.name)
    self.cmdbuf.createMsgCommand('REQUEST_GET_ALL_JOINT_ANGLES', msg)
    self.controller.sendData(self.cmdbuf.getEncodedDataCommand())

    self.controller.waitForReply()

    return self.joints

  #
  #
  #
  def getLinearVelocity(self) :
    vel=[0,0,0]
    self.responseObj = None
    self.cmdbuf.setHeader('COMM_REQUEST_GET_LINEAR_VELOCITY', name=self.name)
    self.controller.sendData(self.cmdbuf.getEncodedCommand())
    self.controller.waitForReply()
    if self.responseObj is None:
      print "ERROR in getLinearVelocity"
    else:
      vel = self.responseObj
    return vel

  def setLinearVelocity(self, x, y, z) :
    self.cmdbuf.setHeader('COMM_REQUEST_SET_LINEAR_VELOCITY', name=self.name
                    ('d', x), ('d', y), ('d', z))
    self.controller.sendData(self.cmdbuf.getEncodedCommand(), 0)

  #
  # Camera...
  #
  def getCameraIDs(self):
    if  self.cameraIds is None:
      self.cameraIds = []
      for x in  self.attributes.keys():
        if x.find("elnk") == 0:
          self.cameraIds.append(int(x[4:]))
      self.cameraIds.sort()
    else:
      pass

    return self.cameraIds 

  def getCameraNum(self):
    return len(self.getCameraIDs())

  def getCamDir(self, camID=1, requestToServer=True):
    val = None
    if requestToServer:
      self.responseObj = None
      msg = self.name+','
      self.cmdbuf.createMsgCommand('REQUEST_GET_CAMERA_DIRECTION', msg, ('H', camID))
      self.controller.sendData(self.cmdbuf.getEncodedDataCommand())
      self.controller.waitForReply()
      if self.responseObj is None:
        print "ERROR in getCamDir"
      else:
        val = self.responseObj
    else:
      if self.checkCameraID(camID):
        val= [self.attributes["evx%d" % camID].value,
              self.attributes["evy%d" % camID].value,
              self.attributes["evz%d" % camID].value]

      else:
        print "No such a camera ID=%d" % camID
    return val

  def setCamDir(self, pos, camID=1):
    if  self.checkCameraID(camID):
      self.attributes["evx%d" % camID].value = pos[0]
      self.attributes["evy%d" % camID].value = pos[1]
      self.attributes["evz%d" % camID].value = pos[2]

      msg = self.name+','
      self.cmdbuf.createMsgCommand('REQUEST_SET_CAMERA_DIRECTION', msg, ('H', camID),
                                ('d', pos[0]), ('d', pos[1]), ('d', pos[2]))
      self.controller.sendData(self.cmdbuf.getEncodedDataCommand(), 0)
    else:
      print "No such a camera, id = %d" % camID
    return

  def getCamPos(self, camID=1, requestToServer=True):
    val = None
    if requestToServer:
      self.responseObj = None
      msg = self.name+','
      self.cmdbuf.createMsgCommand('REQUEST_GET_CAMERA_POSITION', msg, ('H', camID))
      self.controller.sendData(self.cmdbuf.getEncodedDataCommand())
      self.controller.waitForReply()
      if self.responseObj is None:
        print "ERROR in getCamDir"
      else:
        val = self.responseObj
    else:
      if self.checkCameraID(camID):
        val= [self.attributes["epx%d" % camID].value,
              self.attributes["epy%d" % camID].value,
              self.attributes["epz%d" % camID].value]
      else:
        print "No such a camera ID=%d" % camID
    return val

  def setCamPos(self, pos, camID=1):
    if  self.checkCameraID(camID):
      self.attributes["epx%d" % camID].value = pos[0]
      self.attributes["epy%d" % camID].value = pos[1]
      self.attributes["epz%d" % camID].value = pos[2]

      msg = self.name+','
      self.cmdbuf.createMsgCommand('REQUEST_SET_CAMERA_POSITION', msg, ('H', camID),
                                ('d', pos[0]), ('d', pos[1]), ('d', pos[2]))
      self.controller.sendData(self.cmdbuf.getEncodedDataCommand(), 0)

    else:
      print "No such a camera, id = %d" % camID
    return

  def getCameraViewPoint(self, camID=1):
    if  self.checkCameraID(camID):
      if getCameraNum() == 1 and camID == 1:
        return [self.attributes["vpx"].value,
                self.attributes["vpy"].value,
                self.attributes["vpz"].value]
      else:
        return [self.attributes["epx%d" % camID].value,
                self.attributes["epy%d" % camID].value,
                self.attributes["epz%d" % camID].value]
    else:
      print "No such a camera, id = %d" % camID
      return None

  def setCameraViewPoint(self, vec, camID=1):
    if  self.checkCameraID(camID):
      if getCameraNum() == 1 and camID == 1:
        self.attributes["vpx"].value = vec[0]
        self.attributes["vpy"].value = vec[1]
        self.attributes["vpz"].value = vrc[2]
      else:
        self.attributes["epx%d" % camID].value = vec[0]
        self.attributes["epy%d" % camID].value = vec[1]
        self.attributes["epz%d" % camID].value = vrc[2]
    else:
      print "No such a camera, id = %d" % camID
    return

  def getCameraLinkName(self, camID=1):
    if checkCameraID(self, camID):
      if getCameraNum() == 1 and camID == 1:
        return "body"
      else:
        return self.getCameraAttr("elnk" ,camID)
    else:
      print "No such a camera, id = %d" % camID
    return None

  def getCamLink(self, camID=1):
    return self.getCameraAttr("elnk" ,camID)

  def setCamLink(self, lnk, camID=1):
    return self.setCameraAttr("elnk" ,camID, lnk)

  def checkCameraID(self, camID):
    if  self.cameraIds is None:
      self.getCameraIDs()
    return  camID in self.cameraIds

  def getCameraAttr(self, fmt, camID):
    if self.checkCameraID (camID):
      return self.attributes["%s%d" % (fmt,camID)].value
    else:
      print "No such a camera, id = %d" % camID
      return None

  def setCameraAttr(self, fmt, camID, val):
    if self.checkCameraID(camID):
      self.attributes["%s%d" % (fmt,camID)].value = val
      return True
    else:
      print "No such a camera, id = %d" % camID
    return False

  def getCamQuaternion(camID=1):
    if self.checkCameraID(camID):
      return [self.attributes["quw%d" % camID].value,
              self.attributes["qux%d" % camID].value,
              self.attributes["quy%d" % camID].value,
              self.attributes["quz%d" % camID].value]

    else:
      print "No such a camera, id = %d" % camID
    return 
    
  def getCameraViewVector(camID=1):
    if self.checkCameraID(camID):
      if getCameraNum() == 1 and camID == 1:
        return [self.attributes["vvx"].value,
                self.attributes["vvx"].value,
                self.attributes["vvx"].value]
      else:
        return [self.attributes["evx%d" % camID].value,
                self.attributes["evy%d" % camID].value,
                self.attributes["evz%d" % camID].value]
    else:
      print "No such a camera, id = %d" % camID
    return 

  def setCameraViewVector(vec, camID=1):
    if checkCameraID(self, camID):
      if getCameraNum() == 1 and camID == 1:
        self.attributes["vvx"].value = vec[0]
        self.attributes["vvy"].value = vec[1]
        self.attributes["vvz"].value = vec[2]
      else:
        self.attributes["evx%d" % camID].value = vec[0]
        self.attributes["evy%d" % camID].value = vec[1]
        self.attributes["evz%d" % camID].value = vrc[2]
    else:
      print "No such a camera, id = %d" % camID
    return
    
  def getCamFOV(self, camID=1):
    return self.getCameraAttr("FOV" ,camID)

  def setCamFOV(self, fov, camID=1):
    if self.setCameraAttr("FOV" ,camID, fov) :
      msg = self.name+','
      self.cmdbuf.createMsgCommand('REQUEST_SET_CAMERA_FOV', msg, ('H', camID), ('d', fov))
      self.controller.sendData(self.cmdbuf.getEncodedDataCommand(), 0)
    return

  def getCamAS(self, camID=1):
    return self.getCameraAttr("aspectRatio" ,camID)

  def setCamAS(self, val, camID=1):
    if self.setCameraAttr("aspectRatio" ,camID, val) :
      msg = self.name+','
      self.cmdbuf.createMsgCommand('REQUEST_SET_CAMERA_ASPECTRATIO', msg, ('H', camID), ('d', fov))
      self.controller.sendData(self.cmdbuf.getEncodedDataCommand(), 0)

    return 
#
#
#
class Position:
  def __init__(self, *args):
    if len(args) == 3:
      pos = args
    elif len(args) == 1:
      pos = args[0]
    else:
      pos = (0,0,0)
   
    self._x=pos[0]
    self._y=pos[1]
    self._z=pos[2]

  def x(self, val=None):
    if not val is None:
      self._x=val
    return self._x

  def y(self, val=None):
    if not val is None:
      self._y=val
    return self._y

  def z(self, val=None):
    if not val is None:
      self._z=val
    return self._z
#
#
#
class Rotation:
  def __init__(self, *args):
    if len(args) == 4:
      rot = args
    elif len(args) == 1:
      rot = args[0]
    else:
      rot = (0,0,0,0)
   
    self._qw=rot[0]
    self._qx=rot[1]
    self._qy=rot[2]
    self._qz=rot[3]

  def qw(self, val=None):
    if not val is None:
      self._qw=val
    return self._qw

  def qx(self, val=None):
    if not val is None:
      self._qx=val
    return self._qx

  def qy(self, val=None):
    if not val is None:
      self._qy=val
    return self._qy

  def qz(self, val=None):
    if not val is None:
      self._qz=val
    return self._qz

