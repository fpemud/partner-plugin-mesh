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
