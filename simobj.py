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
from Quat import *
from sigcomm import *
from sig import *

#
#   Attribute for SimObj
#      sigcomm.SigMarshaller <--- SigObjAttribute
#
class SigObjAttribute(SigMarshaller):
  def __init__(self, data=''):
    SigMarshaller.__init__(self, data)
    self.name=''
    self.value=None
    self.valueType=None
    self.group=None

  def parse(self):
    datalen = self.unmarshalUShort()
    self.name = self.unmarshalString()
    self.group = self.unmarshalString()
    vallen = self.unmarshalUShort()
    self.valueType = self.unmarshalUShort()

    if self.valueType == typeValue['VALUE_TYPE_BOOL']:
      self.valueType = 'VALUE_TYPE_BOOL'
      value = self.unmarshalUShort()
      if value : self.value=True
      else : self.value=False

    elif self.valueType == typeValue['VALUE_TYPE_DOUBLE']:
      self.valueType = 'VALUE_TYPE_DOUBLE'
      self.value = self.unmarshalDouble()

    elif self.valueType == typeValue['VALUE_TYPE_STRING']:
      self.valueType = 'VALUE_TYPE_STRING'
      self.value = self.unmarshalString()
    else:
      pass

#
#  CParts for SimObj
#      sigcomm.SigMarshaller <--- SigObjPart
#
class SigObjPart(SigMarshaller):
  def __init__(self, data):
    SigMarshaller.__init__(self, data)
    self.name = ''
    self.id=None
    self.type=None
    self.pos=[0,0,0]
    self.quaternion=[0,0,0,0]
    self.partsValue=None

  def parse(self):
    datalen = self.unmarshalUShort()      
    self.id = self.unmarshalUInt()
    type = self.unmarshalUShort()
    self.name = self.unmarshalString()

    self.pos[0] = self.unmarshalDouble()
    self.pos[1] = self.unmarshalDouble()
    self.pos[2] = self.unmarshalDouble()

    rtype = self.unmarshalUShort()
    if rtype == 0:  # ROTATION_TYPE_QUATERNION
      self.quaternion[0] = self.unmarshalDouble()
      self.quaternion[1] = self.unmarshalDouble()
      self.quaternion[2] = self.unmarshalDouble()
      self.quaternion[3] = self.unmarshalDouble()

      extlen = self.unmarshalUShort()

      if type == partType['PARTS_TYPE_BOX'] :
        self.type = 'PARTS_TYPE_BOX'
        x = self.unmarshalDouble()
        y = self.unmarshalDouble()
        z = self.unmarshalDouble()
        self.partsValue = [x, y, z]

      elif type == partType['PARTS_TYPE_CYLINDER'] :
        self.type = 'PARTS_TYPE_CYLINDER'
        r = self.unmarshalDouble()
        l = self.unmarshalDouble()
        self.partsValue = [r, l]

      elif type == partType['PARTS_TYPE_SPHERE'] :
        self.type = 'PARTS_TYPE_SPHERE'
        r = self.unmarshalDouble()
        self.partsValue = [r]

      else:
        self.type = 'PARTS_TYPE_UNKNOWN'
        self.partsValue = None
  #
  #  Position
  #
  def setPos(self, x, y, z):
    self.pos=[x,y,z]

  def getPos(self):
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


#
#  SimObj
#
class SigSimObj:
  def __init__(self, name, ctrl):
    self.cmdbuf=SigDataCommand()
    self.name=name
    self.parts = {}
    self.attributes = {}
    self.updateTime=0.0
    self.controller = ctrl

  #
  # Attach SimObj 
  # 
  def getObj(self):
    self.cmdbuf.setHeader(cmdDataType['COMM_REQUEST_GET_ENTITY'], name=self.name)
    self.controller.sendCmd(self.cmdbuf.getEncodedCommand())

  #
  #  Parse attribute from simserve
  #
  def setAttributes(self, data):
    bufsize = len(data)
    attr = SigMarshaller(data)

    attrlen = attr.unmarshalUShort()
    offset=attr.offset

    while bufsize > offset :
      attr.offset = offset
      datalen = attr.unmarshalUShort()

      attribute = SigObjAttribute(data[offset:offset+datalen])
      attribute.parse()
      self.attributes[attribute.name] = attribute

      offset = offset+datalen 

  #
  #  Parse parts info from  simserver
  #
  def setParts(self, data):
    body = SigMarshaller(data)
    bodylen=body.unmarshalUShort()      

    offset=body.offset
    bufsize = len(data)

    while bufsize > offset :
      body.offset = offset
      datalen = body.unmarshalUShort()      

      part = SigObjPart(data[offset:offset+datalen])
      part.parse()
      self.parts[part.name] = part

      offset = offset+datalen

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
    return self.parts['body'].getPos()

  def setCurrentPosition(self, x, y, z):
    self.parts['body'].setPos(x, y, z)
    return 

  def setPosition(self, x, y, z):
    self.parts['body'].setPos(x, y, z)
    self.cmdbuf.createCommand()
    name = self.name+','
    size = len(name) + struct.calcsize("HH")+struct.calcsize("ddd")
    self.cmdbuf.marshalUShort(cmdDataType['REQUEST_SET_ENTITY_POSITION'])
    self.cmdbuf.marshalUShort(size)
    self.cmdbuf.marshalDouble(x)
    self.cmdbuf.marshalDouble(y)
    self.cmdbuf.marshalDouble(z)
    self.cmdbuf.marshalString(name, 0)
    self.controller.sendData(self.cmdbuf.getEncodedDataCommand(), 0)
    return 

  def updatePosition(self):
    self.cmdbuf.createCommand()
    name = self.name+','
    size = len(name) + struct.calcsize("HH")
    self.cmdbuf.marshalUShort(cmdDataType['REQUEST_GET_ENTITY_POSITION'])
    self.cmdbuf.marshalUShort(size)
    self.cmdbuf.marshalString(name, 0)
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
    return self.parts['body'].getQuaternion()

  def setRotation(self, qw, qx, qy, qz, abs=1):
    self.parts['body'].setQuaternion(qw, qx, qy, qz)
    self.cmdbuf.createCommand()
    name = self.name+','
    size = len(name) + struct.calcsize("HHH")+struct.calcsize("dddd")
    self.cmdbuf.marshalUShort(cmdDataType['REQUEST_SET_ENTITY_ROTATION'])
    self.cmdbuf.marshalUShort(size)
    self.cmdbuf.marshalUShort(abs)
    self.cmdbuf.marshalDouble(qw)
    self.cmdbuf.marshalDouble(qx)
    self.cmdbuf.marshalDouble(qy)
    self.cmdbuf.marshalDouble(qz)
    self.cmdbuf.marshalString(name, 0)
    self.controller.sendData(self.cmdbuf.getEncodedDataCommand(), 0)
    return 

  def setAxisAndAngle(self, x, y, z, ang):
    quat = Quat(x, y, z, ang)
    self.setRotation(quat.w, quat.x, quat.y, quat.z)
    return

  def updateRotation(self):
    self.cmdbuf.createCommand()
    name = self.name+','
    size = len(name) + struct.calcsize("HH")
    self.cmdbuf.marshalUShort(cmdDataType['REQUEST_GET_ENTITY_ROTATION'])
    self.cmdbuf.marshalUShort(size)
    self.cmdbuf.marshalString(name, 0)
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
    return 

  def addForce(self, dfx, dfy, dfz):
    self.cmdbuf.createCommand()
    self.cmdbuf.setHeader(cmdDataType['COMM_REQUEST_ADD_FORCE'], name=self.name)
    self.cmdbuf.marshalDouble(dfx)
    self.cmdbuf.marshalDouble(dfy)
    self.cmdbuf.marshalDouble(dfz)
    self.cmdbuf.marshalBool(0)  # false
    self.controller.sendCmd(self.cmdbuf.getEncodedCommand())
     
    return 

  def setAccel(self, ax, ay, az):
    return 

  def setTorque(self, x, y, z):
    return 

  #
  # Joint...
  #    Ummm... Which is the newer version?
  #  
  def setJointAngle(self, joint_name, angle):
    self.cmdbuf.createCommand()
    self.cmdbuf.setHeader(cmdDataType['COMM_REQUEST_SET_JOINT_ANGLE'], name=self.name)
    self.cmdbuf.marshalString(joint_name)
    self.cmdbuf.marshalDouble(angle)
    self.cmdbuf.marshalBool(0)  # false
    self.controller.sendCmd(self.cmdbuf.getEncodedCommand())
    return 

  def setJointQuaternion(self, joint_name, qw, qx, qy, qz, offset=0):
    self.cmdbuf.createCommand()
    msg = self.name + ',' + joint_name + ','
    if offset :
      msg += '1,'
    else:
      msg += '0,'
    size = len(msg) + struct.calcsize("HH") + struct.calcsize("dddd")
    self.cmdbuf.marshalUShort(cmdDataType['REQUEST_SET_JOINT_QUATERNION'])
    self.cmdbuf.marshalUShort(size)
    self.cmdbuf.marshalDouble(qw)
    self.cmdbuf.marshalDouble(qx)
    self.cmdbuf.marshalDouble(qy)
    self.cmdbuf.marshalDouble(qz)
    self.cmdbuf.marshalString(msg, 0)
    self.controller.sendData(self.cmdbuf.getEncodedDataCommand(), 0)
    return 
