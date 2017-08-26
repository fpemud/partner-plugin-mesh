#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

class _PeerManagerStatic:

    def __init__(self, pObj):
        self.staticPeerList = []
        fn = os.path.join(self.pObj.param.etcDir, "staic-peers")
        if os.path.exists(fn):