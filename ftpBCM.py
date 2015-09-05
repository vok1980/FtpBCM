#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ftplib
import io
import os
import glob
import shutil
import tarfile
import tempfile


class FtpBCM:
	def __init__(self, server, user, passwd):
		self.server = server
		self.user = user
		self.passwd = passwd


	def __login(self, version, platform):
		self.ftp = ftplib.FTP(self.server)
		self.ftp.login(self.user, self.passwd)
		self.__mkd_cd('bcm')
		self.__mkd_cd(version)
		self.__mkd_cd(platform)


	def __mkd_cd(self, dirname):
		try:
			self.ftp.mkd(dirname)
		except ftplib.error_perm as e:
			print(e)

		self.ftp.cwd(dirname)


	def uploadThis(self, path):
		if os.path.isfile(path):
			with open(path, 'rb') as fh:
				self.ftp.storbinary('STOR %s' % os.path.basename(path), fh)

		elif os.path.isdir(path):
			self.__mkd_cd(os.path.basename(os.path.normpath(path)))

			for f in glob.glob(os.path.join(path, '*')):
				self.uploadThis(f)

			self.ftp.cwd('..')


	def push(self, path, version, platform):
		print 'Trying to push ', path, 'on ', self.server, '...' 
		res = False

		try:
			self.__login(version, platform)

			if self.__file_exists('guard_ready'):
				print 'Data already exists, no need to push'

			elif self.__file_exists('guard_push'):
				print 'Data already in progress'

			else:
				print 'Data does not presists on server yet'
				
				arch_name = 'bcm_data'
				arch_path = os.path.join(tempfile.gettempdir(), arch_name)

				print 'archiving...'
				shutil.make_archive(arch_path, 'tar', path)
			
				bio = io.BytesIO(' ')
				self.ftp.storbinary('STOR guard_push', bio)

				print 'uploading...'
				self.uploadThis(arch_path + '.tar')

				print 'setting guard...'
				self.ftp.storbinary('STOR guard_ready', bio)
				print 'done!'
				res = True
					
		except:
			print 'Somthing went wrong'

		finally:
			try:
				self.ftp.delete('guard_push')
				self.ftp.quit()
			except:
				print 'Failed to remove push guard & close ftp connection'			

		return res


	def pull(self, path, version, platform):
		res = False
		print 'Trying to pull', path, 'from', self.server 
		
		try:
			self.__login(version, platform)

			arch_file = 'bcm_data.tar'
			arch_path = os.path.join(tempfile.gettempdir(), arch_file)

			if self.__file_exists('guard_ready'):
				print 'Data exists on the server'

				print 'downloading...'
				with open(arch_path, 'wb') as fh:
					self.ftp.retrbinary('RETR %s' % arch_file, fh.write)

				print 'extracting...'
				tar = tarfile.open(arch_path)
				tar.extractall(path)
				tar.close();
				
				print 'done!'
				res = True
				
			else:
				print 'Data does not exists'

		except:
			print 'Somthing went wrong'
		
		finally:
			try:
				self.ftp.quit()
			except:
				print 'Failed to close ftp session'
		
		return res


	def __file_exists(self, filename):
		filelist = [] #to store all files
		self.ftp.retrlines('LIST',filelist.append)    # append to list  

		for f in filelist:
			if f.split()[-1] == filename:
				return True

		return False


def main():
	import argparse

	parser = argparse.ArgumentParser(description='Push binaries to ftp server with respect to version and target platform')
	parser.add_argument('command', help='Command can be push or pull')
	parser.add_argument('server', help='Destination server name')
	parser.add_argument('path', help='Path to be stored on server')
	parser.add_argument('version', help='Version of binaries')
	parser.add_argument('platform', help='Target platform name')
	parser.add_argument('--user', default='bcm', help='ftp username')
	parser.add_argument('--passwd', default='123', help='ftp userpass')

	args = parser.parse_args()
	bcm = FtpBCM(args.server, args.user, args.passwd)
	ret = False;

	if args.command == 'push':
		ret = bcm.push(args.path, args.version, args.platform)
	elif args.command == 'pull':
		ret = bcm.pull(args.path, args.version, args.platform)
	else:
		print 'Unexpected command: ', args.command
		raise Exception('Unexpected command')

	if False==ret:
		raise Exception('Failed to execute command')


if __name__ == "__main__":
    main()


