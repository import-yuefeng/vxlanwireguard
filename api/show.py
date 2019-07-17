import binascii
import errno
import sys
from typing import List
from . import common
import argparse

NORMAL = '\x1b[0m'
BOLD = '\x1b[1m'
GREEN = '\x1b[32m'
YELLOW = '\x1b[33m'


def vw_show(args: argparse.Namespace) -> int:

    return_value = 0
    for network_name in args.interface:
        # network_name = args[2]
        config = common.Config()

        if not config.load(network_name):
            print("vwgen: Unable to find configuration file '{}.conf'".format(
                network_name),
                  file=sys.stderr)
            return_value = return_value or errno.ENOENT
            continue

        network = config.network()
        nodes = config.nodes()
        blacklist = config.blacklist()

        print('{}network:{} {}{}{}'.format(BOLD, NORMAL, GREEN,
                                           config.network_name(), NORMAL))

        print('  {}address pool ipv4:{} {}'.format(
            BOLD, NORMAL, network.get('AddressPoolIPv4', '')))

        print('  {}address pool ipv6:{} {}'.format(
            BOLD, NORMAL, network.get('AddressPoolIPv6', '')))

        print('  {}vxlan port:{} {}'.format(BOLD, NORMAL,
                                            network.get('VxlanPort', 4789)))

        print('  {}vxlan mtu:{} {}'.format(BOLD, NORMAL,
                                           network.get('VxlanMTU', 1500)))

        print('  {}vxlan id:{} {}'.format(BOLD, NORMAL,
                                          network.get('VxlanID', 0)))

        print()

        for node_name, node in nodes.items():

            print('{}node:{} {}{}{}'.format(BOLD, NORMAL, YELLOW, node_name,
                                            NORMAL))

            secret_base64 = node.get('PrivateKey', '')
            secret = binascii.a2b_base64(secret_base64)
            if len(secret) != 32:
                pubkey = '(error)'
            else:
                pubkey = binascii.b2a_base64(common.pubkey(secret),
                                             newline=False).decode('ascii')

            print('  {}public key:{} {}'.format(BOLD, NORMAL, pubkey))

            print('  {}private key:{} {}'.format(BOLD, NORMAL, secret_base64))

            print('  {}endpoint:{} {}'.format(BOLD, NORMAL,
                                              node.get('Endpoint') or ''))

            print('  {}listen port:{} {}'.format(BOLD, NORMAL,
                                                 node.get('ListenPort', 0)))

            address = node.get('Address', [])
            pubkey_ipv6 = common.generate_pubkey_ipv6(network, node)
            if pubkey_ipv6:
                address.append(pubkey_ipv6)

            print('  {}address:{} {}'.format(BOLD, NORMAL, ', '.join(address)))

            print('  {}allowed ips:{} {}'.format(
                BOLD, NORMAL, ', '.join(node.get('AllowedIPs', []))))

            print('  {}link-layer address:{} {}'.format(
                BOLD, NORMAL, ', '.join(node.get('LinkLayerAddress', []))))

            if node.get('FwMark', 0) != 0:
                print('  {}fwmark:{} {:x}'.format(BOLD, NORMAL,
                                                  node['FwMark']))

            if node.get('PersistentKeepalive', 0) != 0:
                print('  {}persistent keepalive:{} {} {}'.format(
                    BOLD, NORMAL, node['PersistentKeepalive'], 'seconds'
                    if node['PersistentKeepalive'] != 1 else 'second'))

            if node.get('SaveConfig', False):
                print('  {}save config:{} true'.format(BOLD, NORMAL))

            if node.get('UPnP', False):
                print('  {}upnp:{} true'.format(BOLD, NORMAL))

            node_blacklist: List[str] = [
                str(i[1]) for i in blacklist if i[0] == node_name
            ]
            node_whitelist: List[str] = sorted(
                set(nodes) - set(node_blacklist) - {node_name})
            print('  {}blacklist:{} {}'.format(BOLD, NORMAL,
                                               ', '.join(node_blacklist)))
            print('  {}whitelist:{} {}'.format(BOLD, NORMAL,
                                               ', '.join(node_whitelist)))

            print()

        config.close()

    return return_value
