import sig

#############################
#
#  SigService

class SigServiceAdaptor(sig.SocketAdaptor):
  def __init__(self, reader, name, host, port):
    sig.SocketAdaptor.__init__(self, reader, name, host, port)


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
    return

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

  def recv(self, size, timeout=2.0):
    return self.serverAdaptor.recv_data(size, timeout)

  def processRequest(self, timeout=1.0):
    socks = self.waitForRequestSocket(timeout)
    for sock in socks:
      print sock
      self.recvRequestProc(sock)
    
  def recvRequestProc(self, sock=None):
    if sock is None:
      sock = self.serverAdaptor.socket

    data = sock.recv(4)
    if len(data) == 0:
      return -1
    print "Recieve"

    parser = self.serverAdaptor.getParser()   
    parser.printPacket(data)
    parser.setBuffer(data)
    cmd, size = parser.unmarshal('HH')
    size -= 4
    
    print "Cmd, size = %d, %d" % ( cmd, size )
    if size > 0:
      data = sock.recv(size)
      if len(data) != size:
        return 0
      else:
        self.processCmd(cmd, data, sock) 
        return 1

    return -2

  def processCmd(self, cmd, data, sock=None):
    if cmd == 0x0001 :
      print " call onRecvMsg()"
      evt=sig.SigMsgEvent(data)
      self.onRecvMsg(evt)
      pass

    elif cmd == 0x0002 :
      print "push service..",data
      self.serviceList.append(data)
      pass

    elif cmd == 0x0003 :
      print "request to connect controller.."
      parser = self.serverAdaptor.getParser()   
      parser.setBuffer(data)
      port, = parser.unmarshal('H')
      name = data[parser.offset:].split(',')[0]
      print "request to connect controller from %s:%d." % (name, port)
      self.controllers[name] = self.connectToController(port, name)
      pass

    elif cmd == 0x0004 :
      print "disconnect controller.."
      msg = data.split(",")
      ename = msg.pop(0)
      self.disconnectFromController(ename)
      del self.controllers[ename]
      pass

    elif cmd == 0x0005 :
      print "Terminate Service.."
      self.serverAdptor.terminate()
      if  self.autoExitProc :
        sys.exit(0)
      elif self.autoExitLoop :
        self.onLoop = False
      pass

    else:
      print "Invalid command..", cmd
      pass
    return 

  def connectToController(self, port, name):
    adaptor = SigServiceAdaptor(self.srvReader, self.name+":"+name, self.server, port)
    adaptor.connect(False)
    msg = '\x00\x01\x00\x04'
    adaptor.send(msg)
    return adaptor
    
  def connect(self, host, port):
    self.server = host 
    self.port = port 
    if self.serverAdaptor is None:
      self.serverAdaptor = SigServiceAdaptor(self.srvReader,self.name+":srv", host, port)
    res = self.serverAdaptor.connect(False)

    if res != 1:
      print "SigService: Fail to connect server [ %s:%d ]." % (host, port)
      return False

    self.send( "SIGMESSAGE,%s," % self.name )

    data = self.serverAdaptor.recieve_data()
    if data == -1 :
      print "SigService: Fail to connect server [ %s:%d ]." % (host, port)
    
    if data == "SUCC" :
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
    return

  def disconnectFromAllController(self):
    return

  def disconnectFromViewer(self):
    return

  def startLoop(self, intval= -1.0):
    return

  def checkRecvData(self, timeout):
    return

  def connectToViewer(self):
    return

  def captureView(self, entryName, camID=1, cType="RGB24", imgSize="320x240"):
    return None

  def distanceSensor(self, entryName, offset=0.0, range=255.0, camID=1):
    return None

  def distanceSensor1D(self, entryName, offset=0.0, range=255.0, camID=1, cType="GREY8", imgSize="320x1"):

    return None

  def distanceSensor2D(self, entryName, offset=0.0, range=255.0, camID=1, cType="GREY8", imgSize="320x240"):

    return None

  def getDepthImage(self, entryName, offset=0.0, range=255.0, camID=1, cType="GREY8", imgSize="320x240"):

    return None

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
    return None

  def getConnectedControllerNum(self):
    return len(self.controllers)

  def setAutoExitLoop(self, flag):
    self.autoExitLoop = flag
    return 

  def setAutoExitProc(self, flag):
    self.autoExitProc = flag
    return 

  def onInit(self, evt):
    return

  def onRecvMsg(self, evt):
    return

  def onAction(self, evt):
    return
