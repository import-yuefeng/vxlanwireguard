import binascii
import collections
import errno
import fcntl
import ipaddress
import nacl.bindings
import random
import sys
import toml
from typing import Any, cast, Dict, KeysView, ItemsView, Iterator, List, Optional, Set, TextIO, TypeVar, ValuesView
import pickle


T = TypeVar('T')
KT = TypeVar('KT')
VT = TypeVar('VT')


# This metaclass patches the type check of toml 0.9.x
# It should use isinstance(v, list), but actually uses type(v) == list instead
class _FakeListMeta(type(list)):  # type: ignore
    def __hash__(self) -> int:
        return hash(list)

    def __getitem__(self, *args: Any, **kwargs: Any) -> type:
        return self

    def __eq__(self, other: Any) -> bool:
        return id(self) == id(other) or id(list) == id(other)

    def __ne__(self, other: Any) -> bool:
        return id(self) != id(other) and id(list) != id(other)


class FakeList(List[T], metaclass=_FakeListMeta):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)


class SortedDict(Dict[KT, VT]):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def keys(self) -> KeysView[KT]:
        return cast(KeysView[KT], sorted(super().keys()))

    def values(self) -> ValuesView[VT]:
        return super().values()

    def items(self) -> ItemsView[KT, VT]:
        return cast(ItemsView[KT, VT], sorted(super().items()))

    def __iter__(self) -> Iterator[KT]:
        return iter(self.keys())

    def __repr__(self) -> str:
        return '{' + ', '.join(
            (repr(k) + ': ' + repr(v) for k, v in self.items())) + '}'

    def __str__(self) -> str:
        return repr(self)


class SortedSet(FakeList[T]):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._set: Set[T] = set(*args, **kwargs)
        self._sorted: bool = False
        super().__init__()

    def add(self, item: T) -> None:
        self._set.add(item)
        # Add a new item
        self._sorted = False
        #  set sort state is false

    def remove(self, item: T) -> None:
        self._set.remove(item)
        # remove a item
        self._sorted = False
        #  set sort state is false

    def sort(self, **kwargs: Any) -> None:
        if not self._sorted:
            super().__init__(self._set)
            super().sort(**kwargs)
            self._sorted = True

    def __contains__(self, key: Any) -> bool:
        return key in self._set

    def __iter__(self) -> Iterator[T]:
        self.sort()
        return super().__iter__()

    def __len__(self) -> int:
        return len(self._set)

    def __repr__(self) -> str:
        return '{' + ', '.join((repr(i) for i in self)) + '}'

    def __str__(self) -> str:
        return repr(self)


class NamePair(FakeList[str]):
    def __init__(self, name1: str, name2: str) -> None:
        super().__init__((name1, name2))

    def __hash__(self) -> int:
        return hash(tuple(self))


class Config():
    # define type hint
    NetworkType = Dict[str, Any]
    NodeType = Dict[str, Any]
    NodesType = Dict[str, NodeType]
    BlacklistType = SortedSet[NamePair]

    def __init__(self) -> None:
        self._conf = SortedDict[str, Any]()
        # init self._conf
        self._conf_file: Optional[TextIO] = None
        # init config file point
        self._conf_name: Optional[str] = None
        # init str value
        self._writable = False
        # init bool value

    def __del__(self) -> None:
        try:
            self._close_file()
        except Exception:
            pass

    def load(self, conf_name: str) -> bool:
        if conf_name.endswith('.conf'):
            conf_name = conf_name[:-5]
        try:
            self._open_file(conf_name)
        except FileNotFoundError:
            # your network conf init process
            self._conf = SortedDict()
            self._conf_name = conf_name
            return False
        assert self._conf_file is not None
        self._conf = cast(SortedDict[str, Any],
                          toml.load(self._conf_file, SortedDict))
        # decode conf file to json?
        return True

    def conf2str(self) -> bool:
        assert self._conf is not None
        if isinstance(self._conf, SortedDict):
            self._conf2str = self._conf.__str__()
            return True
        return False

    def save(self) -> None:
        if self._conf is None:
            return
        elif self._conf_name is None:
            return
        self._open_file(self._conf_name, writable=True)
        assert self._conf_file is not None
        data: str = toml.dumps(self._conf)
        self._conf_file.truncate()
        self._conf_file.write(data)

    def close(self) -> None:
        self._close_file()

    def network_name(self) -> str:
        if self._conf_name is None:
            raise ValueError('Config not loaded')
        return self._conf_name

    def network(self) -> NetworkType:
        if 'Network' not in self._conf:
            # init network conf (random generate genipv4-pool, ipv6-pool and VxlanID)
            self._conf['Network'] = SortedDict[str, Any]()
            self._conf['Network'][
                'AddressPoolIPv4'] = '192.168.{}.0/24'.format(
                    random.randint(2, 255))
            self._conf['Network'][
                'AddressPoolIPv6'] = '{:x}:{:x}:{:x}::/80'.format(
                    random.randint(0xfd00, 0xfdff),
                    random.randint(0x1000, 0xffff),
                    random.randint(0x1000, 0xffff))
            self._conf['Network']['VxlanID'] = random.randint(1, 0xffffff)
            # To make a UDP packet 2048 byte so we don't waste too many bytes transmitting fragmented headers
            self._conf['Network']['VxlanMTU'] = 1966
            self._conf['Network']['VxlanPort'] = 4789
        return cast(Config.NetworkType, self._conf['Network'])

    def nodes(self) -> NodesType:
        if 'Node' not in self._conf:
            self._conf['Node'] = SortedDict()
        return cast(Config.NodesType, self._conf['Node'])

    def blacklist(self) -> BlacklistType:
        if 'PeerBlacklist' not in self._conf:
            self._conf['PeerBlacklist'] = {'Blacklist': SortedSet()}
        elif 'Blacklist' not in self._conf['PeerBlacklist']:
            self._conf['PeerBlacklist']['Blacklist'] = SortedSet()
        elif not isinstance(self._conf['PeerBlacklist']['Blacklist'],
                            SortedSet):
            self._conf['PeerBlacklist']['Blacklist'] = SortedSet(
                (NamePair(i, j)
                 for i, j in self._conf['PeerBlacklist']['Blacklist']))
        return cast(Config.BlacklistType,
                    self._conf['PeerBlacklist']['Blacklist'])

    def _close_file(self) -> None:
        if self._conf_file is None:
            return
        fcntl.lockf(self._conf_file, fcntl.LOCK_UN)
        self._conf_file.close()
        self._conf_file = None
        # unlock the lock

    def _open_file(self, conf_name: str, writable: bool = False) -> None:
        if self._conf_file is not None and self._conf_name == conf_name and self._writable >= writable:
            self._conf_file.seek(0)
            return
        self._close_file()
        if writable:
            conf_file = open(conf_name + '.conf', 'w+')
        else:
            conf_file = open(conf_name + '.conf', 'r')
        try:
            # LOCK_UN - 解锁
            # LOCK_SH - 获取共享锁
            # LOCK_EX - 获得互斥锁
            try:
                # 避免获得锁的时候产生阻塞
                if writable:
                    fcntl.lockf(conf_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
                else:
                    fcntl.lockf(conf_file, fcntl.LOCK_SH | fcntl.LOCK_NB)
            except OSError as e:
                if e.errno in (errno.EACCES, errno.EAGAIN):
                    # 如果使用 LOCK_NB 并且无法获取锁定，则会引发 OSError ，并且异常将errno属性设置为 EACCES 或 EAGAIN （取决于操作系统;为了便携性，请检查两个值）。
                    print(
                        'The configuration file is being used by another process, waiting.',
                        end='',
                        file=sys.stderr,
                        flush=True)
                    if writable:
                        fcntl.lockf(conf_file, fcntl.LOCK_EX)
                    else:
                        fcntl.lockf(conf_file, fcntl.LOCK_SH)
                    print(file=sys.stderr, flush=True)
                else:
                    raise
        except Exception as e:
            conf_file.close()
            raise
        self._conf_file = conf_file
        self._conf_name = conf_name
        self._writable = writable


def genpsk() -> bytes:
    return cast(bytes, nacl.bindings.randombytes(32))


def genkey() -> bytes:
    secret = bytearray(nacl.bindings.randombytes(32))
    # curve25519_normalize_secret
    secret[0] &= 248
    secret[31] &= 127
    secret[31] |= 64
    return bytes(secret)


def pubkey(secret: bytes) -> bytes:
    return cast(bytes, nacl.bindings.crypto_scalarmult_base(secret))
    # return nacl.bindings.crypto_scalarmult_base(secret)


def generate_pubkey_macaddr(node: Config.NodeType) -> Optional[str]:
    if 'PrivateKey' not in node:
        return None
    secret_base64: str = node['PrivateKey']
    secret: bytes = binascii.a2b_base64(secret_base64)
    if len(secret) != 32:
        return None

    macaddr = pubkey(secret)[-6:]
    return '{:02x}:{:02x}:{:02x}:{:02x}:{:02x}:{:02x}'.format(
        (macaddr[0] & 0xfe) | 0x02, macaddr[1], macaddr[2], macaddr[3],
        macaddr[4], macaddr[5])


def generate_pubkey_ipv6(network: Config.NetworkType,
                         node: Config.NodeType) -> Optional[str]:
    if 'AddressPoolIPv6' not in network:
        return None
    address_pool = ipaddress.IPv6Network(network['AddressPoolIPv6'],
                                         strict=False)

    if 'PrivateKey' not in node:
        return None
    secret_base64: str = node['PrivateKey']
    secret: bytes = binascii.a2b_base64(secret_base64)
    if len(secret) != 32:
        return None

    host = ipaddress.IPv6Address(pubkey(secret)[-16:])
    ipv6 = ipaddress.IPv6Address(
        int(address_pool.network_address)
        | (int(host) & int(address_pool.hostmask)))

    return ipv6.compressed + '/' + str(address_pool.prefixlen)


if __name__ == "__main__":
    pass
