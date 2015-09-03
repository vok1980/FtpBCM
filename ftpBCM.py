#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse


class FtpBCM:
	def __init__(self, command, server, path, version, platform):
		print command, server, path, version, platform	



def main():
	parser = argparse.ArgumentParser(description='Push binaries to ftp server with respect to version and target platform.')
	parser.add_argument('command', help='Command can be push or pull')
	parser.add_argument('server', help='Destination server name.')
	parser.add_argument('path', help='Path to be stored on server.')
	parser.add_argument('version', help='Version of binaries.')
	parser.add_argument('platform', help='Target platform name')

	args = parser.parse_args()

	if ((args.command != 'push')  and (args.command != 'pull')):
		raise Exception('Unexpected command \'', parser.command, '\'')


	bcm = FtpBCM(args.command, args.server, args.path, args.version, args.platform);


if __name__ == "__main__":
    main()


