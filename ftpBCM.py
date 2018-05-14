#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ftplib
import io
import os
import glob
import shutil
import tarfile
import tempfile
import socket
import hashlib
import random
import string


class BcmChecksumMismatch(Exception):
	def __init__(self, value):
		self.value = value
	def __str__(self):
		return repr(self.value)


class FtpBCM:
	def __init__(self, server, user, passwd, project):
		self.server = server
		self.user = user
		self.passwd = passwd
		self.project = project


	def __login(self, version, platform):
		try:
			self.ftp = ftplib.FTP(self.server)
			self.ftp.login(self.user, self.passwd)
		except Exception as e:
			print "Failed fo login", self.server
			raise e
		self.__mkd_cd('bcm')
		self.__mkd_cd(self.project)
		self.__mkd_cd(version)
		self.__mkd_cd(platform)


	def __mkd_cd(self, dirname):
		try:
			self.ftp.mkd(dirname)
		except ftplib.error_perm as e:
			print(e)

		self.ftp.cwd(dirname)


	def __uploadThis(self, path):
		if os.path.isfile(path):
			with open(path, 'rb') as fh:
				self.ftp.storbinary('STOR %s' % os.path.basename(path), fh)

		elif os.path.isdir(path):
			self.__mkd_cd(os.path.basename(os.path.normpath(path)))

			for f in glob.glob(os.path.join(path, '*')):
				self.__uploadThis(f)

			self.ftp.cwd('..')


	def __md5(self, file_directory):
		file_directory = os.path.abspath(file_directory)
		hash_md5 = hashlib.md5()

		for root, dirs, filenames in os.walk(file_directory):
			for fname in filenames:
				fpath = os.path.join(root, fname)
				with open(fpath, "rb") as f:
					for chunk in iter(lambda: f.read(4096), b""):
						hash_md5.update(chunk)

		return hash_md5.hexdigest()


	def __check_md5(self, md5sum):
		if self.__file_exists('md5'):
			filename = 'ftpbcm_md5_{}'.format(''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(8)))
			md5_server = os.path.join(tempfile.gettempdir(), filename)
			with open(md5_server, 'wb') as fh:
				self.ftp.retrbinary('RETR %s' % 'md5', fh.write)
			with open(md5_server, 'rb') as fh:
				sum_on_ftp = fh.read()
				return sum_on_ftp.strip() == md5sum.strip()
		return False


	def push(self, path, version, platform):
		print 'Trying to push', path, 'to', self.server
		print '    Version:', version
		print '    Platform:', platform
		res = False

		try:
			self.__login(version, platform)

			print '...Archiving...'
			arch_name = 'bcm_data'
			arch_path = os.path.join(tempfile.gettempdir(), arch_name)
			shutil.make_archive(arch_path, 'gztar', path)
			arch_path += '.tar.gz'

			print '...calc md5...'
			md5sum = self.__md5(path)

			if self.__file_exists('guard_ready'):
				print 'The binary is already on the server. Stopping the upload.'

			elif self.__file_exists('guard_push'):
				print 'The binary us being uploaded to the server by someone else. Stopping the upload.'

			else:
				print 'The binary was not found on the server. Starting the upload...'

				hostname = os.getenv('HOSTNAME', socket.gethostname())
				bio = io.BytesIO(hostname)
				self.ftp.storbinary('STOR guard_push', bio)

				bio = io.BytesIO(md5sum)
				self.ftp.storbinary('STOR md5', bio)

				print '...Uploading...'
				self.__uploadThis(arch_path)
				self.ftp.storbinary('STOR arch_name', io.BytesIO(os.path.basename(arch_path)))

				print '...Setting guard...'
				bio = io.BytesIO(hostname)
				self.ftp.storbinary('STOR guard_ready', bio)
				print '...Done!'
				res = True

		except BcmChecksumMismatch as e:
			print e
			raise e

		except Exception as e:
			print 'Error occured: ', e

		except:
			print 'Something went wrong!'

		finally:
			try:
				self.ftp.delete('guard_push')
				self.ftp.quit()
			except:
				print 'Failed to remove push guard & close ftp connection!'

		return res


	def pull(self, path, version, platform):
		res = False
		path = os.path.normpath(path)
		print 'Trying to pull', path, 'from', self.server
		print '    Version:', version
		print '    Platform:', platform
		
		try:
			self.__login(version, platform)

			arch_file = 'bcm_data.tar'
			arch_path = os.path.join(tempfile.gettempdir(), arch_file)

			if self.__file_exists('guard_ready'):
				print 'The binary has been found on on the server, staring download...'

				print '...Downloading...'
				with open(arch_path, 'wb') as fh:
					self.ftp.retrbinary('RETR %s' % arch_file, fh.write)

				self.__backup(path)

				print '...Extracting...'
				tar = tarfile.open(arch_path)
				tar.extractall(path)
				tar.close();
				
				print '...Done!'
				res = True

			else:
				print 'The pre-built binary was not found on the server, sorry.'

		except Exception as e:
			print 'Exception:', e

		except:
			print 'Something went wrong!'

		finally:
			try:
				self.ftp.quit()
			except:
				print 'Failed to close ftp session!'

		return res


	def __backup(self, path):
		if os.path.exists(path):
			print 'Backing up old', path, '...'
			bak_path = path + '.bak'

			if os.path.exists(bak_path):
				shutil.rmtree(bak_path)

			shutil.move(path, bak_path)
			print '...', path, 'has been moved to', bak_path


	def __file_exists(self, filename):
		filelist = [] #to store all files
		self.ftp.retrlines('LIST',filelist.append)    # append to list

		for f in filelist:
			if f.split()[-1] == filename:
				return True

		return False


def main():
	import argparse

	parser = argparse.ArgumentParser(description='Upload binaries to FTP server with respect to version and target platform.')
	parser.add_argument('command', help='Command can be push or pull')
	parser.add_argument('server', help='Destination FTP server name')
	parser.add_argument('path', help='Path to be stored on server')
	parser.add_argument('version', help='Version of binaries')
	parser.add_argument('platform', help='Target platform name')
	parser.add_argument('--user', default='anonymous', help='ftp username')
	parser.add_argument('--passwd', default='anonymous@', help='ftp userpass')
	parser.add_argument('--project', default='default', help='project name')

	args = parser.parse_args()
	bcm = FtpBCM(args.server, args.user, args.passwd, args.project)
	ret = False;

	if args.command == 'push':
		ret = bcm.push(args.path, args.version, args.platform)
	elif args.command == 'pull':
		ret = bcm.pull(args.path, args.version, args.platform)
	else:
		print 'Unexpected command: ', args.command
		raise Exception('Unexpected command!')

	if False==ret:
		raise Exception('Failed to execute command!')


if __name__ == "__main__":
    main()

