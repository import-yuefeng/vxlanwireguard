import binascii
import errno
import random
import sys
from typing import List
import argparse
from . import common


def vw_del(args: argparse.Namespace) -> int:
    network_name = args.interface[0]
    # config = common.Config()

    # if not config.load(network_name):
    #     print("vwgen: Unable to find configuration file '{}.conf'".format(
    #         network_name),
    #           file=sys.stderr)
    #     return errno.ENOENT
    config = args.config
    network = config.network()
    nodes = config.nodes()
    blacklist = config.blacklist()
    config.save()

    return_value = 0

    for node_name in args.nodes:
        if node_name not in nodes:
            print("vwgen: Network '{}' does not have node '{}'".format(
                network_name, node_name),
                  file=sys.stderr)
            return_value = return_value or errno.ENOENT
            continue
        del nodes[node_name]

        for i in blacklist:
            if node_name in i:
                blacklist.remove(i)

    config.save()
    config.close()
    return return_value
