#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-


###############################################################################
# reflex-property-dict:
#     "mesh-peer-role": "server" OR "client" OR "p2p-endpoint"
###############################################################################
def get_properties(name):
    # returns plugin-property-dict
    assert False


class ReflexObject:

    @property
    def peer_info(self):
        # returns {
        #     "hostname": HOSTNAME,
        #     "ip": IP-ADDRESS,
        #     "uid": USER-ID,
        # }

    def on_receive_message_from_peer(self, message):
        assert False

    def send_message_to_peer(self, message):
        assert False


# the above template is for both system reflex and user reflex
