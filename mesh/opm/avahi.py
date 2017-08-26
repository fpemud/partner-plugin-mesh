#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

class _PeerManagerAvahi:

    def __init__(self, param):
        self.param = param

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
