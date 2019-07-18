# VxlanWireguard

VxlanWireguard

usage: vwgen [-h] SUBCOMMAND ...

positional arguments:
  SUBCOMMAND  subcommands
    add       Add new nodes to the mesh network or init VxWireguard mesh net
              work
    set       Change the configuration of nodes
    del       Delete nodes from the mesh network
    show      Show mesh network info
    zone      Generate BIND-style DNS zone records
    key       Generates a new private key and writes it to stdout
    psk       Generates a new preshared key and writes it to stdout
    pub       Reads a private key from stdin and writes a public key to stdout
    export    Export your interface config file(default: yaml)
    bl        Manage peering blacklist between specified nodes
    ls        Print peer conf info

optional arguments:
  -h, --help  show this help message and exit

