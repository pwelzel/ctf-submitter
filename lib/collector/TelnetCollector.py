from .Collector import Collector
from ..flag.TelnetFlag import TelnetFlag

import socket
import select
import argparse
from copy import copy

"""
documentation for TelnetCollector "API"
=======================================


OPTION fomat
------------
[?OPTION[=PARAM]] [?OPTION..]]


COMMAND format
--------------
[!COMMAND[=PARAM]] [?OPTION..]


FLAG input format
-----------------
[FLAG] [?OPTION..]

exact structure of FLAG depends on the CTF. in this version it is NOT checked by us!

if you give flag-specific options without prepended by a flag, they will be set for this session. they can be overwritten per-flag or for this session.


possible session options
------------------------
<long code> [ / <short code>] description
?verbose=   / ?V    verbose? (0,1)


possible commands
-----------------


possivle flag options
---------------------
?team=      / ?T    sets teamID
?service=   / ?S    sets serviceName



"""


class TelnetCollector(Collector):
    def __init__(self,flag_queue,bind_port,bind_addr):
        self._bind_addr = bind_addr
        self._bind_port = bind_port
        self._clients = []
        Collector.__init__(self,flag_queue,True)
        self._default_env = argparse.Namespace(verbose=True)
        self._clients_env = dict()
        self._init_argparser()

    def _init_argparser(self):
        self._argparser_opt = argparse.ArgumentParser(prefix_chars='?',add_help=False)
        self._argparser_opt.add_argument('?team','?T',nargs=1,type=int)
        self._argparser_opt.add_argument('?service','?S',nargs=1)
        self._argparser_opt.add_argument('?path',nargs=1)
        self._argparser_flag = argparse.ArgumentParser(prefix_chars='?', \
            parents=[self._argparser_opt],add_help=False)
        self._argparser_flag.add_argument('flag')
        self._argparser_cmd = argparse.ArgumentParser(prefix_chars='?',add_help=False)
        self._argparser_cmd.add_argument('command')

    def _cleanup(self):
        try:
            self._log("stops listening...")
            self._socket.close()
        except socket.error:
            pass

    def _cleanSetup(self, error=None):
        try:
            self._socket.close()
        except Exception:
            pass
        self._socket = socket.socket()
        self._socket.bind((self._bind_addr,self._bind_port))
        self._socket.listen(1)

    def _send(self,sock,msg,enc='UTF-8'):
        sock.send(bytes(msg,enc))

    def _proc_message(self,msg,sock):
        to_parse=msg
        if msg == '':
            self._send(sock,'.\n')
            return
        elif msg[0] == '!':
            parser = self._argparser_cmd
            to_parse=to_parse[1:]
        elif msg[0] == '?':
            parser = self._argparser_opt
        else:
            parser = self._argparser_flag

        try:
            parsed = parser.parse_known_args(to_parse.split(),copy(self._clients_env[sock]))
        except SystemExit as e:
            parsed=(argparse.Namespace(),to_parse.split())

        self._send(sock,"parsed: %s\n" % vars(parsed[0]))
        if parsed[1]:
            self._send(sock,"unknown/invalid arguments: %s\n" % parsed[1])
        elif msg[0] == '!':
            self._send(sock,"command execution not ready yet!\n")
        elif msg[0] == '?':
            self._clients_env[sock] = parsed[0]
            if self._clients_env[sock].verbose:
                self._send(sock,"options are now:\n%s\n"%vars(self._clients_env[sock]))
        else:
            flag = TelnetFlag(parsed[0].flag,sock,team=parsed[0].team)
            for q in self._flag_queue:
                q[0].put((flag,q[1:]))
            
    def _execute(self):
        read, write, oob = select.select([self._socket] + self._clients, [], [], 1)
        for sock in read:
            if sock is self._socket:
                client, addr = sock.accept()
                self._clients.append(client)
                self._clients_env[client] = copy(self._default_env)
                self._log("+++ client %s connected" % addr[0])
            else:
                try:
                    msg = sock.recv(1024)
                    ip = sock.getpeername()[0]
                    if msg:
                        msg = str(msg,encoding='UTF-8',errors='ignore').strip()
                        self._log("[%s] %s" % (ip, msg))
                        for s in msg.split("\n"):
                            self._proc_message(s,sock)
                    else:
                        self._log("--- client %s disconnected" % ip)
                        self._clients.remove(sock)
                        del self._clients_env[sock]
                        sock.close()
                except socket.error as er:
                    self._log("error with socket: %s" % er)
                    self._clients.remove(sock)

