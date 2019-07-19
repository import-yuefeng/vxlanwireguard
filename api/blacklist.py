import binascii
import errno
import ipaddress
import random
import sys
from typing import cast, List, Optional, Set, Tuple
from . import common
import argparse


def vw_blacklist(args: argparse.Namespace) -> int:

    network_name = args.interface[0]
    # config = common.Config()
    # config.load(network_name)
    config = args.config
    network = config.network()
    nodes = config.nodes()
    blacklist = config.blacklist()
    config.save()

    operation: Optional[bool] = None
    if args.operate == "add":
        operation = True
    elif args.operate == "del":
        operation = False
    else:
        print("vwgen: Invalid operation '{}'".format(args.operate))
        return errno.EINVAL

    return_value = 0

    left_node = args.left_node
    if left_node not in nodes:
        print("vwgen: Network '{}' does not have node '{}'".format(
            network_name, left_node),
              file=sys.stderr)
        return_value = return_value or errno.ENOENT
        if operation:
            return return_value
    if not isinstance(args.right_node, list):
        args.right_node = [args.right_node]
    for right_node in args.right_node:

        if right_node not in nodes:
            print("vwgen: Network '{}' does not have node '{}'".format(
                network_name, right_node),
                  file=sys.stderr)
            return_value = return_value or errno.ENOENT
            if operation:
                continue

        if operation:
            blacklist.add(common.NamePair(left_node, right_node))
            blacklist.add(common.NamePair(right_node, left_node))
        else:
            try:
                blacklist.remove(common.NamePair(left_node, right_node))
            except KeyError:
                pass
            try:
                blacklist.remove(common.NamePair(right_node, left_node))
            except KeyError:
                pass

    config.save()
    config.close()
    return return_value
