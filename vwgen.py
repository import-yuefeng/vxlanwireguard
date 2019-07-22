# !/usr/bin/env python3

import sys
import argparse
import subprocess
from pathlib import Path
from api import batch
from api import genkey, genpsk, pubkey
from api import common
from api import add, show, zone, vw_set, vw_del, showconf, blacklist, vw_export
from typing import Dict


NORMAL = '\x1b[0m'
BOLD = '\x1b[1m'
GREEN = '\x1b[32m'
YELLOW = '\x1b[33m'


class vxWireguardCommand():
    def __init__(self):
        self.parser = argparse.ArgumentParser()
        self.subcmd = self.parser.add_subparsers(dest='subcmd',
                                                 help='subcommands',
                                                 metavar='SUBCOMMAND')
        self.parser.add_argument("--config", default="", dest='config', help='config class')

        # self.subcmd.required = True

    def __build_parser_add(self):
        # subCommand: add
        add_parser = self.subcmd.add_parser(
            'add',
            help=
            'Add new nodes to the mesh network or init VxWireguard mesh net work'
        )
        add_parser.add_argument('-n', '--node',
                                default=[],
                                dest='nodes',
                                help='new node user name',
                                action='append')
        add_parser.add_argument('-i',
                                '--interface',
                                dest='interface',
                                required=True,
                                help='network-interface name',
                                action='append')

    def __build_parser_set(self):
        # subCommand: set
        set_parser = self.subcmd.add_parser(
            'set', help='Change the configuration of nodes')
        set_parser.add_argument('-i',
                                '--interface',
                                dest='interface',
                                required=True,
                                help='network-interface name',
                                action='append')

        set_parser.add_argument('-n', "--node", dest='node', type=str, help='Node name')
        set_parser.add_argument('-4', "--ipv4", dest='pool_ipv4', type=str, help='Pool ipv4')
        set_parser.add_argument('-6', "--ipv6", dest='pool_ipv6', type=str, help='Pool ipv6')
        set_parser.add_argument('--vxlan-id', dest='vxlan_id', type=str, help='Vxlan id')
        set_parser.add_argument('--vxlan-mtu', dest='vxlan_mtu', type=str, help='Vxlan MTU')
        set_parser.add_argument('--vxlan-port', dest='vxlan_port', type=str, help='Vxlan port')
        set_parser.add_argument('--addr', dest='addr', type=str, help='Address')
        set_parser.add_argument('--allowed-ips', dest='all_ips', type=str, help='Allowed IP')
        set_parser.add_argument('--endpoint', dest='endpoint', type=str, help='Endpoint')
        set_parser.add_argument('--fwmark', dest='fwmark', type=str, help='fwmark')
        set_parser.add_argument('--lladdr',
                                type=str,
                                dest='ll_addr', 
                                help='Link layer address')
        set_parser.add_argument('--listen-port',
                                dest='listen_port', 
                                type=str,
                                help='Config listen port')
        set_parser.add_argument('--persistent-keepalive',
                                dest='persistent_keepalive', 
                                type=str,
                                help='Keep connect alive')
        set_parser.add_argument('--private-key',
                                dest='private_key', 
                                type=str,
                                help='Modify private key')
        set_parser.add_argument('-s',
                                '--save',
                                dest='save_config', 
                                type=str,
                                help='To save config')
        set_parser.add_argument('--no-save',
                                dest='nosave_config', 
                                type=str,
                                help='Do not save config')
        set_parser.add_argument('--upnp', dest='upnp', type=str, help='To do use UPnP')
        set_parser.add_argument('--no-upnp', dest='noupnp', type=str, help='Do not use UPnP ')

    def __build_parser_del(self):
        # subCommand: del
        del_parser = self.subcmd.add_parser(
            'del', help='Delete nodes from the mesh network')
        del_parser.add_argument('-n', '--node',
                                default=[],
                                dest='nodes',
                                help='new node user name',
                                action='append')
        del_parser.add_argument('-i',
                                '--interface',
                                dest='interface',
                                required=True,
                                help='network-interface name',
                                action='append')

    def __build_parser_zone(self):
        # subCommand: zone
        del_parser = self.subcmd.add_parser(
            'zone', help='Generate BIND-style DNS zone records')
        del_parser.add_argument('-i',
                                '--interface',
                                default=[],
                                dest='interface',
                                help='network-interface name',
                                action='append')
        del_parser.add_argument('-d',
                                '--domain',
                                dest='domain',
                                required=True,
                                help='domain suffix',
                                action='append')

    def __build_parser_show(self):
        # subCommand: show
        show_parser = self.subcmd.add_parser('show',
                                             help='Show mesh network info')
        show_parser.add_argument('-i', '--interface', 
                                 dest='interface',
                                 required=True,
                                 help='network-interface name',
                                 action='append')

    def __build_parser_genkey(self):
        # subCommand: genkey
        genkey_parser = self.subcmd.add_parser(
            'key', help='Generates a new private key and writes it to stdout')

    def __build_parser_genpsk(self):
        # subCommand: genpsk
        genpsk_parser = self.subcmd.add_parser(
            'psk',
            help='Generates a new preshared key and writes it to stdout')

    def __build_parser_pubkey(self):
        # subCommand: pubkey
        pubkey_parser = self.subcmd.add_parser(
            'pub',
            help=
            'Reads a private key from stdin and writes a public key to stdout')

    def __build_parser_export(self):
        # subCommand: export
        export_parser = self.subcmd.add_parser(
            'export', help='Export your interface config file(default: yaml)')
        export_parser.add_argument('-i',
                                   '--interface',
                                   dest='interface',
                                   required=True,
                                   help='network-interface name',
                                   action='append')
        export_parser.add_argument('--yaml',
                                   action='store_true',
                                   dest='yaml',
                                   help='Export config file (yaml)')
        export_parser.add_argument('--toml',
                                   action='store_true',
                                   dest='toml',
                                   help='Export config file (toml)')
        export_parser.add_argument('--xml',
                                   action='store_true',
                                   dest='xml',
                                   help='Export config file (xml)')
        export_parser.add_argument('--json',
                                   action='store_true',
                                   dest='json',
                                   help='Export config file (json)')

    def __build_parser_blacklist(self):
        # subCommand: blacklist
        blacklist_parser = self.subcmd.add_parser(
            'bl', help='Manage peering blacklist between specified nodes')
        blacklist_parser.add_argument('-l',
                                      dest='left_node',
                                      type=str,
                                      help='left_node name')
        blacklist_parser.add_argument('-r',
                                      dest='right_node',
                                      type=str,
                                      help='left_node name')
        blacklist_parser.add_argument('-i',
                                      '--interface',
                                      dest='interface',
                                      required=True,
                                      help='network-interface name',
                                      action='append')
        blacklist_parser.add_argument('operate', help='add or del operate')

    def __build_parser_batch(self):
        # subCommand: batch        

        self.parser.add_argument("-batch", default="", dest='batch', help='Read commands from provided file or standard input and invoke them.')



    def __build_parser_show_conf(self):
        # subCommand: showconf
        show_conf_parser = self.subcmd.add_parser('ls',
                                                  help='Print peer conf info')
        show_conf_parser.add_argument('-i',
                                      '--interface',
                                      dest='interface',
                                      required=True,
                                      help='network-interface name',
                                      action='append')

        show_conf_parser.add_argument('-n', '--node',
                                      type=str,
                                      dest='nodes',
                                      default=[],
                                      help='Show info about a node')
        show_conf_parser.add_argument(
            '-qr',
            action='store_true',
            dest='qr_printable',
            help='Show info about a node(Default: False)')

    def _build_parser(self):

        self.__build_parser_add()
        self.__build_parser_set()
        self.__build_parser_del()
        self.__build_parser_show()
        self.__build_parser_zone()
        self.__build_parser_batch()
        self.__build_parser_genkey()
        self.__build_parser_genpsk()
        self.__build_parser_pubkey()
        self.__build_parser_export()
        self.__build_parser_blacklist()
        self.__build_parser_show_conf()


    def parser_sub_command(self):
        self._build_parser()
        # conf_map = Dict[str, common.Config()]
        conf_map = {}
        args = self.parser.parse_args()

        if args.batch:
            command_list: list(str) = batch.load(args.batch)
        else:
            command_list: list(str) = [None]
        for index, sentence in enumerate(command_list):
            try:
                if sentence == None:
                    args = self.parser.parse_args()
                else:
                    args = self.parser.parse_args(sentence.split())
                if args.subcmd:
                    if args.interface[0] in conf_map:
                        config = conf_map[args.interface[0]]
                    else:
                        config = common.Config()
                        config.load(args.interface[0])
                        conf_map[args.interface[0]] = config

                    args.config = config
                    if args.subcmd == 'add':
                        add.vw_add(args)
                    elif args.subcmd == 'del':
                        vw_del.vw_del(args)
                    elif args.subcmd == 'set':
                        vw_set.vw_set(args)
                    elif args.subcmd == 'show':
                        show.vw_show(args)
                    elif args.subcmd == 'key':
                        genkey.vw_genkey()
                    elif args.subcmd == 'psk':
                        genpsk.vw_genpsk()
                    elif args.subcmd == 'pub':
                        pubkey.vw_pubkey()
                    elif args.subcmd == 'bl':
                        blacklist.vw_blacklist(args)
                    elif args.subcmd == 'ls':
                        if args.nodes == []:
                            show.vw_show(args)
                        else:
                            showconf.vw_show_conf(args)
                    elif args.subcmd == 'export':
                        vw_export.vw_export(args)
                    elif args.subcmd == 'zone':
                        zone.vw_zone(args)
            except Exception as e:
                print("\n", e)
                print("\n{0}Error: {1}{2}Found an error on the {3} line.{1}\n".format(BOLD, NORMAL, YELLOW, index+1))


if __name__ == '__main__':
    test = vxWireguardCommand()
    test.parser_sub_command()
