#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import socket
from util import Util
from util import FlexObject


class _ApiServer:

    def __init__(self, pObj):
        self.pObj = pObj
        self.logger = self.pObj.logger
        self.port = Util.getFreeSocketPort("tcp")

        self.serverSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverSock.bind(('0.0.0.0', self.port))
        self.serverSock.listen(5)
        self.serverSock.setblocking(0)
        self.serverSourceId = GLib.io_add_watch(self.serverSock, GLib.IO_IN | _flagError, self.on_accept)

        self.sockDict = dict()

    def on_accept(self, source, cb_condition):
        try:
            assert not (cb_condition & _flagError)
            assert source == self.serverSock

            new_sock, addr = self.serverSock.accept()
            for p in self.pObj.netPeerDict.values():
                if addr[0] == p.ip:
                    obj = FlexObject()
                    obj.buf = bytes()
                    obj.watch = GLib.io_add_watch(new_sock, GLib.IO_IN | _flagError, self.on_recv)
                    self.sockDict[new_sock] = obj
                    return True

            new_sock.close()
            self.logger.error("%s is not a peer, reject." % (addr[0]))
            return True
        except:
            self.logger.error("Error occured in accept callback.", exc_info=True)
            return True

    def on_recv(self, source, cb_condition):
        try:
            assert source in self.sockDict

            if cb_condition & _flagError:
                source.close()
                del self.sockDict[source]
                return False

            buf2 = source.recv(4096)
            if len(buf2) == 0:
                self._sendMessageToApplication(source.get_peer_address()[0], self.sockDict[source].buf)
                source.close()
                del self.sockDict[source]
                return False

            self.sockDict[source].buf += buf2
            return True
        except:
            self.logger.error("Error occured in receive callback", exc_info=True)
            return True

    def _sendMessageToApplication(self, src_ip, buf):
        pass


    def on_peer_reflex_add(self, reflex_name, reflex_property_dict):
        pass

    def on_peer_reflex_removed(self, reflex_name):
        pass

    def on_peer_message_received(self, hostname, message):
        pass





_flagError = GLib.IO_PRI | GLib.IO_ERR | GLib.IO_HUP | GLib.IO_NVAL
