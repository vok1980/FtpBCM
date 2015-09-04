#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
from ftplib import FTP
import ftplib


class FtpBCM:
	def __init__(self, command, server, user, passwd, path, version, platform):
		print command, server, user, passwd, path, version, platform	
		ftp = FTP(server)
		ftp.login(user, passwd)
		
		self.__mkd_cd(ftp, 'bcm')
		self.__mkd_cd(ftp, version)
		self.__mkd_cd(ftp, platform)

		ftp.retrlines('LIST')

		if command == 'push':
			self.__push(path)

		if command == 'pull':
			self.__pull(path)
		
		ftp.quit()


	def __mkd_cd(self, ftp, dirname):
		try:
                        ftp.mkd(dirname)
                except ftplib.error_perm as e:
                        print(e)

                ftp.cwd(dirname)


	def __push(self, path):
		print 'ready to push ', path


	def __pull(self, path):
		print 'ready to pull', path

		


def main():
	parser = argparse.ArgumentParser(description='Push binaries to ftp server with respect to version and target platform')
	parser.add_argument('command', help='Command can be push or pull')
	parser.add_argument('server', help='Destination server name')
	parser.add_argument('path', help='Path to be stored on server')
	parser.add_argument('version', help='Version of binaries')
	parser.add_argument('platform', help='Target platform name')
	parser.add_argument('--user', default='bcm', help='ftp username')
	parser.add_argument('--passwd', default='123', help='ftp userpass')

	args = parser.parse_args()

	if ((args.command != 'push') and (args.command != 'pull')):
		print 'Unexpected command: ',  args.command
		raise Exception('Unexpected command')

	bcm = FtpBCM(args.command, args.server, args.user, args.passwd, args.path, args.version, args.platform);


if __name__ == "__main__":
    main()


