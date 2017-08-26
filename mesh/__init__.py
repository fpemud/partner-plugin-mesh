#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import socket
import msghole
from gi.repository import Gio
from gi.repository import GObject


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

    def init2(self):
        self.netPeerDict = dict()           # dict<hostname, _NetPeerData>
        self.diskPeerDict = dict()          # dict<hostname, _DiskPeerData>
        self.netStandbyPeerSet = set()      # set<hostname>
        self.__load()

        self.apiServer = _ApiServer(self)
        self.opmWrtdAdvHost = _OnlinePeerManagerWrtdAdvHost(self, self.apiServer.port)

    def dispose(self):
        pass

    def add_api_for_reflex(reflex_object):
        pass



    def _netPeerAppear(self, hostname, ip, port, net_type, can_wakeup):
        if hostname in self.netStandbyPeerSet:
            self.netStandbyPeerSet.remove(hostname)
        self.netPeerDict[hostname] = _NetPeerData(ip, port, net_type, can_wakeup)
        self.__save()

    def _netPeerDisappear(self, hostname):
        if self.netPeerDict[hostname].can_wakeup:
            self.netStandbyPeerSet.add(hostname)
        del self.netPeerDict[hostname]
        self.__save()

    def _netPeerSetWakeup(self, hostname, value):
        self.netPeerDict[hostname].can_wakeup = value
        self.__save()

    def _diskPeerAppear(self, hostname, dev):
        self.diskPeerDict[hostname] = _DiskPeerData(dev)

    def _diskPeerDisappear(self, hostname):
        del self.diskPeerDict[hostname]

    def __load(self):
        pass

    def __save(self):
        pass


class _NetPeerData:

    def __init__(self, ip, port, net_type, can_wakeup):
        assert net_type in ["broadband", "narroband", "traffic-billing"]

        self.ip = ip
        self.port = port
        self.net_type = net_type
        self.can_wakeup = can_wakeup


class _DiskPeerData:

    def __init__(self, dev):
        self.dev = dev





class _OnlinePeerManagerWrtdAdvHost(msghole.EndPoint):

    def __init__(self, pObj, myPort):
        super().__init__()

        self.pObj = pObj
        self.logger = self.pObj.logger
        self.apiPort = 2222
        self.retryTimeout = 3600

        self.sc = Gio.SocketClient.new()
        self.sc.set_family(Gio.SocketFamily.IPV4)
        self.sc.set_protocol(Gio.SocketProtocol.TCP)

        self.connectTimer = GObject.timeout_add_seconds(0, self.on_start)
        self.clientDict = dict()

    def dispose(self):
        self.clientDict.clear()
        if self.connectTimer is not None:
            GLib.source_remove(self.connectTimer)
        self.close()

    def on_start(self):
        try:
            self.logger.info("Establishing WRTD-ADVHOST connection.")
            self.sc.connect_to_host_async(AssUtil.getGatewayIpAddress(), self.apiPort, None, self.on_connect)
        except:
            self.logger.error("Failed to establish WRTD-ADVHOST connection", exc_info=True)
            self._closeAndRestart()
        finally:
            return False

    def on_connect(self, source_object, res):
        try:
            self.connectTimer = None
            conn = source_object.connect_to_host_finish(res)
            super().set_iostream_and_start(conn)
            self.logger.info("WRTD-ADVHOST connection established.")
            super().exec_command("get-host-list", self.on_command_get_host_list_return, self.on_command_get_host_list_error)
        except:
            self.logger.error("Failed to establish WRTD-ADVHOST connection", exc_info=True)
            self._closeAndRestart()

    def on_command_get_host_list_return(self, data):
        for ip, data2 in data.items():
            if "hostname" in data2 and "service-partner" in data2:
                port, net_type, can_wakeup = self.__data2info(data2)
                self.pObj._netPeerAppear(data2["hostname"], ip, port, net_type, can_wakeup)
        self.clientDict.update(data)

    def on_command_get_host_list_error(self, reason):
        self.logger.error("Command \"get-host-list\" error.", exc_info=True)
        self._closeAndRestart()

    def on_error(self, excp):
        self.logger.error("WRTD-ADVHOST connection disconnected with error.", exc_info=True)
        self._closeAndRestart()

    def on_close(self):
        pass

    def on_notification_host_add(self, data):
        for ip, data2 in data.items():
            if "hostname" in data2 and "service-partner" in data2:
                port, net_type, can_wakeup = self.__data2info(data2)
                self.pObj._netPeerAppear(data2["hostname"], ip, port, net_type, can_wakeup)
        self.clientDict.update(data)

    def on_notification_host_change(self, data):
        for ip, data2 in data.items():
            hostname1 = self.clientDict[ip].get("hostname", None)
            hostname2 = data2.get("hostname", None)
            port1 = self.clientDict[ip].get("service-partner", None)
            port2 = data2.get("service-partner", None)
            ok1 = hostname1 is not None and port1 is not None
            ok2 = hostname2 is not None and port2 is not None
            if not ok1 and not ok2:
                pass
            elif ok1 and not ok2:
                self.pObj._peer_disappear(hostname)
            elif not ok1 and ok2:
                port, net_type, can_wakeup = self.__data2info(data2)
                self.pObj._netPeerAppear(hostname2, ip, port, net_type, can_wakeup)
            else:
                if hostname1 != hostname2 or port1 != port2:
                    self.pObj._peer_disappear(hostname1)
                    port, net_type, can_wakeup = self.__data2info(data2)
                    self.pObj._netPeerAppear_channel_net(hostname2, ip, port, net_type, can_wakeup)
                else:
                    if ("can-wakeup" in self.clientDict[ip]) != ("can-wakeup" in data2[ip]):
                        can_wakeup = "can-wakeup" in data2
                        self.pObj._netPeerSetWakeup(hostname2, can_wakeup)

    def on_notification_host_remove(self, data):
        for ip in data:
            if "hostname" in self.clientDict[ip] and "service-partner" in self.clientDict[ip]:
                self.pObj._netPeerDisappear(self.clientDict[ip]["hostname"])
            del self.clientDict[ip]

    def on_notification_network_list_change(self, data):
        pass

    def _closeAndRestart(self):
        assert self.connectTimer is None
        for ip, data2 in self.clientDict:
            if "hostname" in data2 and "service-partner" in data2:
                self.pObj._netPeerDisappear(data2["hostname"])
        self.clientDict.clear()
        self.close()
        self.connectTimer = GObject.timeout_add_seconds(self.retryTimeout, self.on_start)

    def __data2info(data):
        port = data["service-partner"]
        net_type = "narrowband" if "through-vpn" in data else "broadband"
        can_wakeup = "can-wakeup" in data
        return (port, net_type, can_wakeup)


class _PeerManagerAvahi:

    def __init__(self, param):
        self.param = param


class _PeerManagerStatic:

    def __init__(self, pObj):
        self.staticPeerList = []
        fn = os.path.join(self.pObj.param.etcDir, "staic-peers")
        if os.path.exists(fn):
            with open(fn, "r") as f:
                for line in f.read().split("\n"):
                    if line.strip() == "":
                        continue
                    if line.startswith("#"):
                        continue
                    self.staticPeerList.append(line.strip())

        self.refreshTimer = GObject.timeout_add_seconds(0, self._refreshTimerCallback)

    def _refreshTimerCallback(self):
        return False


_flagError = GLib.IO_PRI | GLib.IO_ERR | GLib.IO_HUP | GLib.IO_NVAL
