#!/usr/bin/python
# A script to validate repos
# v.01 - Development 
# Copyright (C) 2009  James Bair <james.d.bair@gmail.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# Modules we need
import os
import shutil
import socket
import sys
import urllib2

# Varibles we need
#repoFolder = '/etc/apt/sources.list.d/'
repoFolder = 'repos/' # For testing reasons
retiredFolder = repoFolder + 'retired/'
mirrorFiles = [ 'Release.gpg', 'en.bz2', 'Release', 'Packages.bz2', 'Packages.gz', 'Packages' ]
exclusion='cydia.list'

def isValidHTTP(url=''):
	"""
	Function to validate a given URL using the P. Returns True/False
	"""
	try:
		urllib2.urlopen(url)
	except:
		return False

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

	return True

def echo(message=''):
	"""
	Function to emulate echo -en type functionality since
	print acts weird at times and py3k changes print as well.
	"""
	sys.stdout.write(message)
	sys.stdout.flush()

def findRepoFiles(folder='', exclusion=None):
	"""
	Function to search a folder for repo files. If given an exclusion, 
	will remove it from the list (exclusion should be a string).
	"""
	
	# Find our files.
	if os.path.isdir(folder):
		results = os.listdir(folder)
	# Make sure our folder is actually there.
	else:
		sys.stderr.write('Our repo folder ' + folder + ' is missing.\n')
		sys.exit(1)

	# Remove cydia.list (it should be here)
	if exclusion is not None:
		if results.count(exclusion) > 0:
			results.remove(exclusion)

	# We only want *.list
	for file in results:
		ourExt = os.path.splitext(file)[-1]
		if ourExt != '.list':
			results.remove(file)

	return results

def findRepos(folder='', files=[]):
	"""
	Function to pull the apt repos out of a list of files from a given folder.
	"""
	results = []
	for file in files:
		# Open the file and save it to a list
		data = open(repoFolder + file, 'r')
		result = data.readlines()
		data.close()
		# Split our string by spaces
		for line in result:
			ourValues = line.split()
			# Make sure we don't have a blank line
			if len(ourValues) > 0:
				# Validate the line and get our info
				if ourValues[0] == 'deb':
					results.append([ file, ourValues[1], ourValues[2] ])
	return results

def checkRepos(ourList=[]):
	"""
	Function to verify if a list of repos are valid.
	Expects a lists of lists, with each child list having:
	[ Filename, Repo, Dist ]
	"""
	result = []
	for item in ourList:
		# Aliases are good.
		filename = item[0]
		repo = item[1]
		dist = item[2]
		hostname = repo.split('/')[2]
		# All repos are false until proven otherwise
		validRepo = False

		# Make sure it resolves. Saves time instead of urllib2 doing this.
		if isValidHostname(hostname):
			# Check the repo itself for the files
			for file in mirrorFiles:
				link = repo + file
				if isValidHTTP(link):
					validRepo = True
			# Now check the dist folder
			if not validRepo:
				for file in mirrorFiles:
					# If ./ is given for dist, it's not used.
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

			# If STILL not valid, all aboard the failboat.
			if not validRepo:
				item.append('Not a valid repository.')
				result.append(item)
		else:
			item.append('Hostname does not resolve.')
			result.append(item)
	return result


############
### MAIN ###
############

if __name__ == '__main__':

	# If this is our first time, create our retired folder
	if not os.path.isdir(retiredFolder):
		echo("No retired folder present, creating...")
		os.mkdir(retiredFolder)
		echo("done.\n")

	# Time to build our list of repos with the info we need
	repoFiles = findRepoFiles(repoFolder, exclusion)
	repoList = findRepos(repoFolder, repoFiles)
	repoNumber = len(repoList)
	# Make sure we found at least 1 repo
	if repoNumber < 1:
		sys.stderr.write('Unable to find our repos! Something is wrong.\n')
		sys.exit(1)

	# Now that we have our repo list. Time to start testing things!
	echo('Beginning scan of all ' + str(repoNumber) + ' repositories, get some coffee...')
	# Find our failed repos
	failedRepos = checkRepos(repoList)
	# Done scanning repos
	echo('done!\n')
	# Check how many bad repos we found.
	failedNumber = len(failedRepos)
	# If we found nothing, all is well
	if failedNumber == 0:
		echo('No failed repos present! All is well on this iPhone.\n')
		sys.exit(0)
	else:
		# Not needed for function, but dang it I love grammar.
		if failedNumber > 1:
			echo('\nWe have found ' + str(failedNumber) + ' bad repos.\n')
			echo('Here are the following offending repos:\n')
		else:
			echo('\nWe have found ' + str(failedNumber) + ' bad repo.\n')
			echo('Here is the offending repo:\n')

		for item in failedRepos:
			# Aliases are good.
			filename = item[0]
			repo = item[1]
			hostname = repo.split('/')[2]
			error = item[-1]
			echo('\nHostname:\t' + hostname)
			echo('\nFull Repo:\t' + repo)
			echo('\nFilename:\t' + filename)
			echo('\nRepo Error:\t' + error + '\n')

		# Retire our bad repos
		echo('\n')
		for item in failedRepos:
			filename = item[0]
			liveFile = repoFolder + filename
			retiredFile = retiredFolder + filename
			echo('Retiring ' + filename + '...')
			shutil.move(liveFile, retiredFile)
			echo('done.\n')
		echo('All invalid repositories have been retired.\n')
		sys.exit(0)
