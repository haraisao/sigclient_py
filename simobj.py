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
      self.value = self.unmarshal('H')
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

  def givePosision(self) :
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
  def dynamics(self):
    try:
      return self.attributes['dynamics'].value
    except:
      return False

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

  def setAxisAndAngle(self, x, y, z, ang):
    quat = Quat.Quat(x, y, z, ang)
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
    self.cmdbuf.createCommand()
    self.cmdbuf.setHeader('COMM_REQUEST_ADD_FORCE', name=self.name)
    self.cmdbuf.marshal('dddB', dfx, dfy, dfz, 0)
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
  # Joint...
  #    Ummm... Which is the newer version?
  #  
  def setJointAngle(self, joint_name, angle):
    self.cmdbuf.createCommand()
    self.cmdbuf.setHeader('COMM_REQUEST_SET_JOINT_ANGLE', name=self.name)
    self.cmdbuf.marshal('SdB', joint_name, angle, 0)
    self.controller.sendCmd(self.cmdbuf.getEncodedCommand())
    return 

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
      self.cmdbuf.createCommand()
      self.cmdbuf.setHeader('COMM_REQUEST_ADD_JOINT_TORQUE', name=self.name)
      self.cmdbuf.marshal('Sd', joint_name, torque)
      self.controller.sendCmd(self.cmdbuf.getEncodedCommand())
    else:
      print "addJointTorque : dynamics is off..."
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
    self.cmdbuf.createCommand()
    self.cmdbuf.setHeader('COMM_REQUEST_SET_ANGULAR_VELOCITY_PARTS', name=self.name)
    self.cmdbuf.marshal('Sdd', name, vel, maxf)
    self.controller.sendCmd(self.cmdbuf.getEncodedCommand())

    return 
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
  # Wheel...
  #
  def setWheelProperty(self, lname, lconsumption, lmax, lunit, lnoise, lres, lmaxf, 
                             rname, rconsumption, rmax, runit, rnoise, rres, rmaxf) :

    self.setSimObjWheelProperty(self.name, lname, lconsumption, lmax, lunit, lnoise, lres, lmaxf, 
                             rname, rconsumption, rmax, runit, rnoise, rres, rmaxf)

    return

  def setSimObjWheelProperty(self, objname, lname, lconsumption, lmax, lunit, lnoise, lres, lmaxf, 
                             rname, rconsumption, rmax, runit, rnoise, rres, rmaxf) :

    my = self.getObj(objname)
    dyn_ctrl = DynamicsConttoller()
    self.dynamicsData[objname] = dyn_ctrl
    dyn_ctrl.setWheelProperty(my.getName, lname, lconsumption, lmax, lunit, lnoise, lres, lmaxf, 
                             rname, rconsumption, rmax, runit, rnoise, rres, rmaxf)
    return 

  def differentialWheelSetSpeed(self, lvel, rvel):
    self.differentialSimObjWheelSetSpeed(self.name, lvel, rvel)
    return

  def differentialSimObjWheelSetSpeed(self, name, lvel, rvel):
    my = self.getObj(name)
    dyn_ctrl = self.dynamicsData[name]
    dyn_ctrl.differentialWheelSetSpeed(name, lvel, rvel)
    return
#
#
#
class DynamicsConttoller:
  def __init__(self):
    self.leftWheelName          = None
    self.leftMotorConsumption   = 0.0
    self.leftWheelRadius        = 0.0
    self.leftWheelMaxSpeed      = 0.0
    self.leftWheelSpeedUnit     = 0.0
    self.leftSlipNoise          = 0.0
    self.leftEncoderNoise       = 0.0
    self.leftEncoderResolution  = 0.0
    self.leftMaxForce           = 0.0
    self.rightWheelName         = None
    self.rightMotorConsumption  = 0.0
    self.rightWheelRadius       = 0.0
    self.rightWheelMaxSpeed     = 0.0
    self.rightWheelSpeedUnit    = 0.0
    self.rightSlipNoise         = 0.0
    self.rightEncoderNoise      = 0.0
    self.rightEncoderResolution = 0.0
    self.rightMaxForce          = 0.0
    self.axleLength             = 0.0

    self.currentLeftWheelSpeed  = 0.0
    self.currentRightWheelSpeed = 0.0

    self.Accueacy  = 0.00000001
    return

  def setWheelProperty(self, objname, lname, lconsumption, lmax, lunit, lnoise, lres, lmaxf, 
                             rname, rconsumption, rmax, runit, rnoise, rres, rmaxf) :
    self.leftWheelName          = lname
    self.leftMotorConsumption   = lconsumption
    self.leftWheelMaxSpeed      = lmax
    self.leftWheelSpeedUnit     = lunit
    self.leftSlipNoise          = lnoise
    self.leftEncoderResolution  = lres
    self.leftMaxForce           = lmaxf
    self.rightWheelName         = rname
    self.rightMotorConsumption  = rconsumption
    self.rightWheelMaxSpeed     = rmax
    self.rightWheelSpeedUnit    = runit
    self.rightSlipNoise         = rnoise
    self.rightEncoderResolution = rres
    self.rightMaxForce          = rmaxf

    if lname and rname:
      pLeft = objname.getParts(lname)
      lx, ly, lz = pLeft.givePosition()
      pRight = objname.getParts(rname)
      rx, ry, rz = pRight.givePosition()

      self.axleLength = math.sqrt((rx * rx) + (ry * ry) + (rz * rz))

    self.getLeftWheelRadius(objname)
    return
  #
  #
  #
  def differentialWheelSetSpeed(self, obj, left, right):
    if self.leftWheelMaxSpeed < left :
      left = self.leftWheelMaxSpeed
    elif left < -self.leftWheelMaxSpeed :
      left = -self.leftWheelMaxSpeed

    if self.leftWheelSpeedUnit > self.Accueacy :
      radiuse = math.fmod(math.fabs(left), self.leftWheelSpeedUnit)
      if  left > 0:
        left -= radiuse
      else:
        left += radiuse
      
    if self.rightWheelMaxSpeed < left :
      left = self.rightWheelMaxSpeed
    elif left < -self.rightWheelMaxSpeed :
      left = -self.rightWheelMaxSpeed

    if self.rightWheelSpeedUnit > self.Accueacy :
      radiuse = math.fmod(math.fabs(left), self.rightWheelSpeedUnit)
      if  right > 0:
        right -= radiuse
      else:
        right += radiuse
      
   
    if  self.leftWheelName:
      obj.setAngularVelocityToParts(self.leftWheelName, left, self.leftMaxForce)
      self.currentLeftWheelSpeed = left

    if  self.rightWheelName:
      obj.setAngularVelocityToParts(self.rightWheelName, right, self.rightMaxForce)
      self.currentRightWheelSpeed = right

    return 

  def getAxleLength(self):
    return self.axleLength

  #
  #
  #
  def getLeftWheelRaius(self, obj):
    radius = 0.0
    part = obj.getParts(self.leftWheelName)
    if part.type == 'PARTS_TYPE_CYLINDER' :
      radius, length =part.giveSize()
    else:
      pass

    self.leftWheelRadius = radius
    return 0.0

  #
  #
  #
  def getRightWheelRaius(self, obj):
    radius = 0.0
    part = obj.getParts(self.rightWheelName)
    if part.type == 'PARTS_TYPE_CYLINDER' :
      radius, length =part.giveSize()
    else:
      pass

    self.rightWheelRadius = radius

    return 0.0

  def getLeftEncoderNoise(self):
    return self.leftEncoderNoise

  def getRightEncoderNoise(self):
    return self.rightEncoderNoise

  def getLeftSlipNoise(self):
    return self.leftSlipNoise

  def getRightSlipNoise(self):
    return self.rightSlipNoise

  def getCurrentLeftWheelSpeed(self):
    return self.currentLeftWheelSpeed

  def getCurrentRightWheelSpeed(self):
    return self.currentRightWheelSpeed

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

