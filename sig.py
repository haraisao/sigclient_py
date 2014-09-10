#
#  Communication Adaptor for SIGVerse
#

import sys
import os
import time
import types
from Quat import *
from sigcomm import *


#
#  Reader for ControllerCmd
#
class SigCmdReader(SigCommReader): 
  def __init__(self, owner):
    SigCommReader.__init__(self, owner)
    self.setHandler( SigCmdHandler(self), SigMessageHandler(self))

  def setHandler(self, dhndlr, mhndlr):
    self.cmdHandler = dhndlr
    self.msgHandler = mhndlr

  def checkCommand(self):
    res = self.parser.checkDataCommand(self.buffer, self.current)
    if res > 0:
      if self.cmdHandler :
#        print "Invoke Handler %d, %d" % (res, len(self.buffer))
        self.cmdHandler.invoke(res)
      return 0

    elif res == 0:
#      print "Not enough data!!"
      return 0

    elif res == -1:
      res = self.parser.checkMessageCommand(self.buffer, self.current)
      if res is None:
        print "Invalid reply!!"
        self.printPacket(self.buffer)
        self.skipBuffer(4)
        return -1
      else:
        if self.msgHandler :
          self.msgHandler.invoke(res)
    else:
      print "Unknown error", res
      return -1

  def parse(self, data):
    SigCommReader.parse(self, data)
    self.checkCommand()
    
#
#  Reader for ControllerData
#
class SigDataReader(SigCommReader): 
  def __init__(self, owner):
    SigCommReader.__init__(self, owner)
#    self.handler = SigDataHandler(self)
    self.command = []

  def checkCommand(self):
    try:
      cmd = self.command.pop(0)
      if cmd == cmdDataType['REQUEST_GET_ENTITY_POSITION']:
        self.setObjPosition(self.buffer)

      elif cmd == cmdDataType['REQUEST_SET_ENTITY_POSITION']:
        pass

      elif cmd == cmdDataType['REQUEST_GET_ENTITY_ROTATION']:
        self.setObjRotation(self.buffer)

      elif cmd == cmdDataType['REQUEST_SET_ENTITY_ROTATION']:
        pass

      elif cmd == "cmd:%d" % cmdDataType['COMM_REQUEST_CONNECT_DATA_PORT']:
        print "[INFO] Connect DataPort"
        pass

      else:
        print "cmd ==> %d" % (cmd)
        self.printPacket(self.buffer)
        pass

    except:
      print "No such command registered: ", cmd

    self.clearBuffer()

  def getSimObj(self):
    return self.owner.getObj()

  def setObjPosition(self, data):
    self.parser.setBuffer(data)
    sucess = self.parser.unmarshalBool()
    x = self.parser.unmarshalDouble()
    y = self.parser.unmarshalDouble()
    z = self.parser.unmarshalDouble()

    if sucess :
      self.getSimObj().setCurrentPosition(x, y, z)
    else:
      print "Fail to getPosition" 
    return

  def setObjRotation(self, data):
    self.parser.setBuffer(data)
    sucess = self.parser.unmarshalBool()
    qw = self.parser.unmarshalDouble()
    qx = self.parser.unmarshalDouble()
    qy = self.parser.unmarshalDouble()
    qz = self.parser.unmarshalDouble()

    if sucess :
      self.getSimObj().setCurrentRotation(qw, qx, qy, qz)
    else:
      print "Fail to getRotation" 
    return

  def setCommand(self, cmd):
    self.command.append(cmd)

  def setMsg(self, msg):
    res = self.parser.checkDataCommand(msg)
    cmd = -1
    if res > 0:
      self.parser.getHeader(msg[4:])
      cmd =  self.parser.type
      self.setCommand("cmd:%d" % (cmd))
    else:
      self.parser.setBuffer(msg)
      cmd = self.parser.unmarshalUShort(0)
      self.setCommand(cmd)
    self.parser.clearBuffer()

    if cmd == -1 :
      print "Invalid command..." 
      self.printPacket(msg)


  def parse(self, data):
    SigCommReader.parse(self, data)
    self.checkCommand()
    self.owner.finishReply()


#
#  Callback handler for command packet.....
#
class SigCmdHandler: 
  def __init__(self, rdr):
    self.reader = rdr
    self.comm = rdr.owner
    self.command = SigDataCommand()

  def invoke(self, n):
    data = self.reader.read(n, 1)
    cmd = data[4:len(data) - 2]
    self.command.setBuffer(cmd)
    self.command.getHeader()

    if self.command.type == cmdDataType['COMM_RESULT_GET_ENTITY'] :
      print "[INFO] Call createSimObj"
      self.comm.createSimObj(cmd)
      pass

    elif self.command.type == cmdDataType['COMM_RESULT_ATTACH_CONTROLLER'] :
      print "[INFO] Controller Attached"
      pass

    elif self.command.type == cmdDataType['COMM_INVOKE_CONTROLLER_ON_COLLISION'] :
      self.comm.invokeOnCollision(self.command.getRemains())
      pass

    else:
      self.command.printHeader()
      self.reader.printPacket(cmd)

#
#  Callback handler for message
#
class SigMessageHandler: 
  def __init__(self, rdr):
    self.reader = rdr
    self.comm = rdr.owner

  def startSim(self,msg):
      size = msg[2] + msg[2] % 4
      data = self.reader.read(size, 1)
      self.comm.setStartTime(msg[1])
      self.comm.start()

  def stopSim(self,msg):
      size = msg[1] + msg[1] % 4
      data = self.reader.read(size, 1)
      self.comm.stop()

  def sendMsg(self,msg):
      padding_size = (msg[2] + msg[1] ) % 4
      data = self.reader.read(msg[2], 1)
      message = self.reader.read(msg[1], 1)
      if padding_size > 0:
        self.reader.read(padding_size, 1)
      self.comm.onRecvMsg(SigMsgEvent(message))    

  def invoke(self, msg):
    if msg[0] == cmdType['START_SIM']:
      self.startSim(msg)
    elif msg[0] == cmdType['STOP_SIM']:
      self.stopSim(msg)
    elif msg[0] == cmdType['SEND_MESSAGE']:
      self.sendMsg(msg)
    else:
      self.reader.printPacket(cmd)

#
#  Foundmental clint class for SIGVerse
#
class SigClient:
  def __init__(self, myname, host="localhost", port=9000):
    self.name = myname
    self.cmdAdaptor=None
    self.dataAdaptor=None
    self.cmdReader=SigCmdReader(self)
    self.dataReader=SigDataReader(self)
    self.wait_for_reply=False
    self.setServer(host, port)

  def setServer(self, host, port):
    self.server=host
    self.port=port

  def connect(self):
    if self.cmdAdaptor is None:
      self.cmdAdaptor = SocketAdaptor(self.cmdReader, self.name, self.server, self.port)
    self.cmdAdaptor.connect()

    if self.dataAdaptor is None:
      self.dataAdaptor = SocketAdaptor(self.dataReader, self.name, self.server, self.port)
    self.dataAdaptor.connect()

  def sendCmd(self, msg):
    self.cmdAdaptor.send(self.name, msg)

  def setWaitForReply(self):
    self.wait_for_reply=True

  def finishReply(self):
    self.wait_for_reply=False

  def waitForReply(self):
    while self.wait_for_reply :
       pass

  def sendData(self, msg, flag=1):
    if flag :
      self.setWaitForReply()
      self.dataReader.setMsg(msg)
    self.dataAdaptor.send(self.name, msg)

  def terminate(self):
    self.cmdAdaptor.terminate()
    self.dataAdaptor.terminate()

  def exit(self):
    self.terminate()

#
#   Attribute for SimObj
#
class SigObjAttribute:
  def __init__(self, name):
    self.name=name
    self.value=None
    self.valueType=None
    self.group=None

#
#  CParts for SimObj
#
class SigObjPart:
  def __init__(self,name):
    self.name=name
    self.id=None
    self.type=None
    self.pos=[0,0,0]
    self.quaternion=[0,0,0,0]
    self.partsValue=None

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
 
  def getObj(self):
    self.cmdbuf.setHeader(cmdDataType['COMM_REQUEST_GET_ENTITY'], name=self.name)
    self.controller.sendCmd(self.cmdbuf.getEncodedCommand())

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
    self.cmdbuf.copyString(name)
    self.controller.sendData(self.cmdbuf.getEncodedDataCommand(), 0)
    return 

  def updatePosition(self):
    self.cmdbuf.createCommand()
    name = self.name+','
    size = len(name) + struct.calcsize("HH")
    self.cmdbuf.marshalUShort(cmdDataType['REQUEST_GET_ENTITY_POSITION'])
    self.cmdbuf.marshalUShort(size)
    self.cmdbuf.copyString(name)
    self.controller.sendData(self.cmdbuf.getEncodedDataCommand())
    return

  def setCurrentRotation(self, qw, qx, qy, qz):
    self.parts['body'].setQuaternion(qw, qx, qy, qz)
    return 

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
    self.cmdbuf.copyString(name)
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
    self.cmdbuf.copyString(name)
    self.controller.sendData(self.cmdbuf.getEncodedDataCommand())
    return

  def getPosition(self):
    self.updatePosition()
    self.controller.waitForReply()
    return self.parts['body'].getPos()

  def getRotation(self):
    self.updateRotation()
    self.controller.waitForReply()
    return self.parts['body'].getQuaternion()

  def x(self, val=None):
    return self.parts['body'].x(val)

  def y(self, val=None):
    return self.parts['body'].y(val)

  def z(self, val=None):
    return self.parts['body'].z(val)

  def qw(self, val=None):
    return self.parts['body'].qw(val)

  def qx(self, val=None):
    return self.parts['body'].qx(val)

  def qy(self, val=None):
    return self.parts['body'].qy(val)

  def qz(self, val=None):
    return self.parts['body'].qz(val)

  def setAttributes(self, data):
    attr = SigCmdMarshaller(data)

    while attr.bufsize > attr.offset :
      offtmp=attr.offset
      datalen = attr.unmarshalUShort()
      name = attr.unmarshalString()
      group = attr.unmarshalString()
      vallen = attr.unmarshalUShort()
      valtype = attr.unmarshalUShort()
      value = None
      if valtype == typeValue['VALUE_TYPE_BOOL']:
        value = attr.unmarshalUShort()
        if value : value="True"
        else : value="False"
      elif valtype == typeValue['VALUE_TYPE_DOUBLE']:
        value = attr.unmarshalDouble()
      elif valtype == typeValue['VALUE_TYPE_STRING']:
        value = attr.unmarshalString()
      else:
        pass
#      print "attr datalen=%d  name=%s group=%s val_type=%d" % (datalen, name, group, valtype)
#      print "value = ",value

      self.attributes[name] = SigObjAttribute(name)
      self.attributes[name].value = value
      self.attributes[name].valueType = valtype
      self.attributes[name].group = group
      attr.offset = offtmp+datalen 

  def setParts(self, data):
    body = SigCmdMarshaller(data)
    bodylen=body.unmarshalUShort()      

    while body.bufsize > body.offset :
      offtmp=body.offset
      datalen=body.unmarshalUShort()      
#      print "body datalen=%d " % (datalen)
      id = body.unmarshalUInt()
      type = body.unmarshalUShort()
      name = body.unmarshalString()

      self.parts[name] = SigObjPart(name)
      self.parts[name].id = id

      x = body.unmarshalDouble()
      y = body.unmarshalDouble()
      z = body.unmarshalDouble()
      self.parts[name].setPos(x, y, z)

      rtype = body.unmarshalUShort()
      if rtype == 0:  # ROTATION_TYPE_QUATERNION
        q1 = body.unmarshalDouble()
        q2 = body.unmarshalDouble()
        q3 = body.unmarshalDouble()
        q4 = body.unmarshalDouble()
        self.parts[name].setQuaternion(q1, q2, q3, q4)

      extlen = body.unmarshalUShort()

      if type == partType['PARTS_TYPE_BOX'] :
        self.parts[name].type = 'PARTS_TYPE_BOX'
        x = body.unmarshalDouble()
        y = body.unmarshalDouble()
        z = body.unmarshalDouble()
        self.parts[name].partsValue = [x, y, z]

      elif type == partType['PARTS_TYPE_CYLINDER'] :
        self.parts[name].type = 'PARTS_TYPE_CYLINDER'
        r = body.unmarshalDouble()
        l = body.unmarshalDouble()
        self.parts[name].partsValue = [r, l]

      elif type == partType['PARTS_TYPE_SPHERE'] :
        self.parts[name].type = 'PARTS_TYPE_SPHERE'
        r = body.unmarshalDouble()
        self.parts[name].partsValue = [r]

#      print "id=%d, type=%d name=%s " % (id, type, name)
#      print "pos=%f,%f,%f, Q=%f,%f,%f,%f  ext=%d " % (x,y,z,q1,q2,q3,q4,extlen)

      body.offset = offtmp +datalen

#
#  Communication base class for SIGVerve
#
class SigController(SigClient):
  def __init__(self, name, ecclass=None):
    SigClient.__init__(self, name)
    self.cmdbuf=SigDataCommand()
    self.ec = None
    self.objs={}
    self.startSimTime = 0.0
    self.startTime=time.time()
    self.request_obj=False
    self.setEC(ecclass)
    self.mutex=threading.Lock()

  def setEC(self, ecclass):
    if ecclass :
      self.ecClass = ecclass
    else:
      self.ecClass = SigControllerEC

  def connect(self):
    SigClient.connect(self)
    self.sendInit() 
    self.connected = True

  def attach(self):
    self.connect()

  def sendInit(self):
    self.cmdbuf.setHeader(cmdDataType['COMM_REQUEST_ATTACH_CONTROLLER'], name=self.name)
    self.sendCmd(self.cmdbuf.getEncodedCommand())

    self.cmdbuf.setHeader(cmdDataType['COMM_REQUEST_CONNECT_DATA_PORT'], name=self.name)
    self.sendData(self.cmdbuf.getEncodedCommand())

  def getObjOld(self, name=None):
    if name is None : name = self.name
    try:
      return self.objs[name]
    except:
      obj = SigSimObj(name, self)
      obj.getObj()
      self.objs[name] = obj
    return obj

  def checkRequest(self):
    with self.mutex:
      return self.request_obj

  def setRequest(self, val):
    with self.mutex:
      self.request_obj = val

  def getObj(self, name=None, waitFlag=1):
    if name is None : name = self.name
    try:
      return self.objs[name]
    except:
      self.setRequest(True)
      self.cmdbuf.setHeader(cmdDataType['COMM_REQUEST_GET_ENTITY'], name=name)
      self.sendCmd(self.cmdbuf.getEncodedCommand())
      if waitFlag :
        while self.checkRequest() :
          pass

      try:
        return self.objs[name]
      except:
        return None

  def createSimObj(self, data):
    self.cmdbuf.setBuffer(data)
    self.cmdbuf.getHeader()
    result=self.cmdbuf.unmarshalUShort()
    if result != cmdType['COMM_RESULT_OK'] :
      self.setRequest(False)
      return False

    m_time=self.cmdbuf.unmarshalDouble()
    exist=self.cmdbuf.unmarshalUShort()

    if exist :
      off = self.cmdbuf.offset
      datalen=self.cmdbuf.unmarshalUShort()
      id=self.cmdbuf.unmarshalUInt()
      name=self.cmdbuf.unmarshalString()
      klass=self.cmdbuf.unmarshalString()
#      print "datalen=%d, id=%d , name=%s, class=%s" % (datalen, id, name, klass)

      obj = SigSimObj(name, self)
      obj.updateTime = m_time

      attached = self.cmdbuf.unmarshalUShort()
      opts     = self.cmdbuf.unmarshalUInt()
      offset1  = self.cmdbuf.unmarshalUShort()
      offset2  = self.cmdbuf.unmarshalUShort()
#      print "attached=%d opts=%d offset1=%d offset2=%d" % (attached, opts, offset1, offset2)
      attrlen  = self.cmdbuf.unmarshalUShort()
#      print "attrlen=%d , size=%d" % (attrlen, len(data[offset1+off:offset2+off]))

      obj.setAttributes(data[offset1+off+2:offset2+off])
      obj.setParts(data[offset2+off:])
      
      self.objs[name] = obj

    self.setRequest(False)
    return

  def invokeOnCollision(self, data):
    evt = SigCollisionEvent(data)
    evt.parse()
    self.onCollision(evt)
    return

  def setStartTime(self, tm):
    self.startSimTime = tm
 
  def onInit(self,evt):
    return
   
  def onAction(self,evt):
    return self.ec.interval

  def onRecvMsg(self, evt):
    return

  def onCollision(self, evt):
    return

  def getCurrentTime(self):
    ctm = time.time() - self.startTime + self.startSimTime
    return ctm

  def start(self):
    self.ec = self.ecClass(self)
    self.startTime=time.time()
    self.ec.start()

  def stop(self):
    if self.ec :
      self.ec.stop()
      self.ec = None


class SigCollisionEvent:
  def __init__(self, data):
    self.parser = SigCmdMarshaller(data)
#    self.parser.printPacket(data)
    self.withVals = []
    self.withParts = []
    self.myParts = []
 
  def parse(self):
    currentTime=self.parser.unmarshalDouble() 
    wn=self.parser.unmarshalUShort() 
    for i in range(wn):
      wi=self.parser.unmarshalString()
      wv, wp, mp, sp = wi.split(":")
      self.withVals.append(wv)
      self.withParts.append(wp)
      self.myParts.append(mp)
    return 

  def getWith(self):
    return self.withVals

  def getWithParts(self):
    return self.withParts

  def getMyParts(self):
    return self.myParts

