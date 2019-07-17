import errno
import ipaddress
import sys
from typing import List, Optional
from . import common
import argparse


class InvalidNodeError(Exception):
    pass


def vw_set(args: argparse.Namespace) -> int:

    network_name = args.interface[0]
    config = common.Config()

    if not config.load(network_name):
        print("vwgen: Unable to find configuration file '{}.conf'".format(
            network_name),
              file=sys.stderr)
        return errno.ENOENT

    network = config.network()
    nodes = config.nodes()
    node: Optional[common.Config.NodeType] = None
    config.save()

    return_value = 0

    try:
        if args.node:
            node_name = args.node
            if node_name not in nodes:
                print("vwgen: Network '{}' does not have node '{}'".format(
                    network_name, node_name),
                      file=sys.stderr)
                return errno.ENOENT
            node = nodes[node_name]

        if args.pool_ipv4:
            network['AddressPoolIPv4'] = ipaddress.IPv4Network(
                args.pool_ipv4, strict=False).compressed

        elif args.pool_ipv6:
            network['AddressPoolIPv6'] = ipaddress.IPv6Network(
                args.pool_ipv6, strict=False).compressed

        elif args.vxlan_id:
            network['VxlanID'] = int(args.vxlan_id)

        elif args.vxlan_mtu:
            network['VxlanMTU'] = int(args.vxlan_mtu)

        elif args.vxlan_port:
            network['VxlanPort'] = int(args.vxlan_port)

        elif args.addr:
            if node is None:
                raise InvalidNodeError
            node['Address'] = list(map(str.strip, args.addr.split(',')))

        elif args.all_ips:
            if node is None:
                raise InvalidNodeError
            node['AllowedIPs'] = list(map(str.strip, args.all_ips.split(',')))

        elif args.endpoint:
            if node is None:
                raise InvalidNodeError
            if args.endpoint:
                endpoint = args.endpoint
                if endpoint.startswith('[') and endpoint.endswith(']'):
                    endpoint += str(node.get('ListenPort', 0))
                elif ':' not in endpoint:
                    endpoint += ':' + str(node.get('ListenPort', 0))
                elif endpoint.count(':') > 1:
                    endpoint = '[' + endpoint + ']:' + str(
                        node.get('ListenPort', 0))
                node['Endpoint'] = endpoint
            else:
                node['Endpoint'] = None

        elif args.fwmark:
            if node is None:
                raise InvalidNodeError
            if args.fwmark == 'off':
                node['FwMark'] = 0
            else:
                node['FwMark'] = int(args.fwmark, base=0)

        elif args.ll_addr:
            if node is None:
                raise InvalidNodeError
            node['LinkLayerAddr'] = args.ll_addr

        elif args.listen_port:
            if node is None:
                raise InvalidNodeError
            node['ListenPort'] = int(args.listen_port)

        elif args.persistent_keepalive:
            if node is None:
                raise InvalidNodeError
            if args.persistent_keepalive == 'off':
                node['PersistentKeepalive'] = 0
            else:
                node['PersistentKeepalive'] = int(args.persistent_keepalive)

        elif args.private_key:
            if node is None:
                raise InvalidNodeError
            node['PrivateKey'] = args.private_key

        elif args.save_config:
            if node is None:
                raise InvalidNodeError
            node['SaveConfig'] = True

        elif args.nosave_config:
            if node is None:
                raise InvalidNodeError
            node['SaveConfig'] = False

        elif args.upnp:
            if node is None:
                raise InvalidNodeError
            node['UPnP'] = True
        elif args.noupnp:
            if node is None:
                raise InvalidNodeError
            node['UPnP'] = False
    except InvalidNodeError:
        print(
            "vwgen: '{}' must be used after 'node' directive, use '--help' to check for help"
            .format(argv[arg_index]),
            file=sys.stderr)

    config.save()
    config.close()
    return return_value
