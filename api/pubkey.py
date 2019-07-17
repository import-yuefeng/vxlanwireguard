import binascii
import errno
import sys
from typing import List
from . import common


def vw_pubkey() -> int:

    # secret_base64 = sys.stdin.buffer.read()
    # secret_base64 = sys.stdin.readlines()
    secret_base64 = input()
    try:
        secret = binascii.a2b_base64(secret_base64)
        if len(secret) != 32:
            raise ValueError
    except (binascii.Error, ValueError):
        print('vwgen: Key is not the correct length or format',
              file=sys.stderr)
        return errno.EINVAL

    print(
        binascii.b2a_base64(common.pubkey(secret),
                            newline=False).decode('ascii'))

    return 0
