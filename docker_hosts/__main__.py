# -*- coding: utf-8 -*-
from argparse import ArgumentParser

import daiquiri

from .docker_hosts import DockerHosts


def main():
    parser = ArgumentParser()
    parser.add_argument('-f', '--hosts-file', default="/etc/hosts", help="the hosts-style file to write to (default: %(default)s)")
    parser.add_argument('-p', '--pattern', default="{hostname}.{network}.local", help="the host entry pattern (default: %(default)s)")
    parser.add_argument('--container-filter', type=str, nargs='*')
    parser.add_argument('--network-filter', type=str, nargs='*')
    parser.add_argument('-v', '--verbose', action='count', help="Increase verbosity (default: %(default)s)", default=3)

    args = parser.parse_args()

    daiquiri.setup(level=40 - ((int(args.verbose) - 1) * 10))

    c = DockerHosts(container_filter=args.container_filter,
                network_filter=args.network_filter,
                hosts_file=args.hosts_file,
                pattern=args.pattern)
    c.run()


if __name__ == "__main__":
    main()
