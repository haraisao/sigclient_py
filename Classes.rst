API List
===========

------------------------------------------------------------
sig.SigClient
-------------------
Descriptions
^^^^^^^^^^^^^^

Supers
^^^^^^^
   None

Variables
^^^^^^^^^^^^
    name = myname
    cmdAdaptor = None
    dataAdaptor = None
    cmdReader = SigCmdReader(self)
    dataReader = SigDataReader(self)
    srvReader = SigServiceReader(self)
    services = {}
    wait_for_reply = False
    self.server = host
    self.port = port


Methods
^^^^^^^^
* __init__( myname, host="localhost", port=9000):

* setServer( host, port):

* connect():

* sendCmd(msg):

* getAllSockets():

* waitForRequestSocket( timeout=0.1):

* setWaitForReply():

* finishReply():

* waitForReply():

* sendData( msg, flag=1):

* terminate():

* exit():



------------------------------------------------------------
sig.SigController
-------------------
Descriptions
^^^^^^^^^^^^^^

Supers
^^^^^^^
   sig.SigClient

Variables
^^^^^^^^^^
    cmdbuf = sigcomm.SigDataCommand()
    ec = None
    objs={}
    startSimTime = 0.0
    startTime = time.time()
    request_obj = False
    ecClass = sigcomm.SigControllerEC
    mutex=threading.Lock()
    chkServiceFlag = 0


Methods
^^^^^^^^
* __init__(self, name, host="localhost", port=9000, ecclass=None):

* getName():

* getMarshaller():

* setEC( ecclass):

* connect():

* attach():

* sendInit():

* checkRequest():

* waitForReply( timeout=10.0):

* setRequest( val):

* getObj( name=None, waitFlag=1):

* createSimObj( data):

* invokeOnCollision( data):

* sendMsg( to_name, msg, distance=-1.0):

* broadcastMsg( msg, distance=-1.0):

* broadcastMsgToSrv( msg):

* broadcastMsgToCtl( msg, distance=-1.0):

* broadcast( msg, distance, to):

* sendMessageAction( msgBuf):

* checkService( name):

* connectToService( name):

* setStartTime( tm):

* getCurrentTime():

* start()

* stop():

* onInit(evt):

* onAction(evt):

* onRecvMsg(evt):

* onCollision(evt):


------------------------------------------------------------
sig.SigSimObj
-------------------
Descriptions
^^^^^^^^^^^^^^


Supers
^^^^^^^
   None

Variables
^^^^^^^^^^
    cmdbuf = sigcomm.SigDataCommand()
    name=name
    parts = {}
    attributes = {}
    joints={}
    updateTime=0.0
    controller = ctrl

Methods
^^^^^^^^
  def __init__(self, name, ctrl):
  def getObj(self):
  def setAttributes(self, data):
  def getName(self):
  def setParts(self, data):
  def getParts(self, name):
  def dynamics(self):
  def getPosition(self):
  def setCurrentPosition(self, x, y, z):
  def setPosition(self, x, y, z):
  def updatePosition(self):
  def setCurrentRotation(self, qw, qx, qy, qz):
  def x(self, val=None):
  def y(self, val=None):
  def z(self, val=None):
  def getRotation(self):
  def setRotation(self, qw, qx, qy, qz, abs=1):
  def setAxisAndAngle(self, x, y, z, ang):
  def updateRotation(self):
  def qw(self, val=None):
  def qx(self, val=None):
  def qy(self, val=None):
  def qz(self, val=None):
  def setForce(self, fx, fy, fz):
  def addForce(self, dfx, dfy, dfz):
  def getMass(self):
  def setMass(self, val):
  def setAccel(self, ax, ay, az):
  def setTorque(self, x, y, z):
  def setJointAngle(self, joint_name, angle):
  def setJointQuaternion(self, joint_name, qw, qx, qy, qz, offset=0):
  def addJointTorque(self, joint_name, torque):
  def setJointVelocity(self, joint_name, vel, mx):
  def setAngularVelocityToJoint(self, joint_name, vel, mx):
  def setAngularVelocityToParts(self, name, vel, maxf) :
  def getAllJointAngles(self):
  def setWheelProperty(self, lname, lconsumption, lmax, lunit, lnoise, lres, lmaxf, 
                             rname, rconsumption, rmax, runit, rnoise, rres, rmaxf) :
  def setSimObjWheelProperty(self, objname, lname, lconsumption, lmax, lunit, lnoise, lres, lmaxf, 
                             rname, rconsumption, rmax, runit, rnoise, rres, rmaxf) :


------------------------------------------------------------
sig.SigServiceBase
-------------------
Descriptions
^^^^^^^^^^^^^^

Supers
^^^^^^^
   sig.SigServiceBase

Variables
^^^^^^^^^^
    name = ""
    owner = owner
    adaptor = None 

Methods
^^^^^^^^
* __init__(owner):

* setName(name):

* setAdaptor(adp):

* setEntityName(name):

------------------------------------------------------------
sig.ViewService
-------------------
Descriptions
^^^^^^^^^^^^^^

Supers
^^^^^^^
   sig.SigServiceBase

Variables
^^^^^^^^^^
    adaptor = adaptor 
    command={"capture":5, "distance":6, "detect": 7, }


Methods
^^^^^^^^
* __init__(self, owner, adaptor):

* detectEntities(self, cam_id):

* captureView(self, cam_id, colorType, imgSize):

* distanceSendor(self, start=0.0, end=255.0, camId=1, cType="GREY8"):

* distanceSendor1D(self, start=0.0, end=255.0, camId=1, cType="GREY8", imgSize="320x1"):

* distanceSendor2D(self, start=0.0, end=255.0, camId=1, cType="GREY8", imgSize="320x240"):

* sendDSRequest(self, type, start, end, camId, ctypee):


------------------------------------------------------------
sig.ViewImage
-------------------
Descriptions
^^^^^^^^^^^^^^

Supers
^^^^^^^
   None

Variables
^^^^^^^^^^
    buffer=img
    info = info
    image = Image.fromstring(...)
    fov = 0.
    asprct_ratio = 4.0/3.0

Methods
^^^^^^^^
* __init__(self, img, info):

* getBuffer(self):

* getBufferLength(self):

* saveAsWindowsBMP(self, fname):

* setBitImageAsWindowsBMP(self, bitImage):

* getWidthBytes(self, w, bpp):

* calcBufferSize(self, info):

* getViewImageInfo(self):

* getWidth(self):

* getHeight(self):

* getFOVy(self):

* setFOVy(self, val):

* getFOVx(self):

* getAspectRatio(self):

* setAspectRatio(self, val):


------------------------------------------------------------
sig.ViewImageInfo
-------------------
Descriptions
^^^^^^^^^^^^^^

Supers
^^^^^^^
   None

Variables
^^^^^^^^^^
    self.fmt=fmt
    self.colorType = ctype
    self.imageSize = size
    self.dataType = None

Methods
^^^^^^^^
* __init__(self, fmt, ctype, size):

* type(self):

* size(self):

* setDataType(self):

* setColorBitType(self):

* Width(self):

* Height(self):

* getByteParOnePixel(self):

* getImageSize(self):


------------------------------------------------------------
sigservice.SigService
------------------------
Descriptions
^^^^^^^^^^^^^^

Supers
^^^^^^^
   sig.SigClient

Variables
^^^^^^^^^^
    serverAdaptor = None
    viewerAdaptor = None
    controllers = {}
    entitiesName = []
    serviceList = []
    autoExitLoop = False
    autoExitProc = False
    onLoop = False
    ec = None
    ecClass = SigServiceEC

Methods
^^^^^^^
* setEC(ecclass):

* sendMsg(to_name, msg, distance=-1.0):

* sendMsgToCtrl(to_name, msg):

* send(msg, flag=1):

* connectToController(port, name):

* connect(host, port):

* disconnect():

* disconnectFromController(entryName):

* disconnectFromAllController():

* disconnectFromViewer():

* startLoop(intval= -1.0):

* stopLoop():

* connectToViewer(host="localhost", port=11000):

* getIsConnectedView():

* captureView( entryName, camID=1, cType="RGB24", imgSize="320x240"):

* distanceSensor( entryName, offset=0.0, range=255.0, camID=1):

* distanceSensor1D( entryName, offset=0.0, range=255.0, camID=1, cType="GREY8", imgSize="320x1"):

* distanceSensor2D( entryName, offset=0.0, range=255.0, camID=1, cType="GREY8", imgSize="320x240"):

* getDepthImage( entryName, offset=0.0, range=255.0, camID=1, dimension=2, cType="GREY8", imgSize="320x240"):

* getName():

* setName( name):

* getNewServiceNum():

* getAllOtherSerives():

* getAllConnectedEntitiesName():

* getControllerSocket( name):

* getConnectedControllerNum():

* setAutoExitLoop( flag):

* setAutoExitProc( flag):

* pushService( data):

* requestToConnect( data):

* requestToDisconnect( data):

* terminateService():

* onInit( evt):

* onRecvMsg( evt):

* onAction( evt):

