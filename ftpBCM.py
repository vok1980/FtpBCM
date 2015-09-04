#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
from ftplib import FTP
import ftplib
import io
import os
import glob


class FtpBCM:
	def __init__(self, command, server, user, passwd, path, version, platform):
		print command, server, user, passwd, path, version, platform	
		self.ftp = FTP(server)
		self.ftp.login(user, passwd)
		
		self.__mkd_cd('bcm')
		self.__mkd_cd(version)
		self.__mkd_cd(platform)

		if command == 'push':
			self.__push(path)

		if command == 'pull':
			self.__pull(path)
		
		self.ftp.quit()


	def __mkd_cd(self, dirname):

		try:
			self.ftp.mkd(dirname)
		except ftplib.error_perm as e:
			print(e)

		self.ftp.cwd(dirname)



	def uploadThis(self, path):

		if os.path.isfile(path):
			fh = open(path, 'rb')
			self.ftp.storbinary('STOR %s' % os.path.basename(path), fh)
			fh.close()

		elif os.path.isdir(path):			
			self.__mkd_cd(os.path.basename(os.path.normpath(path)))
			g = glob.glob(os.path.join(path, '*'))
			print 'glob result:', g

			for f in g:
				self.uploadThis(f)

			self.ftp.cwd('..')



	def __push(self, path):
		print 'ready to push ', path

		if self.__file_exists('guard_ready') or self.__file_exists('guard_push'):
			print 'data already exists or in progress'
			return

		else:
			print 'Data does not presists on server yet'

			bio = io.BytesIO(' ')
			self.ftp.storbinary('STOR guard_push', bio)

			self.__mkd_cd('data')
			self.uploadThis(path)

			self.ftp.delete(os.path.join('..', 'guard_push'))





	def __pull(self, path):
		print 'ready to pull', path
		
		if self.__file_exists('.guard_ready'):
			print 'data already exists'
			return
		else:
			print 'data does not exists'
			self.__mkd_cd('data')


	


	def __file_exists(self, filename):
		filelist = [] #to store all files
		self.ftp.retrlines('LIST',filelist.append)    # append to list  

		for f in filelist:
			if f.split()[-1] == filename:
				return True
		
		return False
		


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


