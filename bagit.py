#!/usr/bin/env python3

"""
BagIt is a directory, filename convention for bundling an arbitrary set of
files with a manifest, checksums, and additional metadata. More about BagIt
can be found at:
    http://purl.org/net/bagit
bagit.py is a pure python drop in library and command line tool for creating,
and working with BagIt directories:
For more help see:
    % bagit.py --help
"""

import argparse
import hashlib
import os
import shutil
import sys
import tempfile

CHECKSUM_NAMES = ['md5', 'sha1', 'sha256', 'sha512']
READ_BUFFER = 1048576

class Version(object):
  major = 0
  minor = 97

  def __init__(self, major, minor):
    self.major = major
    self.minor = minor

  def __str__(self):
    return "{}.{}".format(self.major, self.minor)

class FetchItem(object):
  url = ""
  length = 0
  path = ""

  def __init__(self, url, length, path):
    self.url = url
    self.length = length
    self.path = path

class Manifest(object):
  algorithm = "md5"
  fileToChecksumMap = {}

  def __init__(self, algorithm):
    if algorithm not in CHECKSUM_NAMES:
      raise ValueError("{} not one of the accepted checksum algorithms: {}".format(algorithm, CHECKSUM_NAMES))
    self.algorithm = algorithm

class Bag(object):
  def __init__(self):
    self.version = Version(0, 97)
    self.fileEncoding = "utf-8"
    self.itemsToFetch = []
    self.payLoadManifests = []
    self.tagManifests = []
    self.metadata = {}
    self.rootDir = tempfile.mkdtemp()
    #TODO

def create_parser():
    parser = argparse.ArgumentParser(
        description=__doc__.strip(), formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-d", "--dryrun", help="Just print out what would have happened.", action="store_true")
    parser.add_argument("--bag", nargs="*", help="The directory or directories to bag. if --bag-to-directory is not specified they are bagged in place")
    parser.add_argument("--bag-to-directory", help="directory to bag to.")
    parser.add_argument("--update-tag-manifests", help="regenerate tag manifest(s). useful if they have been edited manually.", action="store_true")
    parser.add_argument("--checksum-algorithm", help="which checksum algorithm to use when generating a manifest. Defaults to md5", choices=["md5", "sha1", "sha256", "sha512"], default="md5")
    parser.add_argument("--is-valid", nargs="*", help="verify that the bag(s) are valid. A bag is valid if it is complete and every checksum has been verified against the contents of its corresponding file.")
    parser.add_argument("--is-complete", nargs="*", help="verify that the bag(s) are complete. See https://tools.ietf.org/html/draft-kunze-bagit-13#section-3 for more information on what complete means.")

    return parser

def bag_in_place(directory, *, dryrun=False, algorithm="md5"):
    bag = Bag()
    bag.rootDir = directory

    dataDir = _create_data_directory(directory, dryrun=dryrun)
    _move_files_to_data_dir(directory, dataDir, dryrun=dryrun)
    _create_bagit_file(directory, bag.version, dryrun=dryrun)

    payloadManifest = _create_payloadManifest(dataDir, algorithm, dryrun=dryrun)
    bag.payLoadManifests.append(payloadManifest)
    
    _write_payload_manifest(directory, payloadManifest, dryrun=dryrun)

    return bag

def _create_data_directory(directory, *, dryrun=False):
  dataDir = os.path.join(directory, "data")
  if not dryrun:
    os.makedirs(dataDir)
  else:
    print("would have created {}".format(dataDir))
  return dataDir

def _move_files_to_data_dir(directory, dataDir, *, dryrun=False):
  for file in os.listdir(directory):
    if os.path.basename(file) is not "data":
      if not dryrun:
        shutil.move(os.path.join(directory, file), dataDir)
      else:
        print("Would have moved {} to {}".format(os.path.join(directory, file), os.path.join(dataDir, file)))

def _create_bagit_file(directory, version, *, dryrun=False):
  if not dryrun:
    bagitFile = open(os.path.join(directory, "bagit.txt"), 'w')
    bagitFile.write("BagIt-Version: {}\nTag-File-Character-Encoding: UTF-8".format(version))
  else:
    print("Would have created {}".format(os.path.join(directory, "bagit.txt")))

def _create_payloadManifest(dataDir, algorithm, *, dryrun=False):
  if not dryrun:
    payloadManifest = Manifest(algorithm=algorithm)
    for dirName, _, fileList in os.walk(dataDir):
      for file in fileList:
        fullPath = os.path.join(dirName, file)
        try:
          hasher = hashlib.new(payloadManifest.algorithm)
          with open(fullPath, 'rb') as f:
            while True:
              block = f.read(1048576)
              if not block:
                break
              hasher.update(block)
          payloadManifest.fileToChecksumMap[fullPath] = hasher.hexdigest()
        except:
          raise
    return payloadManifest
  else:
    print("Would have created a new payload manifest using algorithm {}".format(algorithm))

def _write_payload_manifest(directory, payloadManifest, *, dryrun=False):
  manifestName = os.path.join(directory, "manifest-{}.txt".format(payloadManifest.algorithm))
  if not dryrun:
    try:
      with open(manifestName, 'w') as manifest:
        for key in payloadManifest.fileToChecksumMap:
          relativePath = os.path.relpath(key, directory)
          manifest.write("{} {}\n".format(payloadManifest.fileToChecksumMap[key], relativePath))
    except:
      raise
  else:
    print("Would have written payload manifest {}".format(manifestName))

def bag_to_directory(from_directory, to_directory, *, dryrun=False, algorithm="md5"):
    #create/update manifest with checksums from from_directory before moving
    #copy files to destination
    #verify?
    pass

def update_tag_manifests(bag_directory, *, dryrun=False):
    #get list of tag manifests
    #update each checksum
    pass

def is_valid(bag_directory, *, dryrun=False):
    #do is complete...
    #check all checksums from manifest(s)
    pass

def is_complete(bag_directory, *, dryrun=False):
    #checkFetchItemsExist
    #checkBagitFileExists
    #checkPayloadDirectoryExists
    #checkIfAtLeastOnePayloadManifestsExist
    #checkAllFilesListedInManifestExist
    #checkAllFilesInPayloadDirAreListedInAManifest
    pass


def main():
    parser = create_parser()
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()
    #TODO

if __name__ == "__main__":
    main()
