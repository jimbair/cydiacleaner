#!/usr/bin/python
# A script to validate repos
# v.01 - Development 

# Modules we need
import os
import socket
import sys
import urllib2

# Varibles we need
#repoFolder = '/etc/apt/sources.list.d/'
repoFolder = 'repos/'
mirrorFiles = [ 'Release.gpg', 'en.bz2', 'Release', 'Packages.bz2', 'Packages.gz', 'Packages' ]
exclusion='cydia.list'

def isValidHTTP(url=''):
	"""
	Function to validate if a given URL is valid. Used to 
	find 2xx status codes over HTTP. Returns True/False
	"""
	try:
		urllib2.urlopen(url)
	except:
		return False
	else:
		return True

def isValidHostname(host=''):
	"""
	Function to validate of a given hostname is valid. Used 
	to find bad hostnames that timeout. Returns True/False
	"""
	try:
		socket.gethostbyname(host)
	except:
		return False
	else:
		return True

def echo(message=''):
	"""
	Function to emulate echo -en type functionality since
	print acts weird at times and py3k changes print as well.
	"""
	sys.stdout.write(message)
	sys.stdout.flush()


if __name__ == '__main__':
	# Find our files.
	if os.path.isdir(repoFolder):
		repoFiles = os.listdir(repoFolder)
	else:
		sys.stderr.write('Our repo folder ' + repoFolder + ' is missing.\n')
		sys.exit(1)

	# Remove cydia.list (it should be here)
	if repoFiles.count(exclusion) > 0:
		repoFiles.remove(exclusion)
	else:
		 sys.stderr.write(exclusion + ' is missing from ' + repoFolder)
		 sys.stderr.write(' This repo is not valid or something has changed.\n')
		 sys.exit(1)

	# Remove invalid stuff
	for file in repoFiles:
		ourExt = os.path.splitext(file)[-1]
		if ourExt != '.list':
			repoFiles.remove(file)

	# Time to build our lists
	repoList = []
	for file in repoFiles:
		# Open the file and save it as a list
		data = open(repoFolder + file, 'r')
		result = data.readlines()
		data.close()
		# take each line and split it by spaces
		for line in result:
			ourValues = line.split()
			# Make sure we don't have a blank line
			if len(ourValues) > 0:
				# Pull the path to the mirror and it's dist value
				if ourValues[0] == 'deb':
					repoList.append([ file, ourValues[1], ourValues[2] ])

	# Now that we have our repo list. Time to start testing things!
	for item in repoList:

		filename = item[0]
		repo = item[1]
		dist = item[2]
		hostname = repo.split('/')[2]
		validRepo = False

		if isValidHostname(hostname):
			# Check the root of the repo
			for file in mirrorFiles:
				link = repo + file
				if isValidHTTP(link):
					validRepo = True
			# Now check the dist
			if not validRepo:
				for file in mirrorFiles:
					if dist == './':
						break
					link = repo + 'dists/' + dist + '/' + file
					if isValidHTTP(link):
						validRepo = True
						break
			# Last chance, done for iphonehe since their repo is weird.
			# This checks the root of the hostname for the files.
			if not validRepo:
				for file in mirrorFiles:
					link = 'http://' + hostname + '/' + file
					if isValidHTTP(link):
						validRepo = True
						break

		echo('Finished up on ' + repo + ' and it is ' + str(validRepo) + '\n')
