#this is an interface to submit flags to the gameserver
from .Submitter import Submitter
import socket

class Gameserver(Submitter):
    def __init__(self, srv_addr, srv_port, maxsize = 0):
        self._srv_addr = srv_addr
        self._srv_port = srv_port
        self._sock = None
        Submitter.__init__(self,maxsize)

    def __del__(self):
        self._close()

    def _cleanSetup(self,error=None):
        self._close()
        self._open()

    def _open(self,option=None):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.connect((self._srv_addr,self._srv_port))
        #here could some "authentification" be added if needed

    def _close(self,option=None):
        #here can come some proper connection closing if needed
        try:
            self._sock.close()
        except Exception:
            pass

    def _send(self,string):
        self._sock.send(bytes(string,'UTF-8'))

    def _proc_flag(self,flag):
        try:
            self._send(flag.flag)
        except Exception:
            self._cleanSetup()
            try:
                self._send(flag.flag)
            except Exception as e:
                self._sock.close()
                print("exception: %s"% e)
                return None
        return str(self._sock.recv(1024),encoding='UTF-8',errors='ignore').strip()