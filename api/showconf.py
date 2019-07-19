import binascii
import errno
import sys
from typing import List, Optional
from . import common
import argparse
import qrcode_terminal


def vw_show_conf(args: argparse.Namespace) -> int:

    conf_content: str = ""
    network_name, node_name = args.interface[0], args.nodes

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

    if node_name not in nodes:
        print("vwgen: Network '{}' does not have node '{}'".format(
            network_name, node_name),
              file=sys.stderr)
        return errno.ENOENT
    node = nodes[node_name]

    print()

    conf_content += '[Interface]\n'
    conf_content += 'ListenPort = {:d}\n'.format(node.get('ListenPort', 0))

    if 'PrivateKey' in node:
        conf_content += 'PrivateKey = {}\n'.format(node['PrivateKey'])
    if 'LinkLayerAddress' in node:
        conf_content += 'Address = {}\n'.format(', '.join(
            node['LinkLayerAddress']))
    conf_content += 'MTU = {}\n'.format(
        int(network.get('VxlanMTU', 1500)) + 50)
    conf_content += 'Table = off\n'
    if node.get('FwMark', 0) != 0:
        conf_content += 'FwMark = {:x}\n'.format(node['FwMark'])

    if node.get('SaveConfig', False):
        conf_content += 'SaveConfig = true\n'
    for script in node.get('PreUp', []):
        conf_content += 'PreUp = {}\n'.format(script)
    mac_address = common.generate_pubkey_macaddr(node)
    mac_address_cmdline = ''
    if mac_address:
        mac_address_cmdline = 'address {} '.format(mac_address)

    conf_content += 'PreUp = ip link add v%i {}mtu {} type vxlan id {} dstport {} ttl 1 noudpcsum || true\n'.format(
        mac_address_cmdline, network.get('VxlanMTU', 1500),
        network.get('VxlanID', 0), network.get('VxlanPort', 4789))

    conf_content += 'PreUp = ethtool -K v%i tx off rx off\n'
    conf_content += 'PreUp = sysctl -w net.ipv4.conf.v%i.accept_redirects=0 net.ipv4.conf.v%i.send_redirects=0 net.ipv6.conf.v%i.accept_redirects=0\n'
    for address in node.get('Address', []):
        conf_content += 'PreUp = ip address add {} dev v%i || true\n'.format(
            address)
    pubkey_ipv6 = common.generate_pubkey_ipv6(network, node)
    if pubkey_ipv6:
        conf_content += 'PreUp = ip address add {} dev v%i || true\n'.format(
            pubkey_ipv6)
    if node.get('UPnP', False) and node.get('ListenPort', 0) != 0:
        conf_content += 'PreUp = upnpc -r {} udp &\n'.format(
            node['ListenPort'])
    for peer_name, peer in nodes.items():
        if peer_name == node_name:
            continue
        in_blacklist = common.NamePair(node_name, peer_name) in blacklist
        comment_prefix = '#' if in_blacklist else ''

        for address in peer.get('LinkLayerAddress', []):
            conf_content += '{}PostUp = bridge fdb append 00:00:00:00:00:00 dev v%i dst {} via %i\n'.format(
                comment_prefix,
                str(address).split('/', 1)[0])
 
    conf_content += 'PostUp = ip link set v%i up\n'
    for script in node.get('PostUp', []):
        conf_content += 'PostUp = {}\n'.format(script)
    for script in node.get('PreDown', []):
        conf_content += 'PreDown = {}\n'.format(script)
    conf_content += 'PreDown = ip link set v%i down\n'
    conf_content += 'PostDown = ip link delete v%i\n'

    for script in node.get('PostDown', []):
        conf_content += 'PostDown = {}\n'.format(script)
    conf_content += '\n'

    for peer_name, peer in nodes.items():
        if peer_name == node_name:
            continue
        in_blacklist = common.NamePair(node_name, peer_name) in blacklist
        comment_prefix = '#' if in_blacklist else ''
        conf_content += '{}# Peer node {}\n'.format(comment_prefix, peer_name)
        conf_content += '{}[Peer]\n'.format(comment_prefix)

        if peer.get('PrivateKey'):
            secret_base64: str = peer['PrivateKey']
            secret: bytes = binascii.a2b_base64(secret_base64)
            if len(secret) != 32:
                print("vwgen: Node '{}' has incorrect PrivateKey".format(
                    peer_name),
                      file=sys.stderr)
            else:
                pubkey = binascii.b2a_base64(common.pubkey(secret),
                                             newline=False).decode('ascii')
                conf_content += '{}PublicKey = {}\n'.format(
                    comment_prefix, pubkey)

        if peer.get('AllowedIPs'):
            conf_content += '{}AllowedIPs = {}\n'.format(
                comment_prefix, ', '.join(peer['AllowedIPs']))
        if peer.get('Endpoint'):
            conf_content += '{}Endpoint = {}\n'.format(comment_prefix,
                                                       peer['Endpoint'])
        if peer.get('PersistentKeepalive', 0) != 0:
            conf_content += '{}PersistentKeepalive = {}\n'.format(
                comment_prefix, node['PersistentKeepalive'])
        conf_content += '\n'
    print(conf_content)
    if args.qr_printable:
        qrcode_terminal.draw(conf_content)

    return 0
