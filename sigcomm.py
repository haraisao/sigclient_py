#
#  Communication Adaptor for SIGVerse
#

import sys
import os
import socket
import select
import time
import threading
import struct


#
# Raw Socket Adaptor
#
class SocketAdaptor(threading.Thread):
  def __init__(self, reader, name, host, port):
    threading.Thread.__init__(self)
    self.reader = reader
    self.name = name
    self.host = host
    self.port = port
    self.socket = None
    self.mainloop = False
    self.debug = False

  #
  # Connect
  #
  def connect(self):
    if self.mainloop :
      return

    try:
      self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      self.socket.connect((self.host, self.port))

    except socket.error:
      print "Connection error"
      self.close()
      return 0
    except:
      print "Error in connect"
      self.close()
      return -1

    print "Start read thread"
    self.mainloop = True
    self.start()

    return 1

  def wait_for_read(self, timeout=0.1):
    try:
      rready, wready, xready = select.select([self.socket],[],[], timeout)

      if len(rready) : return 1
      return 0
    except:
      print "Error in wait_for_read"
      self.terminate()
      return -1

  #
  # Receive
  #
  def receive_data(self):
    data = None
    try:
      rready, wready, xready = select.select([self.socket],[],[], 1.0)

      if len(rready) :
        data = self.socket.recv(4096)  # buffer size = 1024
        if len(data) != 0:
          return data
        else:
          return  -1

    except socket.timeout:
      pass

    except socket.error:
      print "socket.error in recieve_data"
      self.terminate()

    except:
      print "Error in recieve_data"
      self.terminate()

    return data

  #  Background job ( message reciever )
  #
  def run(self):
    while self.mainloop:
      data = self.receive_data() 

      if data  == -1:
        self.terminate()
      elif data :
        self.reader.parse(data)

    print "Read thread terminated"
  #
  #
  def close(self):
    if self.socket :
      self.socket.close()
      self.socket = None
  #
  #  Stop background job
  #
  def terminate(self):
    self.mainloop = False
    self.close()
  #
  #  Send message
  #
  def send(self, name, msg):
    if not self.socket :
      print "Error: Not connected"
      return None

    try:
      self.socket.sendall(msg)
    except socket.error:
      print "Socket error in send"
      self.close()

#
#  Commands for SIGVerse
#
typeValue={
        'VALUE_TYPE_NOT_SET':-1,
        'VALUE_TYPE_STRING':0,
        'VALUE_TYPE_INT':1,
        'VALUE_TYPE_UINT':2,
        'VALUE_TYPE_LONG':3,
        'VALUE_TYPE_ULONG':4,
        'VALUE_TYPE_FLOAT':5,
        'VALUE_TYPE_DOUBLE':6,
        'VALUE_TYPE_BOOL':7,
        'VALUE_TYPE_NUM':8,
}

partType={
        'PARTS_TYPE_NOT_SET':-1,
        'PARTS_TYPE_BOX':0,
        'PARTS_TYPE_CYLINDER':1,
        'PARTS_TYPE_SPHERE':2,
        'PARTS_TYPE_NUM':3,
}

cmdType={
    'CMD_HEADER':0xabcd,
    'CMD_FOOTER':0xdcba,
    'SEND_MESSAGE':0x0001,
    'START_SIM':0x0002,
    'STOP_SIM':0x0003,
    'COMM_RESULT_OK':0,
    'COMM_RESULT_ERROR':1,
    'COMM_RESULT_NO_AGENT':2,
  }

cmdDataType={
        'COMM_DATA_TYPE_NOT_SET': -1,
        'COMM_REQUEST_SIM_CTRL': 0,
        'COMM_REQUEST_GET_ALL_ENTITIES': 1,
        'COMM_RESULT_GET_ALL_ENTITIES': 2,
        'COMM_REQUEST_GET_ENTITY':3,
        'COMM_RESULT_GET_ENTITY':4,
        'COMM_REQUEST_UPDATE_ENTITIES':5,
        'COMM_REQUEST_CAPTURE_VIEW_IMAGE':6,
        'COMM_RESULT_CAPTURE_VIEW_IMAGE':7,
        'COMM_REQUEST_DETECT_ENTITIES':8,
        'COMM_RESULT_DETECT_ENTITIES':9, 
        'COMM_REQUEST_ATTACH_CONTROLLER':10,
        'COMM_RESULT_ATTACH_CONTROLLER':11,
        'COMM_REQUEST_ATTACH_VIEW':12,
        'COMM_RESULT_ATTACH_VIEW':13,
        'COMM_REQUEST_CONNECT_DATA_PORT':14,
        'COMM_RESULT_CONNECT_DATA_PORT':15,
        'COMM_REQUEST_PROVIDE_SERVICE':16,
        'COMM_RESULT_PROVIDE_SERVICE':17,
        'COMM_REQUEST_GET_ATTRIBUTES':18,
        'COMM_RESULT_GET_ATTRIBUTES':19,
        'COMM_REQUEST_SET_ATTRIBUTES':20, 
        'COMM_REQUEST_SET_JOINT_ANGLE':21,
        'COMM_REQUEST_SOUND_RECOG':22,
        'COMM_RESULT_SOUND_RECOG':23,
        'COMM_REQUEST_CONNECT_JOINT':24,
        'COMM_REQUEST_RELEASE_JOINT':25,
        'COMM_REQUEST_GET_JOINT_FORCE':26,
        'COMM_RESULT_GET_JOINT_FORCE':27,
        'COMM_INVOKE_CONTROLLER_ON_INIT':28,
        'COMM_INVOKE_CONTROLLER_ON_ACTION':29,
        'COMM_INVOKE_CONTROLLER_ON_RECV_TEXT':30,
        'COMM_INVOKE_CONTROLLER_ON_RECV_SOUND':31,
        'COMM_INVOKE_CONTROLLER_ON_RECV_MESSAGE':32,
        'COMM_LOG_MSG':33,
        'COMM_CONTROLLER_COMMAND':34,
        'COMM_NS_QUERY_REQUEST':35,
        'COMM_NS_QUERY_RESULT':36,
        'COMM_NS_PINGER_REQUEST':37,
        'COMM_NS_PINGER_RESULT':38,
        'COMM_REQUEST_X3DDB':39,
        'COMM_RESULT_X3DDB':40,
        'COMM_REQUEST_GET_OBJECT_NAMES':41,
        'COMM_RESULT_GET_OBJECT_NAMES':42,
        'COMM_INVOKE_CONTROLLER_ON_COLLISION':43, 
        'COMM_REQUEST_SET_JOINT_QUATERNION':44,
        'COMM_REQUEST_ADD_JOINT_TORQUE':45,
        'COMM_REQUEST_SET_ANGULAR_VELOCITY_JOINT':46,
        'COMM_REQUEST_SET_ANGULAR_VELOCITY_PARTS':47,
        'COMM_REQUEST_GET_JOINT_ANGLE':48,
        'COMM_RESULT_GET_JOINT_ANGLE':49,
        'COMM_DISPLAY_TEXT':50,
        'COMM_REQUEST_DISTANCE_SENSOR':51,
        'COMM_RESULT_DISTANCE_SENSOR':52,
        'COMM_REQUEST_ADD_FORCE':53, 
        'COMM_REQUEST_ADD_FORCE_ATPOS':54,
        'COMM_REQUEST_ADD_FORCE_ATRELPOS':55,
        'COMM_REQUEST_SET_MASS':56,
        'COMM_REQUEST_GET_ANGULAR_VELOCITY':57,
        'COMM_RESULT_GET_ANGULAR_VELOCITY':58,
        'COMM_REQUEST_GET_LINEAR_VELOCITY':59,
        'COMM_RESULT_GET_LINEAR_VELOCITY':60,
        'COMM_REQUEST_ADD_FORCE_TOPARTS':61,
        'COMM_REQUEST_SET_GRAVITY_MODE':62,
        'COMM_REQUEST_GET_GRAVITY_MODE':53,
        'COMM_RESULT_GET_GRAVITY_MODE':64,
        'COMM_REQUEST_SET_DYNAMICS_MODE':65,
        'COMM_REQUEST_GET_POINTED_OBJECT':66,
        'COMM_RESULT_GET_POINTED_OBJECT':67,
        'COMM_REQUEST_SET_LINEAR_VELOCITY':68,
        'COMM_DATA_TYPE_NUM':69,

        'REQUEST_GET_ALL_ENTITIES_FIRST':1,
        'REQUEST_START_SIMULATION':2,
        'REQUEST_STOP_SIMULATION':3,
        'REQUEST_GET_MOVE_ENTITIES':4,
        'REQUEST_DOWNLOAD_SHAPE':5,
        'REQUEST_DISCONNECT':6,
        'REQUEST_QUIT':7,
        'REQUEST_SENDMSG_FROM_CONTROLLER':8,
        'REQUEST_CONNECT_SERVICE':9,
        'REQUEST_GET_JOINT_POSITION':11,
        'REQUEST_SET_JOINT_QUATERNION':12,
        'REQUEST_GET_POINTING_VECTOR':13,
        'REQUEST_GET_PARTS_POSITION':14,
        'REQUEST_SET_ENTITY_POSITION':15,
        'REQUEST_CHECK_SERVICE':16,
        'REQUEST_GET_ENTITY_POSITION':17,
        'REQUEST_SET_ENTITY_ROTATION':18,
        'REQUEST_GET_ENTITY_ROTATION':19,
        'REQUEST_CHECK_ENTITY':20,
        'REQUEST_SET_CAMERA_POSITION':21,
        'REQUEST_GET_CAMERA_POSITION':22,
        'REQUEST_SET_CAMERA_DIRECTION':23,
        'REQUEST_GET_CAMERA_DIRECTION':24,
        'REQUEST_SET_CAMERA_FOV':25,
        'REQUEST_SET_CAMERA_ASPECTRATIO':26,
        'REQUEST_SET_WHEEL':27,
        'REQUEST_SET_WHEEL_VELOCITY':28,
        'REQUEST_GET_JOINT_ANGLE':29,
        'REQUEST_SET_JOINT_VELOCITY':30,
        'REQUEST_GRASP_OBJECT':31,
        'REQUEST_RELEASE_OBJECT':32,
        'REQUEST_GET_ALL_JOINT_ANGLES':33,
        'REQUEST_WORLD_STEP':34,
        'REQUEST_WORLD_QUICK_STEP':35,
        'REQUEST_GET_ISGRASPED':36,
        'REQUEST_SET_COLLISIONABLE':37,
        'REQUEST_GET_SIMULATION_TIME':38,
        'REQUEST_GET_COLLISION_STATE':39,
        'REQUEST_SIZE':40, 

        }

#
#  Foundmental reader class for SIGVerse Communiction
#
class SigCommReader:
  def __init__(self, owner=None):
    self.buffer = ""
    self.bufsize = 0
    self.current=0
    self.owner = owner
    self.parser = SigDataCommand()
    self.mgsHandler = None
    self.dataHandler = None

  def parse(self, data):
    self.appendBuffer( data )

  def setOwner(self, owner):
    self.owner = owner

  def setBuffer(self, buffer):
    if self.buffer : del self.buffer
    self.buffer=buffer
    self.bufsize = len(buffer)
    self.current=0

  def appendBuffer(self, buffer):
    self.buffer += buffer
    self.bufsize = len(self.buffer)

  def printPacket(self, data):
    if data :
      for x in data:
        print "0x%02x" % ord(x), 
      print
    else:
      print "No command"

  def read(self, nBytes, delFlag=1):
    start = self.current
    end = start + nBytes

    if self.bufsize < end :
      end = self.bufsize

    data = self.buffer[start:end]
    self.current = end

    if  delFlag :
      self.buffer =  self.buffer[end:]
      self.current =  0
    return data

  def skipBuffer(self, n=4, flag=1):
    self.current += n
    if flag :
      self.buffer = self.buffer[self.current:]
      self.current = 0
    return 

  def clearBuffer(self):
    if self.buffer : del self.buffer
    self.buffer = ""
    self.current = 0

class SigMsgEvent: 
  def __init__(self, msg):
    self.allmessgae = msg
    self.sender = ""
    self.size = 0
    self.message = ""
    self.parse(msg)

  def parse(self, msg):
    pos1 = msg.find(',')
    self.sender = msg[:pos1]
    pos2 = msg.find(',', pos1+1)
    self.size = int(msg[pos1+1:pos2])
    self.message = msg[pos2+1:pos2+1+self.size]

  def getSender(self):
    return self.sender

  def getMsg(self):
    return self.message

#
#  Controoller base class for SIGVeerse
#    The custom cotroller should be inherit this class.
#
class SigControllerEC(threading.Thread):
  def __init__(self, ctrl, intval=1.0):
    threading.Thread.__init__(self)
    self.controller = ctrl
    self.mainloop = True
    self.interval = intval

  def run(self):
    self.controller.onInit(None)
    while self.mainloop:
      intval = self.controller.onAction(None)
      time.sleep(intval)

  def stop(self):
    self.mainloop = False
    print "Controller stopped"

#
# Marshal/Unmarshal command packet for SIGVerse
#
class SigCmdMarshaller:
  def __init__(self, buffer):
    self.buffer=buffer
    self.offset=0
    self.cmdheaderMarshaller=struct.Struct('!HH')
    self.cmdfooterMarshaller=struct.Struct('!H')

    self.bufsize = len(buffer)
    self.cmdsize = 0

    self.encbuf=None
    self.encpos=0

  def setBuffer(self, buffer):
    if self.buffer : del self.buffer
    self.buffer=buffer
    self.bufsize = len(buffer)
    self.offset=0

  def clearBuffer(self):
    if self.buffer : del self.buffer
    self.buffer=""
    self.bufsize=0
    self.offset=0

  def appendBuffer(self, buffer):
    self.buffer += buffer
    self.bufsize = len(self.buffer)

  def checkDataCommand(self, buffer, offset=0):
    bufsize = len(buffer)

    if bufsize - offset >= self.cmdheaderMarshaller.size:
      (cmd, size) = self.cmdheaderMarshaller.unpack_from(buffer, offset)

      if cmd == cmdType['CMD_HEADER'] :
        if size <= bufsize - offset:
          offset = offset + size  - self.cmdfooterMarshaller.size
          (footer,) = self.cmdfooterMarshaller.unpack_from(buffer, offset)

          if footer == cmdType['CMD_FOOTER'] :
            self.cmdsize = size - self.cmdheaderMarshaller.size - self.cmdfooterMarshaller.size
            return size
          else:
            print "Invalidl footer"
            self.cmdsize = 0
            return -2
        else:
          print "Short Packet %d/%d" % (bufsize, size)
          return 0

      else:
        self.cmdsize = 0
        return -1

    print "---> %d - %d <=%d" % ( bufsize, offset, self.cmdheaderMarshaller.size)
    return 0

  def checkMessageCommand(self, buffer, offset=0):
    (cmd,) =  struct.unpack_from('!H', buffer, offset)
    offset += struct.calcsize('!H')
    if cmd == cmdType['START_SIM'] : 
      offset += offset % 4
      (startTime,) =  struct.unpack_from('d', buffer, offset)
      return (cmd, startTime, offset+struct.calcsize('d'))

    elif cmd == cmdType['STOP_SIM'] : 
      return (cmd, offset)

    elif cmd == cmdType['SEND_MESSAGE'] : 
      (size,) =  struct.unpack_from('!H', buffer, offset)
      offset += struct.calcsize('!H')
      return (cmd, size, offset)

    return None

  def getCommand(self, buffer=None, offset=0):
    if buffer: self.buffer = buffer
    res =  self.checkDataCommand(self.buffer, offset)

    if res == 1:
      eoc = offset+self.cmdsize + self.cmdheaderMarshaller.size + self.cmdfooterMarshaller.size
      start = offset+ self.cmdheaderMarshaller.size
      end =  offset+ self.cmdheaderMarshaller.size + self.cmdsize
      cmd = self.buffer[start:end]
      self.buffer =  self.buffer[eoc:]
      self.offset =  0
      return cmd

    elif res == 0:
      return ''

    else:
      self.skipBuffer()
      return None

  def skipBuffer(self):
      print "call skipBuffer"
      return 

  def printPacket(self, data):
    for x in data:
      print "0x%02x" % ord(x), 
    print

  def unmarshalString(self, offset=-1):
    if offset < 0 : offset=self.offset
    try:
     (size,) =  struct.unpack_from('!I', self.buffer, offset)
     self.offset = offset + struct.calcsize('!I')
     if(size > 0):
       (str,) =  struct.unpack_from('!%ds' % (size), self.buffer, self.offset)
       self.offset += (1+(size / 4 )) * 4
       return str 
     else:
       return ""
    except:
      print "Error in parseCommand"
      return None

  def unmarshalNum(self, fmt, offset=-1):
    if offset < 0 : offset=self.offset
    try:
     (res,) =  struct.unpack_from(fmt, self.buffer, offset)
     self.offset = offset + struct.calcsize(fmt)
     return res
    except:
      print "Error in unmarshalNum"
      return None
     
  def unmarshalUShort(self, offset=-1):
    return self.unmarshalNum('!H', offset)
     
  def unmarshalUInt(self, offset=-1):
    return self.unmarshalNum('!I', offset)
     
  def unmarshalDouble(self, offset=-1):
    return self.unmarshalNum('d', offset)
     
  def unmarshalBool(self, offset=-1):
    if offset < 0 : offset=self.offset
    try:
     (res,) =  struct.unpack_from('B', self.buffer, offset)
     self.offset = offset + struct.calcsize('B')
     return res
    except:
      print "Error in unmarshalBool"
      return None
     
  def createCommand(self):
    self.encbuf=bytearray('\xab\xcd\x00\x06\xdc\xba')
    self.encpos=4 

  def setCommandSize(self):
    size = len(self.encbuf)
    struct.pack_into('!H', self.encbuf, 2, size)

  def getEncodedCommand(self):
    self.setCommandSize()
    return str(self.encbuf)

  def getEncodedDataCommand(self):
#    self.printPacket( str(self.encbuf[4:-2]) )
    return str(self.encbuf[4:-2])

  def clearEncodedCommand(self):
    if self.encbuf : del self.encbuf
    self.encbuf=None
    return

  def marshalNumericData(self, fmt, s):
    enc_code = bytearray( struct.calcsize(fmt))
    struct.pack_into(fmt, enc_code, 0, s)
    self.encbuf = self.encbuf[:-2]+enc_code+self.encbuf[-2:]
    self.encpos += struct.calcsize(fmt)

  def marshalUShort(self, s):
    self.marshalNumericData('!H', s)

  def marshalUInt(self, s):
    self.marshalNumericData('!I', s)

  def marshalDouble(self, d):
    self.marshalNumericData('d', d)

  def marshalString(self, str):
    size=len(str)
    if size > 0 :
      encsize = struct.calcsize('!I') + (1+size/4)*4
    else:
      encsize = struct.calcsize('!I')

    enc_code = bytearray( encsize )
    struct.pack_into('!I', enc_code, 0, size)

    if size > 0 :
      struct.pack_into('%ds' % (size,), enc_code, struct.calcsize('!I'), str)

    self.encbuf = self.encbuf[:-2]+enc_code+self.encbuf[-2:]
    self.encpos += encsize

  def copyString(self, str):
    size=len(str)
    enc_code = bytearray( size )

    struct.pack_into('%ds' % (size,), enc_code, 0, str)

    self.encbuf = self.encbuf[:-2]+enc_code+self.encbuf[-2:]
    self.encpos += size

#
#
#
class SigDataCommand(SigCmdMarshaller):
  def __init__(self, buffer=''):
    SigCmdMarshaller.__init__(self, buffer)
    self.headerMarshaller=struct.Struct('!HHHH') ## type, packetNum, seq, fowardFlags. 
    self.type = 0
    self.packetNum = 0
    self.seq = 0
    self.forwardFlag = 0
    self.forwardTo = ""
    self.reachRadius = -1

  def getHeader(self, data=None):
    try:
      if data :  self.setBuffer(data)
      (self.type, self.packetNum, self.seq, self.forwardFlags,) = self.headerMarshaller.unpack_from(self.buffer)
      self.offset += self.headerMarshaller.size
      self.forwardTo = self.unmarshalString()
      self.reachRadius = self.unmarshalDouble()
      return True
    except:
      print "Error in parseCommand"
      return False
   
  def setHeader(self, type, n=1, seq=0, flag=0, to='', radius=-1.0,name=None):
    if self.encbuf : del self.encbuf
    self.createCommand()
    self.marshalUShort(type)
    self.marshalUShort(n)
    self.marshalUShort(seq)
    self.marshalUShort(flag)
    self.marshalString(to)
    self.marshalDouble(radius)
    if not name is None:
      self.marshalString(name)

  def printHeader(self):
    print "Cmd %d" % (self.type)
    print "Num %d" % (self.packetNum)
    print "Seq %d" % (self.seq)
    print "Radius %d" % (self.reachRadius)
    if self.forwardFlags :
      print "Forward %s" % (self.forwardTo)
 

