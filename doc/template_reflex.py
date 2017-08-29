#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-


###############################################################################
# reflex-property-dict:
#     "protocol": PROTOCOL-NAME
#     "role": "server" OR "server-per-client" OR "client" OR "p2p-endpoint"
###############################################################################
def get_properties(name, plugin_name=None):
    # returns plugin-property-dict
    assert False


class ReflexObjectServer:

    @property
    def my_hostname(self):
        assert False

    def on_receive_message_from_peer(self, peer_hostname, message):
        assert False

    def send_message_to_peer(self, peer_hostname, message):
        assert False


class ReflexObjectServerPerClient:

    @property
    def peer_info(self):
        # returns {
        #     "hostname": HOSTNAME,
        #     "ip": IP-ADDRESS,
        #     "uid": USER-ID,
        # }

    @property
    def my_hostname(self):
        assert False

    def on_receive_message_from_peer(self, message):
        assert False

    def send_message_to_peer(self, message):
        assert False


class ReflexObjectServerPerClient:
    # same as ReflexObjectServerPerClient
    pass


class ReflexObjectP2pEndpoint:
    # same as ReflexObjectServerPerClient
    pass


# the above template is for both system reflex and user reflex
