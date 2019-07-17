import binascii
import errno
import ipaddress
import random
import sys
from typing import Any, Dict, List, Optional, Set
from . import common
import argparse


def vw_add(args: argparse.Namespace) -> int:

    network_name = args.interface[0]
    config = common.Config()
    config.load(network_name)
    network = config.network()
    nodes = config.nodes()
    blacklist = config.blacklist()
    config.save()

    return_value = 0

    for node_name in args.nodes:
        if node_name in nodes:
            print("vwgen: Network '{}' already has node '{}'".format(
                network_name, node_name),
                  file=sys.stderr)
            return_value = return_value or errno.EEXIST
            continue

        node: Dict[str, Any] = common.SortedDict()
        if 'AddressPoolIPv4' in network:
            ipv4 = generate_random_ipv4(network, nodes)
            if ipv4 is None:
                print('vwgen: IPv4 address pool is full')
                break
            node['Address'] = [ipv4]
        else:
            node['Address'] = []

        ipv4ll = generate_random_ipv4ll(nodes)
        if ipv4ll is None:
            print('vwgen: Link-layer address pool is full')
            break

        node['AllowedIPs'] = [ipv4ll + '/32']
        node['Endpoint'] = None
        node['FwMark'] = 0
        node['LinkLayerAddress'] = [ipv4ll + '/16']
        node['ListenPort'] = random.randint(32768, 60999)
        node['PersistentKeepalive'] = 0
        node['PrivateKey'] = binascii.b2a_base64(common.genkey(),
                                                 newline=False).decode('ascii')
        node['SaveConfig'] = False
        node['UPnP'] = False

        node['PreUp'] = []
        node['PostUp'] = []
        node['PreDown'] = []
        node['PostDown'] = []

        nodes[node_name] = node

    config.save()
    config.close()
    return return_value


def generate_random_ipv4(network: common.Config.NetworkType,
                         nodes: common.Config.NodesType) -> Optional[str]:

    address_pool = ipaddress.IPv4Network(network['AddressPoolIPv4'],
                                         strict=False)

    if address_pool.prefixlen < 31:
        num_hosts = address_pool.num_addresses - 2
    else:
        num_hosts = address_pool.num_addresses

    existing_addresses: Set[str] = set((str(j).split('/', 1)[0]
                                        for i in nodes.values()
                                        for j in i.get('Address', [])))

    if len(existing_addresses) == num_hosts:
        return None

    while True:

        if address_pool.prefixlen >= 32:
            host = 0
        elif address_pool.prefixlen == 31:
            host = random.randint(0, 1)
        else:
            host = random.randint(1,
                                  (0xffffffff >> address_pool.prefixlen) - 1)

        ipv4 = ipaddress.IPv4Address(int(address_pool.network_address)
                                     | host).compressed

        if ipv4 not in existing_addresses:
            break

    return ipv4 + '/' + str(address_pool.prefixlen)


def generate_random_ipv4ll(nodes: common.Config.NodesType) -> Optional[str]:

    existing_addresses: Set[str] = set(
        (str(j).split('/', 1)[0] for i in nodes.values()
         for j in i.get('LinkLayerAddress', [])))

    if len(existing_addresses) >= 0xa9feff00 - 0xa9fe0100:
        return None

    while True:

        ipv4ll = ipaddress.IPv4Address(random.randint(0xa9fe0100,
                                                      0xa9fefeff)).compressed

        if ipv4ll not in existing_addresses:
            break

    return ipv4ll
