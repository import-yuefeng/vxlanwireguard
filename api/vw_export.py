from typing import List, Optional
import argparse
import errno
from . import common
import json
import dicttoxml
import toml
import yaml
import sys

class exporter():
    def __init__(self, args):
        # self.config = common.Config()

        # if not self.config.load(network_name):
        #     print("vwgen: Unable to find configuration file '{}.conf'".format(
        #         network_name),
        #           file=sys.stderr)
        #     exit(0)
        self.config = args.config

        network = self.config.network()
        nodes = self.config.nodes()
        node: Optional[common.Config.NodeType] = None

        self.config.conf2str()
        self.dict_context = eval(self.config._conf2str)

    def dict2json(self) -> str:
        json_context :str = json.dumps(self.dict_context)
        return json_context

    def dict2yaml(self) -> str:
        yaml_context :str = yaml.dump(self.dict_context)
        return yaml_context

    def dict2xml(self) -> str:
        xml_context :str = dicttoxml.dicttoxml(self.dict_context)
        return xml_context

    def dict2toml(self) -> str:
        toml_context :str = toml.dumps(self.dict_context)
        return toml_context


def vw_export(args: argparse.Namespace) -> int:

    network_name = args.interface[0]

    export = exporter(args)

    if args.yaml:
        print(export.dict2yaml())
    elif args.json:
        print(export.dict2json())
    elif args.xml:
        print(export.dict2xml())
    elif args.toml:
        print(export.dict2toml())
    else:
        print(export.dict2json())
