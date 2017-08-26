#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import socket
import msghole
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

    def init2(self):
        self.netPeerDict = dict()           # dict<hostname, _NetPeerData>
        self.diskPeerDict = dict()          # dict<hostname, _DiskPeerData>
        self.netStandbyPeerSet = set()      # set<hostname>
        self.__load()

        self.apiServer = _ApiServer(self)
        self.opmWrtdAdvHost = OnlinePeerManagerWrtdAdvHost(self, self.apiServer.port)

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
