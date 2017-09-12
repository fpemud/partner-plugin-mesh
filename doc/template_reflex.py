#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-


###############################################################################
# reflex-property-dict:
#     "protocol": PROTOCOL-NAME
#     "role": "server" OR "p2p"
#             "server-per-client" OR "client" OR "p2p-per-peer"
###############################################################################
def get_properties(name, plugin_name=None):
    # returns plugin-property-dict
    assert False


class ReflexObjectServer:

    @property
    def my_hostname(self):
        assert False

    @property
    def peer_info(self):
        # returns [
        #     {   "hostname": HOSTNAME,
        #         "ip": IP-ADDRESS,
        #         "uid": USER-ID,
        #     },
        #     {   "hostname": HOSTNAME,
        #         "ip": IP-ADDRESS,
        #         "uid": USER-ID,
        #     },
        # ]
        assert False

    def on_peer_appear(self, peer_hostname, peer_ip, peer_uid):
        assert False

    def on_peer_disappear(self, peer_hostname):
        assert False

    def send_message_to_peer(self, peer_hostname, message):
        assert False

    def on_receive_message_from_peer(self, peer_hostname, message):
        assert False

    def get_file_from_peer(self, peer_hostname, peer_filename):
        # returns job-id
        assert False

    def on_get_file_from_peer_complete(self, peer_hostname, job_id, file_content):
        assert False

    def on_get_file_from_peer_error(self, peer_hostname, job_id, excp):
        assert False

    def pull_file_from_peer(self, peer_hostname, peer_filename, local_filename):
        # returns job-id
        assert False

    def on_pull_file_from_peer_complete(self, peer_hostname, job_id):
        assert False

    def on_pull_file_from_peer_error(self, peer_hostname, job_id, excp):
        assert False

    def pull_directory_from_peer(self, peer_hostname, peer_dirname, local_dirname, exclude_pattern=None, include_pattern=None):
        # returns job-id
        assert False

    def on_pull_directory_from_peer_complete(self, peer_hostname, job_id):
        assert False

    def on_pull_directory_from_peer_error(self, peer_hostname, job_id, excp):
        assert False


class ReflexObjectP2p:
    # same as ReflexObjectServer
    pass


class ReflexObjectServerPerClient:

    @property
    def my_hostname(self):
        assert False

    @property
    def peer_info(self):
        # returns {
        #     "hostname": HOSTNAME,
        #     "ip": IP-ADDRESS,
        #     "uid": USER-ID,
        # }
        assert False

    def on_receive_message_from_peer(self, message):
        assert False

    def send_message_to_peer(self, message):
        assert False

    def get_file_from_peer(self, peer_filename):
        # returns job-id
        assert False

    def on_get_file_from_peer_complete(self, job_id, file_content):
        assert False

    def on_get_file_from_peer_error(self, job_id, excp):
        assert False

    def pull_file_from_peer(self, peer_filename, local_filename):
        # returns job-id
        assert False

    def on_pull_file_from_peer_complete(self, job_id):
        assert False

    def on_pull_file_from_peer_error(self, job_id, excp):
        assert False

    def pull_directory_from_peer(self, peer_dirname, local_dirname, exclude_pattern=None, include_pattern=None):
        # returns job-id
        assert False

    def on_pull_directory_from_peer_complete(self, job_id):
        assert False

    def on_pull_directory_from_peer_error(self, job_id, excp):
        assert False


class ReflexObjectServerPerClient:
    # same as ReflexObjectServerPerClient
    pass


class ReflexObjectP2pPerPeer:
    # same as ReflexObjectServerPerClient
    pass


# the above template is for both system reflex and user reflex
