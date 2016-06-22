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
import re
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
  length = ""
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

def create_parser():
    parser = argparse.ArgumentParser(description=__doc__.strip(), formatter_class=argparse.RawTextHelpFormatter)
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

    data_dir = _create_data_directory(directory, dryrun=dryrun)
    _move_files_to_data_dir(directory, data_dir, dryrun=dryrun)
    _create_bagit_file(directory, bag.version, dryrun=dryrun)

    payload_manifest = _create_payload_manifest(data_dir, algorithm)
    bag.payLoadManifests.append(payload_manifest)
    
    _write_payload_manifest(directory, payload_manifest, dryrun=dryrun)
    print("Completed bag in place for directory {}".format(directory))
    return bag

def _create_data_directory(directory, *, dryrun=False):
  data_dir = os.path.join(directory, "data")
  if not dryrun:
    os.makedirs(data_dir)
  else:
    print("would have created {}".format(data_dir))
  return data_dir

def _move_files_to_data_dir(directory, data_dir, *, dryrun=False):
  for filename in os.listdir(directory):
    if os.path.basename(filename) is not "data":
      if not dryrun:
        shutil.move(os.path.join(directory, filename), data_dir)
      else:
        print("Would have moved {} to {}".format(os.path.join(directory, filename), os.path.join(data_dir, filename)))

def _create_bagit_file(directory, version, *, dryrun=False):
  if not dryrun:
    bagit_file = open(os.path.join(directory, "bagit.txt"), 'w')
    bagit_file.write("BagIt-Version: {}\nTag-File-Character-Encoding: UTF-8".format(version))
  else:
    print("Would have created {}".format(os.path.join(directory, "bagit.txt")))

def _create_payload_manifest(data_dir, algorithm):
    payload_manifest = Manifest(algorithm=algorithm)
    for dirName, _, fileList in os.walk(data_dir):
      for file in fileList:
        full_path = os.path.join(dirName, file)
        try:
          hasher = hashlib.new(payload_manifest.algorithm)
          payload_manifest.fileToChecksumMap[full_path] = _hash_file(hasher, full_path)
        except:
          raise
    return payload_manifest

def _hash_file(hasher, full_path):
    with open(full_path, 'rb') as f:
        while True:
            block = f.read(READ_BUFFER)
            if not block:
                break
            hasher.update(block)
    return hasher.hexdigest()

def _write_payload_manifest(directory, payload_manifest, *, dryrun=False):
  manifest_name = os.path.join(directory, "manifest-{}.txt".format(payload_manifest.algorithm))
  if not dryrun:
    try:
      with open(manifest_name, 'w') as manifest:
        for key in payload_manifest.fileToChecksumMap:
          relative_path = os.path.relpath(key, directory)
          manifest.write("{} {}\n".format(payload_manifest.fileToChecksumMap[key], relative_path))
    except:
      raise
  else:
    print("Would have written payload manifest {}".format(manifest_name))

def bag_to_directory(from_directories, to_directory, *, dryrun=False, algorithm="md5"):
    print("NOT YET IMPLEMENTED")
    #create/update manifest with checksums from from_directory before moving
    #copy files to destination
    #verify?
    print("completed bag directories {} to directory {}".format(from_directories, to_directory))

def update_tag_manifests(bag_directory, *, dryrun=False):
    print("NOT YET IMPLEMENTED")
#    for filename in os.listdir(bag_directory):
#        if filename.startswith("tagmanifest-"):
#
    #get list of tag manifests
    #update each checksum
    print("Completed updating tag manifest(s)")

def is_valid(bag_directory):
    #check all checksums from manifest(s)
    for name in os.listdir(bag_directory):
        if name.startswith("manifest-") or name.startswith("tagmanifest-"):
            filename = os.path.join(bag_directory, name)
            algorithm = re.split("-|\.", name)[1]
            with open(filename) as f:
                for line in f:
                    split_line = line.split(maxsplit=1)
                    full_path = os.path.join(bag_directory, split_line[1]).rstrip()
                    hasher = hashlib.new(algorithm)
                    calulated_hash = _hash_file(hasher, full_path)
                    if split_line[0] != calulated_hash:
                        print("File {} calculated hash {} does not match expected hash {}".format(split_line[1], calulated_hash, split_line[0]))
                        return False

    return is_complete(bag_directory)


def is_complete(bag_directory):
    all_files = _all_files_in_manifests(bag_directory)

    return _check_fetch_items_exist(bag_directory) and \
        _check_bagit_file_exists(bag_directory) and \
        _check_payload_directory_exists(bag_directory) and \
        _check_at_least_one_payload_manifest_exists(bag_directory) and \
        _check_all_files_in_manifests_exist(all_files) and \
        _check_all_files_in_payload_dir_exist_in_at_least_one_manifest(bag_directory, all_files)

def _check_fetch_items_exist(bag_directory):
    fetchfile = os.path.join(bag_directory, "fetch.txt")
    if os.path.isfile(fetchfile):
        with open(fetchfile) as f:
            for line in f:
                relative_path = line.split(maxsplit=2)[2]
                file_to_fetch = os.path.join(bag_directory, relative_path)
                if not os.path.isfile(file_to_fetch):
                    return False
    return True

def _check_bagit_file_exists(bag_directory):
    bagitfile = os.path.join(bag_directory, "bagit.txt")
    if not os.path.isfile(bagitfile):
        print("{} does not exist!".format(bagitfile))
        return False
    return True

def _check_payload_directory_exists(bag_directory):
    payload_directory = os.path.join(bag_directory, "data")
    if not os.path.isdir(payload_directory):
        print("{} does not exist!".format(payload_directory))
        return False
    return True

def _check_at_least_one_payload_manifest_exists(bag_directory):
    for filename in os.listdir(bag_directory):
        if filename.startswith("manifest-"):
            return True
    print("Could not find at least one payload manifest file!")
    return False

def _all_files_in_manifests(bag_directory):
    all_files = set()
    for filename in os.listdir(bag_directory):
        if filename.startswith("manifest-") or filename.startswith("tagmanifest-"):
            full_path = os.path.join(bag_directory, filename)
            with open(full_path) as f:
                for line in f:
                    all_files.add(os.path.join(bag_directory, line.split(maxsplit=1)[1].rstrip()))
    return all_files

def _check_all_files_in_manifests_exist(all_files):
    for filename in all_files:
        if not os.path.isfile(filename):
            print("File {} is listed in manifest but does not exist".format(filename))
            return False
    return True

def _check_all_files_in_payload_dir_exist_in_at_least_one_manifest(bag_directory, all_files):
    data_dir = os.path.join(bag_directory, "data")
    for dir_name, _, file_list in os.walk(data_dir):
        for name in file_list:
            filename = os.path.join(dir_name, )
            if os.path.isfile(filename) and filename not in all_files:
                print("File {} not in any manifest!".format(filename))
                return False
    return True


def main():
    parser = create_parser()
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()
    if args.bag is not None:
        if args.bag_to_directory is not None:
            bag_to_directory(args.bag, args.bag_to_directory, dryrun=args.dryrun, algorithm=args.checksum_algorithm)
        elif args.update_tag_manifests is True:
            for bag_directory in args.bag:
                update_tag_manifests(bag_directory, dryrun=args.dryrun)
        else:
            for bag_directory in args.bag:
                bag_in_place(bag_directory, dryrun=args.dryrun, algorithm=args.checksum_algorithm)
    elif args.is_valid is not None:
        for bag_directory in args.is_valid:
            if is_valid(bag_directory):
                print("Bag {} is valid".format(bag_directory))
    elif args.is_complete is not None:
        for bag_directory in args.is_complete:
            if is_complete(bag_directory):
                print("Bag {} is complete".format(bag_directory))

if __name__ == "__main__":
    main()
