#this is an interface to submit flags to the gameserver
from . import FlagOut
import socket

class Gameserver(FlagOut):
    def __init__(self, srv_addr, srv_port, timeout = None, maxsize = 0):
        QueueThread.__init__(maxsize)
        self.__srv_addr = srv_addr
        self.__srv_port = srv_port
        if(timeout == None):
            self.__timeout = socket.getdefaulttimeout()
        else
            self.__timeout = timeout
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def _open(self):
        self.__sock.connect((self.__srv_addr,self.__srv_port))
        #here could some "authentification" be added if needed

    def _close(self):
        #here can come some proper connection closing if needed
        self.__sock.close()

    def _process(self,flag):
        try
            self.__sock.send(flag)
        except Exception:
            self._open()
            #print "connection timed out; reconnected and retransmitting"
            try
                self.__sock.send(flag)
            except Exception, e:
                self.__sock.close()
            raise e
        return self.__sock.recv(1024)