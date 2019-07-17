import binascii
import sys
from typing import List
from . import common


def vw_genpsk() -> int:
    print(binascii.b2a_base64(common.genkey(), newline=False).decode('ascii'))
    return 0
