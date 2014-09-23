#
#
#
import sys
import os
#import struct
import time
import threading
import sigcomm
import sig

#############################
#
#  SigService

class SigServiceAdaptor(sigcomm.SocketAdaptor):
  def __init__(self, owner, reader, name, host, port):
    sigcomm.SocketAdaptor.__init__(self, reader, name, host, port)
    self.parser=sigcomm.SigSrvCommand()
    self.owner=owner
    self.buffer=""
    self.recieve_size = 0

  def clear_buffer(self):
    self.buffer = ""
    self.recieve_size = 0

  def recv(self,size):
    self.clear_buffer()
    ssize = size
    while ssize > 0:
      ssize = size - len(self.buffer)
      data = self.recieve_data(ssize)

      if data == -1:
        print "Error in SigServiceAdaptor.recv", ssize
        return None
      elif data is None:
        pass
      else:
        self.buffer += data
	if len(self.buffer) >= size :
          break
    print "RECV:",len(self.buffer)
    return self.buffer

  def message_reciever(self):
    while self.mainloop:
      try:
        if self.recieve_size == 0 :
          data = self.socket.recv(4)
          if len(data) != 4:
            self.terminate()

#          cmd, size = struct.unpack_from('!HH', data)
          cmd, size = self.parser.parseCommand(data)
          self.recieve_size = size - self.parser.getCommandLength()
          print "Cmd, size = %d, %d" % ( cmd, size )

        if self.recieve_size > 0:
          self.buffer += self.socket.recv(self.recieve_size - len(self.buffer))

          if len(self.buffer) != self.recieve_size:
            pass
          else:
            self.processCmd(cmd, self.buffer) 
            self.clear_buffer()
      except:
        print "Catch exception... :",self.name
        self.terminate()

    print "Read thread terminated:",self.name
    return 
     
  def processCmd(self, cmd, data):
    if cmd == 0x0001 :
      thr = threading.Thread(target=sig.runOnRecvMsg, args=(self.owner, data))    
      thr.start()
      pass

    elif cmd == 0x0002 :
      print "push service..",data
      self.owner.pushService(data)
      pass

    elif cmd == 0x0003 :
      print "request to connect controller.."
      self.owner.requestToConnect(data)
      pass

    elif cmd == 0x0004 :
      print "disconnect controller.."
      self.owner.requestToDisconnect(data)
      pass

    elif cmd == 0x0005 :
      print "Terminate Service.."
      self.terminate()
      self.owner.terminateService()
      pass

    else:
      print "Invalid command..", cmd
      pass
    return 

#
#    SigClient <--- SigService
#
class SigService(sig.SigClient):
  def __init__(self, name):
    sig.SigClient.__init__(self, name, "localhost", 9000)
    self.serverAdaptor = None
    self.viewerAdaptor = None
    self.controllers = {}
    self.entitiesName = []
    self.serviceList = []
    self.autoExitLoop = False
    self.autoExitProc = False
    self.onLoop = False
    self.ec = None
    self.setEC(None)
    return

  #
  #  set Execution Context
  #
  def setEC(self, ecclass):
    if ecclass :
      self.ecClass = ecclass
    else:
      self.ecClass = SigServiceEC
  #
  #
  #
  def getAllSockets(self):
    res = []
    if self.serverAdaptor :
      res.append(self.serverAdaptor.socket)
    if self.viewerAdaptor :
      res.append(self.viewerAdaptor.socket)
    for x in self.controllers.values():
      res.append(x.socket)
    return res
    
  #
  #
  #
  def sendMsg(self, to_name, msg, distance=-1.0):
    if type(to_name) == types.StringType:
      msgBuf = "%.5d,%s,%f,1,%s,"  % (len(msg), msg, distance, to_name)

    elif type(to_name) in (types.ListType, types.TupleType):
      msgBuf = "%.5d,%s,%f,%d,%s, "  % (len(msg), msg, distance, len(to_name), ','.to_name)

    else:
      print "[ERR} invalid to_name", to_name
      return
   
    msgLen = "%.5d" % (len(msgBuf) + 5)
    msgBuf = msgLen + msgBuf   
    self.send(msgBuf)
    return

  def sendMsgToCtrl(self, to_name, msg):
    if to_name in self.controllers.keys():
      adaptor = self.controllers[to_name]
      cmdbuf = adaptor.getParser()
      cmdbuf.createMsgCommand(self.name, 0x0002, msg)
      msg = cmdbuf.getEncodedDataCommand()
      adaptor.send(msg)
      return True
    else:
      pass
    return False

  def send(self, msg, flag=1):
    self.serverAdaptor.send(msg, self.name)

  def connectToController(self, port, name):
    adaptor = SigServiceAdaptor(self, self.srvReader, self.name+":"+name, self.server, port)
    adaptor.connect()
    msg = '\x00\x01\x00\x04'
    adaptor.send(msg)
    return adaptor
    
  def connect(self, host, port):
    self.server = host 
    self.port = port 
    if self.serverAdaptor is None:
      self.serverAdaptor = SigServiceAdaptor(self, self.srvReader,self.name+":srv", host, port)
    res = self.serverAdaptor.connect(False)

    if res != 1:
      print "SigService: Fail to connect server [ %s:%d ]." % (host, port)
      return False

    self.send( "SIGMESSAGE,%s," % self.name )

    data = self.serverAdaptor.recieve_data()
    if data == -1 :
      print "SigService: Fail to connect server [ %s:%d ]." % (host, port)
    
    if data == "SUCC" :
      self.serverAdaptor.start()
      return True
    elif data == "FAIL" :
      print "SigService: Service name '%s' is already exist." % (host, port)
    else :
      print "SigService: Unkown reply, ", data

    return False

  def disconnect(self):
    self.send("00004")
    return

  def disconnectFromController(self, entryName):
    cmdbuf = sigcomm.SigMarshaller()
    cmdbuf.createCommand()
    cmdbuf.marshal('H', 0x0004, 2)
    msg = cmdbuf.getEncodedDataCommand()
    self.controllers[entryName].send(msg)

    self.controllers[entryName].terminate()
    del self.controllers[entryName]
    return

  def disconnectFromAllController(self):
    names = self.controllers.keys()
    for name in names:
      self.disconnectFromController(name)
    return

  def disconnectFromViewer(self):
    return

  def startLoop(self, intval= -1.0):
    if self.ec is None:
      self.ec = self.ecClass(self)
      self.startTime=time.time()
      self.ec.start()
    return

  def stopLoop(self):
    if self.ec :
      self.ec.stop()
      self.ec = None

  def checkRecvData(self, timeout):
    print "checkReccvData doesn't implement."
    return

############################  Not implemented yet....
  def connectToViewer(self):
    host = "localhost"
    port = 11000
    if self.viewerAdaptor is None:
      self.viewerAdaptor = SigServiceAdaptor(self, self.srvReader,self.name+":viewer", host, port)
    res = self.viewerAdaptor.connect(False)

    if res != 1:
      print "SigService: Fail to connect viewer [ %s:%d ]." % (host, port)
      self.viewerAdaptor = None
      return False

    cmdbuf = sigcomm.SigMarshaller("")
    cmdbuf.createMsgCommand(0x0000, self.name)
    msg = cmdbuf.getEncodedDataCommand()
    self.viewerAdaptor.send(msg)
    return

  def captureView(self, entryName, camID=1, cType="RGB24", imgSize="320x240"):
    view = None
    if self.viewerAdaptor:
      imgsize = 320 * 240 * 3
      msg="%s,%d,%d," % (entryName, camID, imgsize)
      cmdbuf=sigcomm.SigMarshaller("")
      cmdbuf.createMsgCommand(0x0001, msg)
      self.viewerAdaptor.send(cmdbuf.getEncodedDataCommand())

      headerBuf = self.viewerAdaptor.recv(cmdbuf.calcsize("Hdd"))
      cmdbuf.setBuffer(headerBuf)
      res, fov, ar = cmdbuf.unmarshal('Hdd')

      if res == 2:
        print "Error in captureView: cannot find entry",entryName
      elif res == 3:
        print "Error in captureView: doesn't have such camera [%s:%d]" % (entryName, camID)
      else:
        imgdata=self.viewerAdaptor.recv(imgsize)
        vinfo = sig.ViewImageInfo("WinBMP", cType, imgSize)
	view = sig.ViewImage(imgdata, vinfo)
        view.setFOVy(fov)
        view.setAspectRatio(ar)
    else:
      print "Error in captureView: Service isn't connected to viewer"

    return view

  def distanceSensor(self, entryName, offset=0.0, range=255.0, camID=1):
    return None

  def distanceSensor1D(self, entryName, offset=0.0, range=255.0, camID=1, cType="GREY8", imgSize="320x1"):

    return None

  def distanceSensor2D(self, entryName, offset=0.0, range=255.0, camID=1, cType="GREY8", imgSize="320x240"):

    return None

  def getDepthImage(self, entryName, offset=0.0, range=255.0, camID=1, cType="GREY8", imgSize="320x240"):

    return None

############################
  def getName(self):
    return self.name

  def setName(self, name):
    self.name = name
    return 

  def getNewServiceNum(self):
    return len(self.serviceList)

  def getAllOtherSerives(self):
    return self.serviceList

  def getAllConnectedEntitiesName(self):
    return self.entitiesName

  def getControllerSocket(self, name):
    return self.controllers[name].socket

  def getConnectedControllerNum(self):
    return len(self.controllers)

  def setAutoExitLoop(self, flag):
    self.autoExitLoop = flag
    return 

  def setAutoExitProc(self, flag):
    self.autoExitProc = flag
    return 

  def pushService(self, data):
    self.serviceList.append(data)
    return 

  def requestToConnect(self, data):
    parser = sig.SigSrvCommand(data)
#    parser.setBuffer(data)
    port, = parser.unmarshal('H')
#    port, = struct.unpack_from('!H', data)
    name = data[parser.offset:].split(',')[0]
#    name = data[2:].split(',')[0]
    print "request to connect controller from %s:%d." % (name, port)
    self.controllers[name] = self.connectToController(port, name)
    return 

  def requestToDisconnect(self, data):
    msg = data.split(",")
    ename = msg.pop(0)
    self.disconnectFromController(ename)
    del self.controllers[ename]
    return 

  def terminateService(self):
    if  self.autoExitProc :
      self.stopLoop()
      sys.exit(0)
    elif self.autoExitLoop :
      self.stopLoop()

    return

  def onInit(self, evt):
    print "Call onInit"
    return

  def onRecvMsg(self, evt):
    print "onRecvMsg", evt.getMsg()
    return

  def onAction(self, evt):
    print "Call onAction"
    return 1.0
#
#
#
class SigServiceEC(threading.Thread):
  def __init__(self, srv, intval=1.0):
    threading.Thread.__init__(self)
    self.service = srv
    self.mainloop = True
    self.interval = intval

  def run(self):
    self.service.onInit(None)
    while self.mainloop:
      intval = self.service.onAction(None)
      time.sleep(intval)

  def stop(self):
    self.mainloop = False
    print "SigServiceEC stopped"
