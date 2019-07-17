from typing import List, Optional
import argparse
import errno
from . import common
import json
import dicttoxml
import toml
import yaml


class exporter():
    def __init__(self, network_name):
        self.config = common.Config()

        if not self.config.load(network_name):
            print("vwgen: Unable to find configuration file '{}.conf'".format(
                network_name),
                  file=sys.stderr)
            exit(0)

        network = self.config.network()
        nodes = self.config.nodes()
        node: Optional[common.Config.NodeType] = None

        self.config.conf2str()
        self.dict_context = eval(self.config._conf2str)

    def dict2json(self):
        json_context = json.dumps(self.dict_context)
        return json_context

    def dict2yaml(self):
        yaml_context = yaml.dump(self.dict_context)
        return yaml_context

    def dict2xml(self):
        xml_context = dicttoxml.dicttoxml(self.dict_context)
        return xml_context

    def dict2toml(self):
        toml_context = toml.dumps(self.dict_context)
        return toml_context


def vw_export(args: argparse.Namespace) -> int:

    network_name = args.interface[0]

    export = exporter(network_name)

    print(export.dict2yaml())
