# !/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK

import sys
import subprocess
import argparse
from pathlib import Path
from api import add, show, zone, vw_set, vw_del, genkey, genpsk, pubkey, showconf, blacklist, vw_export
import argcomplete


class vxWireguardCommand():
    def __init__(self):
        self.parser = argparse.ArgumentParser()
        self.subcmd = self.parser.add_subparsers(dest='subcmd',
                                                 help='subcommands',
                                                 metavar='SUBCOMMAND')
        self.subcmd.required = True

    def __build_parser_add(self):
        # subCommand: add
        add_parser = self.subcmd.add_parser(
            'add',
            help=
            'Add new nodes to the mesh network or init VxWireguard mesh net work'
        )
        add_parser.add_argument('-c',
                                type=Path,
                                help='config file path of the directory',
                                metavar='DIR')
        add_parser.add_argument('-n',
                                default=[],
                                dest='nodes',
                                help='new node user name',
                                action='append')
        add_parser.add_argument('-i',
                                dest='interface',
                                required=True,
                                help='network-interface name',
                                action='append')

    def __build_parser_set(self):
        # subCommand: set
        set_parser = self.subcmd.add_parser(
            'set', help='Change the configuration of nodes')

        set_parser.add_argument('-n', "--node", type=str, help='Node name')
        set_parser.add_argument('-4', "--ipv4", type=str, help='Pool ipv4')
        set_parser.add_argument('-6', "--ipv6", type=str, help='Pool ipv6')
        set_parser.add_argument('--vxlan-id', type=str, help='Vxlan id')
        set_parser.add_argument('--vxlan-mtu', type=str, help='Vxlan MTU')
        set_parser.add_argument('--vxlan-port', type=str, help='Vxlan port')
        set_parser.add_argument('--addr', type=str, help='Address')
        set_parser.add_argument('--allowed-ips', type=str, help='Allowed IP')
        set_parser.add_argument('--endpoint', type=str, help='Endpoint')
        set_parser.add_argument('--fwmark', type=str, help='fwmark')
        set_parser.add_argument('--lladdr',
                                type=str,
                                help='Link layer address')
        set_parser.add_argument('--listen-port',
                                type=str,
                                help='Config listen port')
        set_parser.add_argument('--persistent-keepalive',
                                type=str,
                                help='Keep connect alive')
        set_parser.add_argument('--private-key',
                                type=str,
                                help='Modify private key')
        set_parser.add_argument('-s',
                                '--save',
                                type=str,
                                help='To save config')
        set_parser.add_argument('--no-save',
                                type=str,
                                help='Do not save config')
        set_parser.add_argument('--upnp', type=str, help='To do use UPnP')
        set_parser.add_argument('--no-upnp', type=str, help='Do not use UPnP ')

    def __build_parser_del(self):
        # subCommand: del
        del_parser = self.subcmd.add_parser(
            'del', help='Delete nodes from the mesh network')
        del_parser.add_argument('-n',
                                default=[],
                                dest='nodes',
                                help='new node user name',
                                action='append')
        del_parser.add_argument('-i',
                                dest='interface',
                                required=True,
                                help='network-interface name',
                                action='append')

    def __build_parser_zone(self):
        # subCommand: zone
        del_parser = self.subcmd.add_parser(
            'zone', help='Generate BIND-style DNS zone records')
        del_parser.add_argument('-i', '--interface',
                                default=[],
                                dest='interface',
                                help='network-interface name',
                                action='append')
        del_parser.add_argument('-d', '--domain',
                                dest='domain',
                                required=True,
                                help='domain suffix',
                                action='append')

    def __build_parser_show(self):
        # subCommand: show
        show_parser = self.subcmd.add_parser('show',
                                             help='Show mesh network info')
        show_parser.add_argument('-i',
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
                                      dest='interface',
                                      required=True,
                                      help='network-interface name',
                                      action='append')
        blacklist_parser.add_argument('operate', help='add or del operate')

    def __build_parser_show_conf(self):
        # subCommand: showconf
        show_conf_parser = self.subcmd.add_parser(
            'list', help='Manage peering blacklist between specified nodes')
        show_conf_parser.add_argument('-i',
                                      dest='interface',
                                      required=True,
                                      help='network-interface name',
                                      action='append')

        show_conf_parser.add_argument('-n',
                                      type=str,
                                      dest='nodes',
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
        self.__build_parser_genkey()
        self.__build_parser_genpsk()
        self.__build_parser_pubkey()
        self.__build_parser_export()
        self.__build_parser_blacklist()
        self.__build_parser_show_conf()

    def parser_sub_command(self):
        self._build_parser()
        argcomplete.autocomplete(self.parser)
        args = self.parser.parse_args()

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

if __name__ == '__main__':
    test = vxWireguardCommand()
    test.parser_sub_command()
    sys.exit(1)
