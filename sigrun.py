#
#
#
import sys
import os
from optparse import OptionParser

if __name__ == "__main__" :
  parser = OptionParser()
  parser.add_option("", "--host", dest="hostname", default="localhost",
                     help="SIGVerse server name")
  parser.add_option("-p", "--port", dest="port", default="9000",
                    help="SIGVerse server port numer")
  parser.add_option("-n", "--name", dest="name", default="",
                    help="Robot name in SIGVerse server")
  parser.add_option("-f", "--file", dest="file", default="",
                    help="Controller filename")

  (options, args) = parser.parse_args()

  if not options.name  or not options.file:
    print "ERROR: Controlerfile and RobotName required"
    sys.exit()

  execfile(options.file) 

  ctrl=createController(options.name, options.hostname, int(options.port))
  ctrl.attach()
