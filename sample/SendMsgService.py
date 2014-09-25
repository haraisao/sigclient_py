#! /usr/bin/python

from sigservice import *

if __name__ == "__main__" :
  srv = SigService("MyService")
  srv.connect("localhost", 9000)
  srv.sendMsg("robot_000", "Hello!!")
  srv.disconnect()

