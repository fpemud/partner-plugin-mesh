#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-


class OnlinePeerManagerWrtdAdvHost(msghole.EndPoint):

    def __init__(self, logger, myPort, appearFunc, disappearFunc, setWakeupFunc):
        super().__init__()

        self.logger = self.logger
        self.appearFunc = appearFunc
        self.disappearFunc = disappearFunc

        self.advhostApiPort = 2222
        self.advhostRetryTimeout = 3600

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
            self.sc.connect_to_host_async(AssUtil.getGatewayIpAddress(), self.advhostApiPort, None, self.on_connect)
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
            super().exec_command("get-host-list",
                                 return_callback=self.on_command_get_host_list_return,
                                 error_callback=self.on_command_get_host_list_error)
        except:
            self.logger.error("Failed to establish WRTD-ADVHOST connection", exc_info=True)
            self._closeAndRestart()

    def on_command_get_host_list_return(self, data):
        for ip, data2 in data.items():
            if "hostname" in data2 and "service-partner" in data2:
                port, net_type, can_wakeup = self.__data2info(data2)
                self.appearFunc(data2["hostname"], ip, port, net_type, can_wakeup)
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
                self.appearFunc(data2["hostname"], ip, port, net_type, can_wakeup)
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
                self.disappearFunc(hostname)
            elif not ok1 and ok2:
                port, net_type, can_wakeup = self.__data2info(data2)
                self.appearFunc(hostname2, ip, port, net_type, can_wakeup)
            else:
                if hostname1 != hostname2 or port1 != port2:
                    self.disappearFunc(hostname1)
                    port, net_type, can_wakeup = self.__data2info(data2)
                    self.appearFunc_channel_net(hostname2, ip, port, net_type, can_wakeup)
                else:
                    if ("can-wakeup" in self.clientDict[ip]) != ("can-wakeup" in data2[ip]):
                        can_wakeup = "can-wakeup" in data2
                        self.setWakeupFunc(hostname2, can_wakeup)

    def on_notification_host_remove(self, data):
        for ip in data:
            if "hostname" in self.clientDict[ip] and "service-partner" in self.clientDict[ip]:
                self.disappearFunc(self.clientDict[ip]["hostname"])
            del self.clientDict[ip]

    def on_notification_network_list_change(self, data):
        pass

    def _closeAndRestart(self):
        assert self.connectTimer is None
        for ip, data2 in self.clientDict:
            if "hostname" in data2 and "service-partner" in data2:
                self.disappearFunc(data2["hostname"])
        self.clientDict.clear()
        self.close()
        self.connectTimer = GObject.timeout_add_seconds(self.advhostRetryTimeout, self.on_start)
