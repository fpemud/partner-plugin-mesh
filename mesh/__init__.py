#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import json
import logging
import socket
from gi.repository import Gio
from gi.repository import GObject
from .opm.wrtd_advhost import OnlinePeerManagerWrtdAdvHost


def get_plugin_list():
    return [
        "mesh",
    ]


def get_plugin_properties(name):
    if name == "mesh":
        return dict()
    else:
        assert False


def get_plugin_object(name):
    if name == "mesh":
        return _PluginObject()
    else:
        assert False


class _PluginObject:

    def init2(self, reflex_environment):
        self.logger = logging.getLogger(self.__module__ + "." + self.__class__.__name__)

        self.envObj = reflex_environment
        self.envObj.get_plugin_data("mesh") = {
            "peer-list": {},
        }

        self.netPeerDict = dict()           # dict<hostname, _NetPeerData>
        self.diskPeerDict = dict()          # dict<hostname, _DiskPeerData>
        self.netStandbyPeerSet = set()      # set<hostname>
        self._load()

        self.apiServer = _ApiServer(self)

        self.opmWrtdAdvHost = OnlinePeerManagerWrtdAdvHost(self.logger,
                                                           self.apiServer.port,
                                                           self.on_net_peer_appear,
                                                           self.on_net_peer_disappear,
                                                           self.on_net_peer_wakeup_change)

    def dispose(self):
        self.opmWrtdAdvHost.close()
        self.apiServer.close()

    def reflex_pre_init(fullname, properties, obj):
        assert False

    def reflex_post_fini(fullname, properties, obj):
        assert False

    def on_net_peer_appear(self, hostname, ip, port, net_type, can_wakeup):
        if hostname in self.netStandbyPeerSet:
            self.netStandbyPeerSet.remove(hostname)
        self.netPeerDict[hostname] = _NetPeerData(ip, port, net_type, can_wakeup)
        self._save()

        self.envObj.get_plugin_data("mesh")["peer-list"][hostname] = {
            "reflex-list": dict()
        }
        self.envObj.changed()

    def on_net_peer_disappear(self, hostname):
        if self.netPeerDict[hostname].can_wakeup:
            self.netStandbyPeerSet.add(hostname)
        del self.netPeerDict[hostname]
        self._save()

        del self.envObj.get_plugin_data("mesh")["peer-list"][hostname]
        self.envObj.changed()

    def on_net_peer_wakeup_change(self, hostname, value):
        self.netPeerDict[hostname].can_wakeup = value
        self._save()

    def on_disk_peer_appear(self, hostname, dev):
        self.diskPeerDict[hostname] = _DiskPeerData(dev)

    def on_disk_peer_disappear(self, hostname):
        del self.diskPeerDict[hostname]

    def on_peer_reflex_add(self, hostname, reflex_fullname, reflex_property_dict):
        self.envObj.get_plugin_data("mesh")["peer-list"][hostname]["reflex-list"][reflex_fullname] = reflex_property_dict
        self.envObj.changed()

    def on_peer_reflex_removed(self, hostname, reflex_fullname):
        del self.envObj.get_plugin_data("mesh")["peer-list"][hostname]["reflex-list"][reflex_fullname]
        self.envObj.changed()

    def on_peer_message_received(self, hostname, reflex_fullname, message):
        pass

    def _load(self):
        pass

    def _save(self):
        pass


class _NetPeerData:

    def __init__(self, ip, port, net_type, can_wakeup):
        assert net_type in ["broadband", "narroband", "traffic-billing"]

        self.ip = ip
        self.port = port
        self.net_type = net_type
        self.can_wakeup = can_wakeup
        self.reflexDict = dict()


class _DiskPeerData:

    def __init__(self, dev):
        self.dev = dev
        self.reflexDict = dict()


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
        data = json.loads(buf)

        hostname = None
        for hostname2, data in self.pObj.netPeerDict.items():
            if data.ip == src_ip:
                hostname = hostname2
                break
        if hostname is None:
            raise Exception("invalid message received from %s" % (src_ip))

        if "reflex-add" in data:
            for fullname, propDict in data["reflex-add"].items():
                self.pObj.on_peer_reflex_add(hostname, fullname, propDict)
            return

        if "reflex-remove" in data:
            for fullname in data["reflex-remove"]:
                self.pObj.on_peer_reflex_remove(hostname, fullname)
            return
        
        if "app-message" in data:
            self.pObj.on_peer_message_received(hostname, data["source"], data["data"])
            return

        raise Exception("invalid message received")


_flagError = GLib.IO_PRI | GLib.IO_ERR | GLib.IO_HUP | GLib.IO_NVAL
