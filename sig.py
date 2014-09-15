#
#   SIGVerse Client Library
#
#   Copyright(C) 2014, Isao Hara, AIST
#   Release under the MIT License.
#

import sys
import os
import time
import types
from sigcomm import *
from simobj import *

#
#  Reader for ControllerCmd
#     sigcomm.SigCommReader <--- SigCmdReader
#
class SigCmdReader(SigCommReader): 
  def __init__(self, owner):
    SigCommReader.__init__(self, owner)
    self.setHandler( SigCmdHandler(self), SigMessageHandler(self))

  def setHandler(self, dhndlr, mhndlr):
    self.cmdHandler = dhndlr
    self.msgHandler = mhndlr

  #
  # check command format and invoke 
  #
  def checkCommand(self):
    res = self.parser.checkDataCommand(self.buffer, self.current)
#    print "checkCommand:", res

    if res > 0:
      if self.cmdHandler :
#        print "Invoke Handler %d, %d" % (res, len(self.buffer))
        self.cmdHandler.invoke(res)
      return 0

    elif res == 0:
      print "Not enough data!!"
      return 0

    elif res == -1:
      res = self.parser.checkMessageCommand(self.buffer, self.current)
#      print "checkCommand:checkMessageCommand", res
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

  #
  # overwrite 'parse'
  #
  def parse(self, data):
    SigCommReader.parse(self, data)
    self.checkCommand()
    
#
#  Reader for ControllerData
#     sigcomm.SigCommReader <--- SigDataReader
#
class SigDataReader(SigCommReader): 
  def __init__(self, owner):
    SigCommReader.__init__(self, owner)
    self.command = []

  #
  # check command format and invoke 
  #
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

  #
  #  commands...
  # 
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

  #
  #  for synchronization
  #
  def setCommand(self, cmd):
    self.command.append(cmd)

  #
  #
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
  #
  # overwrite 'parse'
  #
  def parse(self, data):
    SigCommReader.parse(self, data)
    self.checkCommand()
    self.owner.finishReply()

#
#  Reader for SigService
#     sigcomm.SigCommReader <--- SigServiceReader
#
class SigServiceReader(SigCommReader): 
  def __init__(self, owner):
    SigCommReader.__init__(self, owner)
    self.command = []

  #
  # check command format and invoke 
  #
  def checkCommand(self):
    try:
      self.printPacket(self.buffer)
    except:
      pess

    self.clearBuffer()
  #
  #  for synchronization
  #
  def setCommand(self, cmd):
    self.command.append(cmd)
  #
  #
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
  #
  # overwrite 'parse'
  #
  def parse(self, data):
    SigCommReader.parse(self, data)
    self.checkCommand()
#    self.owner.finishReply()


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

  #
  # simulation is started
  #
  def startSim(self,msg):
      size = msg[2] + msg[2] % 4
      data = self.reader.read(size, 1)
      self.comm.setStartTime(msg[1])
      self.comm.start()

  #
  # simulation is stopped
  #
  def stopSim(self,msg):
      size = msg[1] + msg[1] % 4
      data = self.reader.read(size, 1)
      self.comm.stop()

  #
  #  call onRecvMsg function of a controller
  #
  def sendMsg(self,msg):
      padding_size = (msg[2] + msg[1] ) % 4
      data = self.reader.read(msg[2], 1)
      message = self.reader.read(msg[1], 1)
      if padding_size > 0:
        self.reader.read(padding_size, 1)
#      self.comm.onRecvMsg(SigMsgEvent(message))    
      thr = threading.Thread(target=runOnRecvMsg, args=(self.comm, message))    
      thr.start()

  #
  # called by SigCmdReader
  #
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
#  global function for thread excution.
#    'onRecMsg' function execute with a thread to avoid blocking read operation.
#    This function called by the SigMessageHandler.sendMsg function.
#
def runOnRecvMsg(comm, msg):
  comm.onRecvMsg(SigMsgEvent(msg))

#
#  Foundmental client class for SIGVerse:
#    A controller has two socket commnunication ports.
#    In this class, we called them as 'command_port' and 'data_port'. conadaptor
#
class SigClient:
  def __init__(self, myname, host="localhost", port=9000):
    self.name = myname
    self.cmdAdaptor=None
    self.dataAdaptor=None
    self.cmdReader=SigCmdReader(self)
    self.dataReader=SigDataReader(self)
    self.srvReader=SigServiceReader(self)
    self.services={}
    self.wait_for_reply=False
    self.setServer(host, port)

  def setServer(self, host, port):
    self.server=host
    self.port=port

  #
  #  connect to simserver
  #
  def connect(self):
    if self.cmdAdaptor is None:
      self.cmdAdaptor = SocketAdaptor(self.cmdReader, self.name+":cmd", self.server, self.port)
    self.cmdAdaptor.connect()

    if self.dataAdaptor is None:
      self.dataAdaptor = SocketAdaptor(self.dataReader, self.name+":data", self.server, self.port)
    self.dataAdaptor.connect()

  #
  #  send command with the command_port
  #
  def sendCmd(self, msg):
    self.cmdAdaptor.send(msg, self.name)

  #
  #  flag for waiting reply
  #
  def setWaitForReply(self):
    self.wait_for_reply=True

  def finishReply(self):
    self.wait_for_reply=False

  def waitForReply(self):
    while self.wait_for_reply :
       pass
  #
  #  send command with the data_port
  #
  def sendData(self, msg, flag=1):
    if flag :
      self.setWaitForReply()
      self.dataReader.setMsg(msg)
    self.dataAdaptor.send(msg, self.name)

  #
  #  close socket communication ports
  #
  def terminate(self):
    self.cmdAdaptor.terminate()
    self.dataAdaptor.terminate()

  def exit(self):
    self.terminate()

#
#  Communication base class for SIGVerve
#
class SigController(SigClient):
  def __init__(self, name, host="localhost", port=9000, ecclass=None):
    SigClient.__init__(self, name, host, port)
    self.cmdbuf=SigDataCommand()
    self.ec = None
    self.objs={}
    self.startSimTime = 0.0
    self.startTime=time.time()
    self.request_obj=False
    self.setEC(ecclass)
    self.mutex=threading.Lock()
  #
  #  set Execution Context
  #
  def setEC(self, ecclass):
    if ecclass :
      self.ecClass = ecclass
    else:
      self.ecClass = SigControllerEC
  #
  #  connetc to simserver
  #
  def connect(self):
    SigClient.connect(self)
    self.sendInit() 
    self.connected = True

  def attach(self):
    self.connect()

  #
  #  send initial message to simserver
  #
  def sendInit(self):
    self.cmdbuf.setHeader(cmdDataType['COMM_REQUEST_ATTACH_CONTROLLER'], name=self.name)
    self.sendCmd(self.cmdbuf.getEncodedCommand())

    self.cmdbuf.setHeader(cmdDataType['COMM_REQUEST_CONNECT_DATA_PORT'], name=self.name)
    self.sendData(self.cmdbuf.getEncodedCommand())
 
  #
  # for waiting a reply
  #
  def checkRequest(self):
    with self.mutex:
      return self.request_obj

  def setRequest(self, val):
    with self.mutex:
      self.request_obj = val

  #
  #  Request SimObj to create
  #
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
  #
  #  create SimObj, called by the cmdHandler
  #
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

      obj = SigSimObj(name, self)
      obj.updateTime = m_time

      attached = self.cmdbuf.unmarshalUShort()
      opts     = self.cmdbuf.unmarshalUInt()

      offset1  = self.cmdbuf.unmarshalUShort()
      offset2  = self.cmdbuf.unmarshalUShort()

      obj.setAttributes(data[offset1+off:offset2+off])
      obj.setParts(data[offset2+off:])
      
      self.objs[name] = obj

    self.setRequest(False)
    return
  #
  # invoke onCollision
  #
  def invokeOnCollision(self, data):
    evt = SigCollisionEvent(data)
    evt.parse()
    self.onCollision(evt)
    return
  #
  # send a message to other agent(s)
  #
  def sendMsg(self, to_name, msg, distance=-1.0):
    if type(to_name) == types.StringType:
      msgBuf = "%.5d,%s,%f,1,%s,"  % (len(msg), msg, distance, to_name)

    elif type(to_name) in (types.ListType, types.TupleType):
      msgBuf = "%.5d,%s,%f,%d,%s,"  % (len(msg), msg, distance, len(to_name), ','.to_name)

    else:
      print "[ERR} invalid to_name", to_name
      return
   
    self.sendMessageAction(msgBuf)
    return

  def broadcastMsg(self, msg, distance=-1.0):
    self.broadcast(msg, distance, -1)
    return

  def broadcastMsgToSrv(self, msg):
    self.broadcast(msg, -1.0, -2)
    return

  def broadcastMsgToCtl(self, msg, distance=-1.0):
    self.broadcast(msg, distance, -3)
    return

  def broadcast(self, msg, distance, to):
    msgBuf = "%.5d,%s,%f,%d,"  % (len(msg), msg, distance, to)
    self.sendMessageAction(msgBuf)
    return

  def sendMessageAction(self, msgBuf):
    self.cmdbuf.createCommand()
    size = len(msgBuf) + struct.calcsize("HH")
    self.cmdbuf.marshalUShort(cmdDataType['REQUEST_SENDMSG_FROM_CONTROLLER'])
    self.cmdbuf.marshalUShort(size)
    self.cmdbuf.copyString(msgBuf)
    self.sendData(self.cmdbuf.getEncodedDataCommand(), 0)
    return
  #
  #  for Service
  #
  def connectToService(self, name):
    try:
      return self.services[name]
    except:
      sev = None
      newport = self.port + 1
      count = 0 
      res = 0
      while res != 1 and count < 10:
        newport += 1
        srvAdaptor=SocketAdaptor(self.srvReader,self.name+(":srv%d" % newport),self.server,newport)
        res = srvAdaptor.bind()
        count += 1

      if res != 1:
        print "Fail to get service...[%s, %s] "  % (self.name, name)
        return None

      ##### Request to Connect #####################
      msgBuf = "%s,%s,"  % (name,self.name) 

      self.cmdbuf.createCommand()
      size = len(msgBuf) + struct.calcsize("HHH")
      self.cmdbuf.marshalUShort(cmdDataType['REQUEST_CONNECT_SERVICE'])
      self.cmdbuf.marshalUShort(size)
      self.cmdbuf.marshalUShort(newport)
      self.cmdbuf.copyString(msgBuf)
      self.sendData(self.cmdbuf.getEncodedDataCommand(), 0)

      ##############################################
      srv = None 
      srv_adaptor = srvAdaptor.wait_accept_service(5, False)

      if not srv_adaptor is None :
        data = srv_adaptor.recv_data(4, 2.0)
        if data :
          ack = srv_adaptor.getParser().unmarshalUShort()
          if ack == 1:
            print "connect to service [%s]" % name
            self.services[name] = srv_adaptor
            srv = ViewService(self, srv_adaptor)
            srv.setEntityName(self.name)
#            srv_adaptor.start()
          elif ack == 4:
            print "fail to connect to service [%s]" % name
            srv_adaptor.close()
          else:
            print "Unknown in connctToService "
            srv_adaptor.close()
        else:
          print "Fail to read accept message"
          srv_adaptor.close()
      else:
        print "ERROR in connectToService"

      srvAdaptor.close()
      return srv
  #
  #
  #
  def setStartTime(self, tm):
    self.startSimTime = tm

  def getCurrentTime(self):
    ctm = time.time() - self.startTime + self.startSimTime
    return ctm
  
  #
  #  start/stop the Execution context
  #
  def start(self):
    self.ec = self.ecClass(self)
    self.startTime=time.time()
    self.ec.start()

  def stop(self):
    if self.ec :
      self.ec.stop()
      self.ec = None
  #
  #  Virtual Functions
  # 
  def onInit(self,evt):
    return
   
  def onAction(self,evt):
    return self.ec.interval

  def onRecvMsg(self, evt):
    return

  def onCollision(self, evt):
    return

#
#  SerivceAdaptor
#
class SigService:
  def __init__(self, owner):
    self.name = ""
    self.owner = owner
    self.adaptor = None 

  def setName(self, name):
    self.adaptor.setHost(name)

  def setAdaptor(self, adp):
    self.adaptor = adp

  def setEntityName(self, name):
    self.name = name

#
#  ViewService
#    SigService <--- ViewService
#
class ViewService(SigService):
  def __init__(self, owner, adaptor):
    SigService.__init__(self, owner)
    self.adaptor = adaptor 

  def detectEntities(self, objs, cam_id):
    msgBuf = "%s,%d," % (self.name, cam_id)

    cmdbuf = self.adaptor.getParser()
    cmdbuf.createCommand()
    size = len(msgBuf) + struct.calcsize("HH")
    cmdbuf.marshalUShort(7)
    cmdbuf.marshalUShort(size)
    cmdbuf.copyString(msgBuf)

    sendBuf = cmdbuf.getEncodedDataCommand()
    self.adaptor.send(sendBuf)
#    self.adaptor.reader.printPacket( sendBuf ) 
    data = self.adaptor.recv_data(4, 2.0)
    if data :
      head = self.adaptor.getParser().unmarshalUShort()
      ssize = self.adaptor.getParser().unmarshalUShort()
      data = self.adaptor.recv_data(ssize, 2.0)
      if data :
        obj = data.split(',')
        n=obj.pop(0)
        for x in range(int(n)):
          objs.append(obj[x])
        return True
      else:
        pass
   
    return False



