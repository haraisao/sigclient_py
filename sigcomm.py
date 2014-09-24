#
#  SIGVerse Client Library
#  Communication Adaptor for SIGVerse
#
#   Copyright(C) 2014, Isao Hara, AIST
#   Release under the MIT License.
#

import sys
import os
import socket
import select
import time
import threading
import struct
import copy
#from sig import *

#
# Raw Socket Adaptor
#
#   threading.Tread <--- SocketAdaptor
#
class SocketAdaptor(threading.Thread):
  def __init__(self, reader, name, host, port):
    threading.Thread.__init__(self)
    self.reader = reader
    self.name = name
    self.host = host
    self.port = port
    self.socket = None
    self.service = []
    self.service_id = 0
    self.client_adaptor = True
    self.mainloop = False
    self.debug = False
  #
  #
  #
  def setHost(self, name):
    self.host = name
    return 

  def setPort(self, port):
    self.port = port
    return 

  def setClientMode(self):
    self.client_adaptor = True
    return 

  def setServerMode(self):
    self.client_adaptor = False
    return 
  #
  # Bind
  #
  def bind(self):
    try:
      self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      self.socket.bind((self.host, self.port))

    except socket.error:
      print "Connection error"
      self.close()
      return 0
    except:
      print "Error in connect " , self.host, self.port
      self.close()
      return -1

    return 1

  #
  # Connect
  #
  def connect(self, async=True):
    if self.mainloop :
      return 1

    try:
      self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      self.socket.connect((self.host, self.port))

    except socket.error:
      print "Connection error"
      self.close()
      return 0

    except:
      print "Error in connect " , self.host, self.port
      self.close()
      return -1

    if async :
      print "Start read thread ",self.name
      self.start()

    return 1

  #
  #  Wait for comming data...
  #
  def wait_for_read(self, timeout=0.1):
    try:
      rready, wready, xready = select.select([self.socket],[],[], timeout)

      if len(rready) :
#        print "Ready to read:",self.name
        return 1
      return 0
    except:
      print "Error in wait_for_read"
      self.terminate()
      return -1

  #
  # Receive
  #
  def recieve_data(self, bufsize=8192, timeout=1.0):
    data = None
    try:
      if self.wait_for_read(timeout) == 1  :
        data = self.socket.recv(bufsize)     # buffer size = 1024 * 8
        if len(data) != 0:
          return data
        else:
          return  -1

    except socket.error:
      print "socket.error in recieve_data"
      self.terminate()

    except:
      print "Error in recieve_data"
      self.terminate()

    return data

  def recv_data(self, bufsize=1024, timeout=1.0):
    while True:
      data = self.recieve_data(bufsize, timeout)

      if data is None or data == -1:
        self.reader.clearBuffer()
        return None

      else :
        self.reader.appendBuffer(data)
        if self.reader.bufsize >= bufsize :
          data1 = self.reader.read(bufsize, 1)
          self.reader.parser.setBuffer(data1)
          return data1
        else:
#          print  "Size %d, %d" % (self.reader.bufsize, bufsize )
          pass
      
    return None
    
  #
  #
  #
  def getParser(self):
    return self.reader.parser
  #
  #  Thread oprations...
  #
  def start(self):
    self.mainloop = True
    threading.Thread.start(self)

  def run(self):
    if self.client_adaptor: 
      self.message_reciever()
    else:
      self.accept_service_loop()

  #
  # Backgrount job (server side)
  #
  def accept_service(self, flag=True):
    try:
      conn, addr = self.socket.accept()
      self.service_id += 1
#      print "Accept: ", addr
      name = self.name+":service:%d" % self.service_id
      reader = copy.copy(self.reader)
      newadaptor = SocketAdaptor(self.reader, name, addr[0], addr[1])
      newadaptor.socket = conn
      self.service.append(newadaptor)
      if flag :
        newadaptor.start()
      return newadaptor
    except:
      print "ERROR in accept_service"
      pass
    return None

  def wait_accept_service(self, timeout=5, runflag=True):
    print "Wait for accept %d sec.: %s(%s:%d)" % (timeout, self.name, self.host, self.port)
    self.socket.listen(1)
    res = self.wait_for_read(timeout) 
    if res == 1:
      return self.accept_service(runflag)
    else:
      pass 
    return None

  def accept_service_loop(self, lno=5, timeout=1.0):
    print "Wait for accept: %s(%s:%d)" % (self.name, self.host, self.port)
    self.socket.listen(lno)
    while self.mainloop:
      res = self.wait_for_read(timeout) 
      if res == 1:
        self.accept_service()
      elif res == -1:
        self.terminate()
      else:
        pass
    
    print "Terminate all service %s(%s:%d)" % (self.name, self.host, self.port)
    self.close_service()
    self.close()
    return 
  #
  #  Background job ( message reciever )
  #
  def message_reciever(self):
    while self.mainloop:
      data = self.recieve_data() 

      if data  == -1:
        self.terminate()

      elif data :
        self.reader.parse(data)

      elif data is None :
        pass

      else :
        print "Umm...:",self.name
        print data

    print "Read thread terminated:",self.name

  #
  #  close socket
  #
  def close_service(self):
    for s in  self.service :
      s.terminate()

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
  def send(self, msg, name=None):
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
  def __init__(self, owner=None, parser=None):
    self.buffer = ""
    self.bufsize = 0
    self.current=0
    self.owner = owner
    if parser is None:
      self.parser = SigMarshaller('')
    else:
      self.parser = parser
 
    self.mgsHandler = None
    self.dataHandler = None
    if owner is None:
      self.debug = True
    else:
      self.debug = False

  #
  #  parse recieved data, called by SocketAdaptor
  #
  def parse(self, data):
    if self.debug:
      print data
    self.appendBuffer( data )

  #
  #  Usually 'owner' is a controller
  #
  def setOwner(self, owner):
    self.owner = owner

  #
  #  Buffer
  #
  def setBuffer(self, buffer):
    if self.buffer : del self.buffer
    self.buffer=buffer
    self.bufsize = len(buffer)
    self.current=0

  def appendBuffer(self, buffer):
    self.buffer += buffer
    self.bufsize = len(self.buffer)

  def skipBuffer(self, n=4, flag=1):
    self.current += n
    if flag :
      self.buffer = self.buffer[self.current:]
      self.current = 0
    return 

  def clearBuffer(self, n=0):
    if n > 0 :
#      self.printPacket( self.buffer[:n] )
      self.buffer = self.buffer[n:]
      self.current = 0
    else:
      if self.buffer : del self.buffer
      self.buffer = ""
      self.current = 0

  def checkBuffer(self):
    try:
      h_pos = self.buffer.find('\xab\xcd', self.current)
      f_pos = self.buffer.find('\xdc\xba', self.current)

      if h_pos < 0 and f_pos >= 0:
         self.buffer=self.buffer[f_pos+2:]
         self.current = 0

      if len(self.buffer) > self.current :
        res = self.parser.checkDataCommand(self.buffer, self.current)
        if res > 0:
          return True

        elif res == -1:
          res = self.parser.checkMessageCommand(self.buffer, self.current)
          if res :
            return True

        self.buffer = self.buffer[self.current:]
        self.current = 0
    except:
      print "ERR in checkBuffer"
      self.printPacket(self.buffer)
      self.buffer=""
      pass

    return False
     

  #
  #  extract data from self.buffer 
  #
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

  #
  # print buffer (for debug)
  #
  def printPacket(self, data):
    if self.parser:
      self.parser.printPacket(data)
#
#  Controoller base class for SIGVeerse
#    The custom cotroller should be inherit this class.
#
#   threading.Tread <--- SigController
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
class SigMarshaller:
  def __init__(self, buffer):
    self.buffer=buffer
    self.bufsize = len(buffer)

    self.offset=0
    self.cmdsize = 0

    self.cmdheaderMarshaller=struct.Struct('!HH')
    self.cmdfooterMarshaller=struct.Struct('!H')
    self.encbuf=None
    self.encpos=0

    self.cmd_header='\xab\xcd\x00\x00'
    self.cmd_footer='\xdc\xba'

  #
  #  for buffer
  #
  def setBuffer(self, buffer):
    if self.buffer : del self.buffer
    self.buffer=buffer
    self.bufsize = len(buffer)
    self.offset=0

  def clearBuffer(self):
    self.setBuffer("")

  def appendBuffer(self, buffer):
    self.buffer += buffer
    self.bufsize = len(self.buffer)

  #
  #  check command format...  (0xabcd size_of_message encoded_command 0xdcba)
  #
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
            print "#Invalidl footer"
            self.cmdsize = 0
            return -2
        else:
#          print "Short Packet %d/%d" % (bufsize, size)
          return 0

      else:
        self.cmdsize = 0
        return -1

    print "---> %d - %d <=%d" % ( bufsize, offset, self.cmdheaderMarshaller.size)
    return 0
  #
  # extract command from buffer
  #
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

  #
  #  skip buffer, but not implemented....
  #
  def skipBuffer(self):
      print "call skipBuffer"
      return 
  #
  #  check message format (cmd encoded_args)
  #
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

  #
  #  print buffer for debug
  #
  def printPacket(self, data):
    for x in data:
      print "0x%02x" % ord(x), 
    print

  #
  #  dencoding data
  # 
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
    return self.unmarshalNum('B', offset)

  def unmarshal(self, fmt):
    res=[]
    for x in fmt:
      if x in ('i', 'h', 'I', 'H'):
        res.append(self.unmarshalNum('!'+x))
      elif x in ('d', 'B'):
        res.append(self.unmarshalNum(x))
      elif x == 'S':
        res.append(self.unmarshalString())
    return res

  #  generate command
  #
  def createCommand(self):
    self.encbuf=bytearray()
    self.encpos=0 

  def setCommandSize(self):
    size = len(self.encbuf)
    struct.pack_into('!H', self.encbuf, 2, size)

  def getEncodedCommand(self):
    self.encbuf = self.cmd_header + self.encbuf + self.cmd_footer
    self.setCommandSize()
    return str(self.encbuf)

  def getEncodedDataCommand(self):
    return str(self.encbuf)

  def clearEncodedCommand(self):
    if self.encbuf : del self.encbuf
    self.encbuf=None
    return
  #
  #  encoding data
  # 
  def marshalNumericData(self, fmt, s):
    enc_code = bytearray( struct.calcsize(fmt))
    struct.pack_into(fmt, enc_code, 0, s)
    self.encbuf = self.encbuf+enc_code
    self.encpos += struct.calcsize(fmt)

  def marshalUShort(self, s):
    self.marshalNumericData('!H', s)

  def marshalUInt(self, s):
    self.marshalNumericData('!I', s)

  def marshalDouble(self, d):
    self.marshalNumericData('d', d)

  def marshalBool(self, d):
    if d :
      self.marshalNumericData('B', 1)
    else :
      self.marshalNumericData('B', 0)

  def marshalString(self, str, with_size=1):
    size=len(str)

    if with_size :
      if size > 0 :
        enc_size = struct.calcsize('!I') + (1+size/4)*4
      else:
        enc_size = struct.calcsize('!I')

      enc_code = bytearray( enc_size )
      struct.pack_into('!I', enc_code, 0, size)
      offlen = struct.calcsize('!I')
    else:
      enc_size = size
      offlen = 0
      enc_code = bytearray( enc_size )

    if size > 0 :
      struct.pack_into('%ds' % (size,), enc_code, offlen, str)

    self.encbuf = self.encbuf+enc_code
    self.encpos += enc_size

  def marshal(self, fmt, *data):
    pos = 0
    for x in fmt:
      if x in ('i', 'h', 'I', 'H'):
        self.marshalNumericData('!'+x, data[pos])
      elif x in ('d', 'B'):
        self.marshalNumericData(x, data[pos])
      elif x == 'S':
        self.marshalString(data[pos])
      elif x == 's':
        self.marshalString(data[pos], 0)
      pos += 1
    return 

  def createMsgCommand(self, cmd, msgBuf, *opt):
    if type(cmd).__name__ == 'str' :
      cmd = cmdDataType[cmd]
    self.createCommand()
    size = len(msgBuf) + struct.calcsize("HH")
    if len(opt) > 0:
      for x in opt:
        size = size + struct.calcsize(x[0])

      self.marshal('HH', cmd, size)
      for x in opt:
        self.marshal(x[0], x[1])
      self.marshal('s', msgBuf)
    else:
      self.marshal('HHs', cmd, size, msgBuf)

  def calcsize(self, fmt):
    res = 0
    for x in fmt:
      if x in ('i', 'h', 'I', 'H', 'd', 'B'):
        res += struct.calcsize(x)
      else:
        print "Unsupported format:",x
    return res

#
#  marshalling command 
#     SigMarshaller <--- SigDataCommand
#
class SigDataCommand(SigMarshaller):
  def __init__(self, buffer=''):
    SigMarshaller.__init__(self, buffer)

    self.headerMarshaller=struct.Struct('!HHHH') ## type, packetNum, seq, fowardFlags. 
    self.type = 0
    self.packetNum = 0
    self.seq = 0
    self.forwardFlag = 0
    self.forwardTo = ""
    self.reachRadius = -1

  #
  # for Header
  #  (type, num_of_packet, sequence_No., foward_flag, forwarding_address, radius_to_reach_msg)
  #
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
   
  def setHeader(self, typ=0, n=1, seq=0, flag=0, to='', radius=-1.0,name=None):
    if type(typ).__name__ == 'str' :
      typ = cmdDataType[typ]
    if self.encbuf : del self.encbuf
    self.createCommand()
    self.marshalUShort(typ)
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
 
  #
  #  extract remains from the buffer
  #
  def getRemains(self, size=-1):
    remainsLen = self.remainsSize()
    if size > 0 :
      if remainsLen >= size:
        res = self.buffer[self.offset:self.offset+size]
        self.offset += size
        self.buffer = self.buffer[self.offset:]
        self.bufsize = len(self.buffer)
        return res
      else:
        return None
    else:
      return self.buffer[self.offset:]

  def remainsSize(self):
    return len(self.buffer[self.offset:])

#
#  marshalling command 
#     SigMarshaller <--- SigSrvCommand
#
class SigSrvCommand(SigDataCommand):
  def __init__(self, buffer=''):
    SigDataCommand.__init__(self, buffer)

  def createMsgCommand(self, sender, cmd, msg):
    msgBuf="%s,%d,%s" % (sender, len(msg), msg)
    self.createCommand()
    size = len(msgBuf) + struct.calcsize("HH")
    self.marshal('HHs', cmd, size, msgBuf)

  def parseCommand(self, data):
    self.setBuffer(data)
    return self.unmarshal('HH')

  def getCommandLength(self):
    return struct.calcsize("HH")
#
# Events
#

#
#  Message Event ( sender, size, message, )
#
class SigMsgEvent: 
  def __init__(self, msg):
    self.allmessgae = msg
    self.sender = ""
    self.size = 0
    self.message = ""
    self.parse(msg)

  def parse(self, msg):
    try:
      pos1 = msg.find(',')
      self.sender = msg[:pos1]
      pos2 = msg.find(',', pos1+1)
      self.size = int(msg[pos1+1:pos2])
      self.message = msg[pos2+1:pos2+1+self.size]
    except:
      print "Invalid Message[%d]: %s." % (len(msg), msg)
      self.size = 0
      self.message = ""
     

  def getSender(self):
    return self.sender

  def getMsg(self):
    return self.message

  def setData(self, data, size):
    data_ar = data.split(',')
    self.sender = data_ar.pop(0)
    self.size = int(data_ar.pop(0))
    self.message = ','.join(data_ar)
    return 
#
#
#  Collision Event
#     SigMarshaller <--- SigCollisionEvent
#
class SigCollisionEvent(SigMarshaller):
  def __init__(self, data):
    SigMarshaller.__init__(self, data)
    self.withVals = []
    self.withParts = []
    self.myParts = []
 
  def parse(self):
    currentTime=self.unmarshalDouble() 
    num_of_with=self.unmarshalUShort() 
    for i in range(num_of_with):
      str_with = self.unmarshalString()
      with_val, with_part, my_part, sp = str_with.split(":")
      self.withVals.append(with_val)
      self.withParts.append(with_part)
      self.myParts.append(my_part)
    return 

  def getWith(self):
    return self.withVals

  def getWithParts(self):
    return self.withParts

  def getMyParts(self):
    return self.myParts

