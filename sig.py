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
#from sigcomm import *
import sigcomm
#from simobj import *
import simobj

#
#  Reader for ControllerCmd
#     sigcomm.SigCommReader <--- SigCmdReader
#
class SigCmdReader(sigcomm.SigCommReader): 
  def __init__(self, owner):
    sigcomm.SigCommReader.__init__(self, owner, sigcomm.SigDataCommand())
    self.setHandler( SigCmdHandler(self), SigMessageHandler(self))

  def setHandler(self, dhndlr, mhndlr):
    self.cmdHandler = dhndlr
    self.msgHandler = mhndlr

  #
  # check command format and invoke 
  #
  def checkCommand(self):
    result = -1
#    while self.checkBuffer() :
    res = self.parser.checkDataCommand(self.buffer, self.current)

    if res > 0:
      if self.cmdHandler :
   #     print "Invoke Handler %d, %d" % (res, len(self.buffer))
        self.cmdHandler.invoke(res)
      return 0

    elif res == 0:
      print "Not enough data!!"
      return 0

    elif res == -1:
      res = self.parser.checkMessageCommand(self.buffer, self.current)
#      print "checkCommand:checkMessageCommand", res
      if res is None:
        print "Invalid reply!!, clear current buffer"
        self.printPacket(self.buffer)
        self.clearBuffer()
#        pos = self.buffer.find('\xdc\xba')
#        if pos < 0:
#          self.clearBuffer()
#        else:
#          self.printPacket( self.buffer[:pos+2] )
#          self.clearBuffer(pos+2)
#          print "-------------------------------------"
      else:
        if self.msgHandler :
          self.msgHandler.invoke(res)
        result = 0
    else:
      print "Unknown error", res

    return result

  #
  # overwrite 'parse'
  #
  def parse(self, data):
    sigcomm.SigCommReader.parse(self, data)
    while self.checkBuffer():
      self.checkCommand()
    
#
#  Reader for ControllerData
#     sigcomm.SigCommReader <--- SigDataReader
#
class SigDataReader(sigcomm.SigCommReader): 
  def __init__(self, owner):
    sigcomm.SigCommReader.__init__(self, owner, sigcomm.SigDataCommand())
    self.command = []

  #
  # check command format and invoke 
  #
  def checkCommand(self):
    len = 0
    try:
      cmd = self.command.pop(0)

      if cmd == cmdDataType['REQUEST_GET_ENTITY_POSITION']:
        self.setObjPosition(self.buffer)
        len=self.parser.offset

      elif cmd == cmdDataType['REQUEST_SET_ENTITY_POSITION']:
        pass

      elif cmd == cmdDataType['REQUEST_GET_ENTITY_ROTATION']:
        self.setObjRotation(self.buffer)
        len=self.parser.offset

      elif cmd == cmdDataType['REQUEST_SET_ENTITY_ROTATION']:
        pass

      elif cmd == cmdDataType['REQUEST_GRASP_OBJECT']:
        self.parser.setBuffer(self.buffer)
        result, = self.parser.unmarshal('H')
        len=self.parser.offset
        if result == 0:
          print "Success to grasp the object."
        elif result == 1:
          print "Fail to grasp, no object found."
        elif result == 2:
          print "Already grasp the object "
        elif result == 3:
          print "Already grasp an other object "
        elif result == 4:
          print "Fail to grasp, out of reach."
        elif result == 5:
          print "Fail to grasp, the target is too far."
        else:
          print "Unknown ERROR in graspObj"

      elif cmd == cmdDataType['REQUEST_GET_ALL_JOINT_ANGLES']:
        self.parser.setBuffer(self.buffer)
        recvSize, jointSize = self.parser.unmarshal('HH')
        recvSize -= struct.calcsize('HH')
        msg = self.parser.getRemains(recvSize)
        if msg is None:
          print "too short!!"
          self.command.insert(0, cmd)
          return
        else:
          msg_ar = msg.split(',')
          obj = self.getSimObj()
          for i in range(jointSize) :
            jname = msg_ar[i*2]
            ang = msg_ar[i*2+1]
            obj.joints[jname] = float(ang)

      elif cmd == "cmd:%d" % cmdDataType['COMM_REQUEST_CONNECT_DATA_PORT']:
        print "[INFO] Connect DataPort"
        pass

      else:
        print "cmd ==> %d" % (cmd)
        self.printPacket(self.buffer)
        pass

    except:
      print "No such command registered: ", cmd
    #  self.printPacket(self.buffer)

#    print "clear Buffer len: ", len
    self.clearBuffer(len)
#    self.clearBuffer()

  #
  #  commands...
  # 
  def getSimObj(self):
    return self.owner.getObj()

  def setObjPosition(self, data):
    self.parser.setBuffer(data)
    success, x, y, z = self.parser.unmarshal('Bddd')

    if success :
      self.getSimObj().setCurrentPosition(x, y, z)
    else:
      print "Fail to getPosition" 
    return

  def setObjRotation(self, data):
    self.parser.setBuffer(data)
    success, qw, qx, qy, qz = self.parser.unmarshal('Bdddd')

    if success :
      self.getSimObj().setCurrentRotation(qw, qx, qy, qz)
    else:
      print "Fail to setObjRotation" 
    return

  #
  # Camera...
  #
  def getCamFOV(self):
    return 

  def getCamAs(self):
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
      cmd, = self.parser.unmarshal('H')
      self.setCommand(cmd)
    self.parser.clearBuffer()

    if cmd == -1 :
      print "Invalid command..." 
      self.printPacket(msg)
  #
  # overwrite 'parse'
  #
  def parse(self, data):
    sigcomm.SigCommReader.parse(self, data)
    self.checkCommand()
    self.owner.finishReply()

#
#  Reader for SigService
#     sigcomm.SigCommReader <--- SigServiceReader
#
class SigServiceReader(sigcomm.SigCommReader): 
  def __init__(self, owner):
    sigcomm.SigCommReader.__init__(self, owner, sigcomm. SigSrvCommand())
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
      cmd, = self.parser.unmarshal('H')
      self.setCommand(cmd)
    self.parser.clearBuffer()

    if cmd == -1 :
      print "Invalid command..." 
      self.printPacket(msg)
  #
  # overwrite 'parse'
  #
  def parse(self, data):
    sigcomm.SigCommReader.parse(self, data)
    self.checkCommand()
#    self.owner.finishReply()


#
#  Callback handler for command packet.....
#
class SigCmdHandler: 
  def __init__(self, rdr):
    self.reader = rdr
    self.comm = rdr.owner
    self.command = sigcomm.SigDataCommand()

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
#      self.comm.onRecvMsg(sigcomm.SigMsgEvent(message))    
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
#      self.reader.printPacket(cmd)
      pass

#
#  global function for thread excution.
#    'onRecMsg' function execute with a thread to avoid blocking read operation.
#    This function called by the SigMessageHandler.sendMsg function.
#
def runOnRecvMsg(comm, msg):
  comm.onRecvMsg(sigcomm.SigMsgEvent(msg))

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
      self.cmdAdaptor = sigcomm.SocketAdaptor(self.cmdReader, self.name+":cmd", self.server, self.port)
    self.cmdAdaptor.connect()

    if self.dataAdaptor is None:
      self.dataAdaptor = sigcomm.SocketAdaptor(self.dataReader, self.name+":data", self.server, self.port)
    self.dataAdaptor.connect()

  #
  #  send command with the command_port
  #
  def sendCmd(self, msg):
    self.cmdAdaptor.send(msg, self.name)
  
  #
  #
  #
  def getAllSockets(self):
    res = []
    for x in self.services.values():
      res.append(x.socket)
    return res
    
  def waitForRequestSocket(self, timeout=0.1):
    try:
      rready, wready, xready = select.select(self.getAllSockets(), [], [], timeout)
      return rready
    except:
      print "Error in wait_for_read"
      return None

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
    self.cmdbuf = sigcomm.SigDataCommand()
    self.ec = None
    self.objs={}
    self.startSimTime = 0.0
    self.startTime=time.time()
    self.request_obj=False
    self.setEC(ecclass)
    self.mutex=threading.Lock()

  #
  #
  def getName(self):
    return self.name

  def getMarshaller(self):
    return self.cmdbuf
 
  #
  #  set Execution Context
  #
  def setEC(self, ecclass):
    if ecclass :
      self.ecClass = ecclass
    else:
      self.ecClass = sigcomm.SigControllerEC
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
        return self.objs[name]
  #
  #  create SimObj, called by the cmdHandler
  #
  def createSimObj(self, data):
    self.cmdbuf.setBuffer(data)
    self.cmdbuf.getHeader()
    result, = self.cmdbuf.unmarshal('H')
    if result != cmdType['COMM_RESULT_OK'] :
      self.setRequest(False)
      return False

    m_time, exist = self.cmdbuf.unmarshal('dH')

    if exist :
      off = self.cmdbuf.offset
      datalen,id,name,klass = self.cmdbuf.unmarshal('HISS')

      obj = simobj.SigSimObj(name, self)
      obj.updateTime = m_time

      attached,opts,offset1,offset2 = self.cmdbuf.unmarshal('HIHH')

      obj.setAttributes(data[offset1+off:offset2+off])
      obj.setParts(data[offset2+off:])
      
      self.objs[name] = obj

    self.setRequest(False)
    return
  #
  # invoke onCollision
  #
  def invokeOnCollision(self, data):
    evt = sigcomm.SigCollisionEvent(data)
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
    self.cmdbuf.createMsgCommand(cmdDataType['REQUEST_SENDMSG_FROM_CONTROLLER'], msgBuf)
    self.sendData(self.cmdbuf.getEncodedDataCommand(), 0)
    return
  #
  #  for Service
  #
  def checkSerice(self, name):
    return False

  def connectToService(self, name):
    try:
      adaptor = self.services[name]
      return ViewService(self, adaptor)
    except:
      sev = None
      newport = self.port + 1
      count = 0 
      res = 0
      while res != 1 and count < 10:
        newport += 1
        srvAdaptor = sigcomm.SocketAdaptor(self.srvReader,self.name+(":srv%d" % newport),self.server,newport)
        res = srvAdaptor.bind()
        count += 1

      if res != 1:
        print "Fail to get service...[%s, %s] "  % (self.name, name)
        return None

      ##### Request to Connect #####################
      msgBuf = "%s,%s,"  % (name,self.name) 

      self.cmdbuf.createMsgCommand(cmdDataType['REQUEST_CONNECT_SERVICE'], msgBuf, ('H', newport))
      self.sendData(self.cmdbuf.getEncodedDataCommand(), 0)

      ##############################################
      srv = None 
      #
      #  Wait 5 seconds until connection from the service.
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
            print "Unknown in connectToService "
            srv_adaptor.close()
        else:
          print "Fail to read accept message"
          srv_adaptor.close()
      else:
        print "ERROR in connectToService"

      #
      # close service adaptor for connection
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
class SigServiceBase:
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
#    SigServiceBase <--- ViewService
#
class ViewService(SigServiceBase):
  def __init__(self, owner, adaptor):
    SigServiceBase.__init__(self, owner)
    self.adaptor = adaptor 
    self.command={"capture":5, "distance":6, "detect": 7, }

  def detectEntities(self, cam_id):
    objs = []
    msgBuf = "%s,%d," % (self.name, cam_id)

    cmdbuf = self.adaptor.getParser()
    cmdbuf.createMsgCommand(self.command["detect"], msgBuf)
    self.adaptor.send( cmdbuf.getEncodedDataCommand() )

    data = self.adaptor.recv_data(4, 2.0)
    if data :
      head,ssize = self.adaptor.getParser().unmarshal('HH')
      data = self.adaptor.recv_data(ssize-4, 2.0)
      if data :
        obj = data.split(',')
        n=obj.pop(0)
        for x in range(int(n)):
          objs.append(obj[x])
        return objs
      else:
        pass
    return None

  def captureView(self, cam_id, colorType, imgSize):
    msgBuf = "%s,%d," % (self.name, cam_id)

    cmdbuf = self.adaptor.getParser()
    cmdbuf.createMsgCommand(self.command["capture"], msgBuf)
    self.adaptor.send( cmdbuf.getEncodedDataCommand() )

    data = self.adaptor.recv_data(4, 2.0)
    if data :
      header, ssize = self.adaptor.getParser().unmarshal('HH')
      if header != 3:
        print "Invalid reply: ", header, ssize
        return None

      if ssize == 1:
        ssize = 230400 # 320x240x3
        colorType = 'RGB24'
        imgSize = '320x240'

      imgdata = self.adaptor.recv_data(ssize, 2.0)
      if imgdata is None or len(imgdata) != ssize :
        print len(imgdata)
        return None

      return ViewImage(imgdata, ViewImageInfo('WinBMP', colorType, imgSize))
    return None
  #
  #  Distance Sensor
  #
  def distanceSendor(self, start=0.0, end=255.0, camId=1, cType="GREY8"):
    self.sendDSRequest(0, start, end, camId, ctype)
    data = self.adaptor.recv_data(4, 2.0)
    if data :
      header, ssize = self.adaptor.getParser().unmarshal('HH')
      if header != 3:
        print "Invalid reply: ", header, ssize
        return None

      if ssize == 2:
        ssize = 1
      distdata = self.adaptor.recv_data(ssize, 2.0)
      if distdata is None or len(distdata) != ssize :
        return None

      return distdata[0]
    
    return None

  def distanceSendor1D(self, start=0.0, end=255.0, camId=1, cType="GREY8", imgSize="320x1"):
    self.sendDSRequest(1, start, end, camId, ctype)
    if data :
      header, ssize = self.adaptor.getParser().unmarshal('HH')
      if header != 3:
        print "Invalid reply: ", header, ssize
        return None

      if ssize == 3:
        ssize = 320
        cType = 'GREY8'
        imgSize = '320x1'

      imgdata = self.adaptor.recv_data(ssize, 2.0)
      if imgdata is None or len(imgdata) != ssize :
        print len(imgdata)
        return None

      return ViewImage(imgdata, ViewImageInfo('WinBMP', cType, imgSize))

    return None
 
  def distanceSendor2D(self, start=0.0, end=255.0, camId=1, cType="GREY8", imgSize="320x240"):
    self.sendDSRequest(2, start, end, camId, ctype)
    if data :
      header, ssize = self.adaptor.getParser().unmarshal('HH')
      if header != 3:
        print "Invalid reply: ", header, ssize
        return None

      if ssize == 4:
        ssize = 768000
        cType = 'GREY8'
        imgSize = '320x240'

      imgdata = self.adaptor.recv_data(ssize, 2.0)
      if imgdata is None or len(imgdata) != ssize :
        print len(imgdata)
        return None

      return ViewImage(imgdata, ViewImageInfo('WinBMP', cType, imgSize))

    return None

  def sendDSRequest(self, type, start, end, camId, ctypee):
    msgBuf = "%s,%d,%d,%f,%f," % (self.name, type, cam_id, start, end)

    cmdbuf = self.adaptor.getParser()
    cmdbuf.createMsgCommand(self.command["distance"], msgBuf)
    self.adaptor.send( cmdbuf.getEncodedDataCommand() )
    return
#
#
#
from PIL import Image
#import opencv

class ViewImage:
  def __init__(self, img, info):
    self.buffer=img
    self.info = info
    if info.type() == "L":
      self.image = Image.fromstring("L", info.size(), img, "raw", "L")
    else:
      self.image = Image.fromstring(info.type(), info.size(), img, "raw", "BGR")
    self.fov = 0.
    self.asprct_ratio = 4.0/3.0
    
  def getBuffer(self):
    return self.buffer

  def getBufferLength(self):
    return len(self.buffer)

  def saveAsWindowsBMP(self, fname):
    print "save file ....", fname
    self.image.save(fname)
    return

  def setBitImageAsWindowsBMP(self, bitImage):
    print "Not Implemented."
    return
    
  def getWidthBytes(self, w, bpp):
    res = w * bpp
    res += res % 4  #  Need?
    return res 
    
  def calcBufferSize(self, info):
    size=self.info.size()
    if size :
      return size[0] * size[1] * self.info.getByteParOnePixel()
    return 0
    
  def getViewImageInfo(self):
    return self.info

  def getWidth(self):
    return self.info.getWidth()

  def getHeight(self):
    return self.info.getHeight()

  def getFOVy(self):
    return self.fov

  def setFOVy(self, val):
    self.fov = val
    return

  def getFOVx(self):
    return math.atan(math.tan(self.fov * 0.5) * self.aspect_ratio) * 2.0

  def getAspectRatio(self):
    return self.aspect_ratio

  def setAspectRatio(self, val):
    self.aspect_ratio = val
    return 
#
#  ViewImageInfo:
#   original: 
#      color type(enum): COLORBIT_24, DEPTHBIT_8
#      image size(enum): IMAGE_320X240, IMAGE_320X1
#
#   This implementation:
#      color type(str): "RGB24", "RGB32", "GREY8"
#      image size(str): "320x240", "320x1"
#
class ViewImageInfo:
  def __init__(self, fmt, ctype, size):
    self.fmt=fmt
    self.colorType = ctype
    self.imageSize = size
    self.dataType = None
    
  def type(self):
    if self.colorType in ("RGB24", "COLORBIT_24"):
      return 'RGB'
    elif self.colorType in ("RGB32", "COLORBIT_32"):
      return 'RGBA'
    elif self.colorType in ("GREY8", "DEPTHBIT_8"):
      return 'L'
    else:
      print "ERROR: Invalid color type"
      return None

  def size(self):
    size = self.imageSize.split("x")
    if len(size) >= 2:
      return (int(size[0]), int(size[1]))
    else:
      print "ERROR: Invalid image size"
      return None

  def setDataType(self):
    return self.dataType

  def setColorBitType(self):
    return self.colorType

  def Width(self):
    return self.size()[0]

  def Height(self):
    return self.size()[1]

  def getByteParOnePixel(self):
    if self.colorType in ("RGB24", "COLORBIT_24"):
      return 3
    elif self.colorType in ("RGB32", "COLORBIT_32"):
      return 4
    elif self.colorType in ("GREY8", "DEPTHBIT_8"):
      return  1
    else:
      print "ERROR: Invalid color type"
      return 0

