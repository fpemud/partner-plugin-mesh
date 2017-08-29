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

        self.netPeerDict = dict()           # dict<hostname, _NetPeer>
        self.diskPeerDict = dict()          # dict<hostname, _DiskPeerData>
        self.netStandbyPeerSet = set()      # set<hostname>
        self._load()

        self.reflexDict = dict()            # dict<reflex-fullname, (reflex-property-dict, reflex-object)>

        self.apiServer = _ApiServer(self)

        self.opmWrtdAdvHost = OnlinePeerManagerWrtdAdvHost(self.logger,
                                                           self.apiServer.port,
                                                           self.on_net_peer_appear,
                                                           self.on_net_peer_disappear,
                                                           self.on_net_peer_wakeup_change)

    def dispose(self):
        self.opmWrtdAdvHost.close()
        self.apiServer.close()

    def get_good_reflexes(self, reflex_name, reflex_properties):
        if reflex_properties["role"] == "server":
            return [reflex_name]
        
        if reflex_properties["role"] in ["server-per-client", "p2p-endpoint"]:
            ret = []
            for peername in self.envObj.get_plugin_data("mesh")["peer-list"]:
                ret.append(reflex_name + "." + peername)
            return ret

        if reflex_properties["role"] == "client":
            ret = []
            for peername, peerdata in self.envObj.get_plugin_data("mesh")["peer-list"].items():
                for reflex_fullname, reflex_data in peerdata.["reflex-list"].items():
                    if reflex_data["protocol"] == reflex_properties["protocol"]:
                        if reflex_data["role"] == "server":
                            ret.append(reflex_name + "." + peername)
                        elif reflex_data["role"] == "server-per-client" and reflex_fullname == reflex_name + "." + socket.gethostname():
                            ret.append(reflex_name + "." + peername)
            return ret

    def reflex_pre_init(reflex_fullname, reflex_properties, obj):
        reflex_properties = reflex_properties.copy()
        reflex_properties.pop("knowledge")
        reflex_properties.pop("hint-in")
        reflex_properties.pop("hint-out")
        self.reflexDict[reflex_fullname] = (reflex_properties, obj)

        if reflex_properties["role"] in ["server-per-client", "p2p-endpoint", "client"]:
            peername = reflex_fullname.split(".")[1]
            obj.peer_info = {
                "hostname": peername,
                "ip": self.netPeerDict[peername],
            }
            obj.send_message_to_peer = lambda data: self._send_message(reflex_fullname, peername, data)
        else:
            obj.send_message_to_peer = lambda peername, data: self._send_message(reflex_fullname, peername, data)

    def reflex_post_fini(reflex_fullname, reflex_properties):
        del self.reflexDict[reflex_fullname]

    def on_net_peer_appear(self, hostname, ip, port, net_type, can_wakeup):
        if hostname in self.netStandbyPeerSet:
            self.netStandbyPeerSet.remove(hostname)
        self.netPeerDict[hostname] = _NetPeer(ip, port, net_type, can_wakeup)
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
        del self.diskPeerDict[hostname]prop2

    def on_peer_reflex_add(self, hostname, reflex_fullname, reflex_property_dict):
        self.envObj.get_plugin_data("mesh")["peer-list"][hostname]["reflex-list"][reflex_fullname] = reflex_property_dict
        self.envObj.changed()

    def on_peer_reflex_removed(self, hostname, reflex_fullname):
        del self.envObj.get_plugin_data("mesh")["peer-list"][hostname]["reflex-list"][reflex_fullname]
        self.envObj.changed()

    def on_peer_message_received(self, peername, reflex_fullname, data):
        reflex_properties = self.envObj.get_plugin_data("mesh")["peer-list"][hostname]["reflex-list"][reflex_fullname]

        fullname = self._match_reflex(peername, reflex_fullname, reflex_properties)
        if fullname is None:
            self.logger.warn("Reject message from non-exist reflex %s on peer %s." % (reflex_fullname, peername))
            return

        if self._reflex_split_fullname(fullname)[1] == "":
            self.reflexDict[fullname][1].on_receive_message_from_peer(peername, data)
        else:
            self.reflexDict[fullname][1].on_receive_message_from_peer(data)

    def _send_message(self, reflex_fullname, peername, data):
        data = {
            "app-message": {
                "source": reflex_fullname,
                "data": message,
            }
        }
        self.netPeerDict[peername].messageQueue.put(data)

    def _match_reflex(self, peername, reflex_fullname, reflex_properties):
        name, insname = _reflex_split_fullname(reflex_fullname)
        assert insname == socket.gethostname() if insname != "" else True

        for fullname2, value in self.reflexDict.items():
            name2, insname2 = _reflex_split_fullname(fullname2)
            prop2 = value[0]
            if self.__match(name, insname, reflex_properties, name2, insname2, prop2, peername)
                return fullname2
        return None

    def _match_peer_reflex(self, peername, reflex_fullname, reflex_properties):
        name, insname = _reflex_split_fullname(reflex_fullname)
        assert insname == peername if insname != "" else True

        for fullname2, prop2 in self.envObj.get_plugin_data("mesh")["peer-list"][peername]["reflex-list"].items():
            name2, insname2 = _reflex_split_fullname(fullname2)
            if self.__match(name, insname, reflex_properties, name2, insname2, prop2, socket.gethostname())
                return fullname2
        return None

    def __match(name, insname, prop, name2, insname2, prop2, hostname)
        if name2 != name:
            return False
        if insname2 != "" and insname2 != hostname:
            return False
        if prop2["protocol"] != prop["protocol"]:
            return False
        if prop2["role"] == "server" and prop["role"] == "client":
            return True
        if prop2["role"] == "server-per-client" and prop["role"] == "client":
            return True
        if prop2["role"] == "p2p-endpoint" and prop["role"] == "p2p-endpoint":
            return True
        if prop2["role"] == "client" and prop["role"] == "server":
            return True
        if prop2["role"] == "client" and prop["role"] == "server-per-client":
            return True
        return False

    def _load(self):
        pass

    def _save(self):
        pass


class _NetPeer(threading.Thread):

    def __init__(self, ip, port, net_type, can_wakeup):
        super().__init__()

        assert net_type in ["broadband", "narroband", "traffic-billing"]

        self.ip = ip
        self.port = port
        self.net_type = net_type
        self.can_wakeup = can_wakeup

        self.messageQueue = queue.Queue()
        self.sendThread = None
        self.bStop = False
        self.start()

    def dispose(self):
        self.bStop = True
        self.messageQueue.put(None)
        self.join()

    def run(self):
        while True:
            data = self.messageQueue.get()
            if data is None:
                return

            while True:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                try:
                    s.connect((self.ip, self.port))
                    s.send(json.dumps(data))
                    s.close()
                    s = None
                    break
                except socket.error:
                    if s is not None:
                        s.close()
                    for i in range(0, 10):
                        if bStop:
                            return
                        time.sleep(10)

            self.messageQueue.task_done()


class _DiskPeerData:

    def __init__(self, dev):
        self.dev = dev


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


def _reflex_make_fullname(name, instance_name):
    if instance_name == "":
        return name
    else:
        return name + "." + instance_name


def _reflex_split_fullname(fullname):
    tlist = fullname.split(".")
    if len(tlist) == 1:
        return (fullname, "")
    else:
        assert len(tlist) == 2
        return (tlist[0], tlist[1])


_flagError = GLib.IO_PRI | GLib.IO_ERR | GLib.IO_HUP | GLib.IO_NVAL
