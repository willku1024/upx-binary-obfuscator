# Author: k1rk#1999 on discord
# Date: 27 July 2020 

# Standard library #
from sys import exit, argv
import os
import subprocess
import argparse

# constant variables
usage = f"Usage: python {argv[0]} --upx ~/upx --files /root/myexe /$HOME/file"
author = "Author: k1rk#1999"
direc = "/build/"

# global functions
run = lambda cmd: subprocess.run(cmd.split(' '), capture_output=True)
debug = lambda message, raw: f"Info: {message}\nShell Output: {raw}"
is_elf = lambda path: "ELF 64-bit LSB executable" in run(f"file {path}").stdout.decode()

# program init #
def _init():
    """add arguments for the program and validate them"""
    parser = argparse.ArgumentParser(
        description="Coded by kirk, compress a raw elf binary and change the upx magic numbers to prevent analysis and reverse engineering"
    )

    # list of paths to the elf binaries #
    parser.add_argument(
        "--files", 
        type=str, 
        help="Space Delimited List Of File Paths to an executable binary e.g (/root/main, /$HOME/myelf, /direc/anotherelf)",
        nargs="+",
        required=True
    )
    
    # upx path if left none assume upx is symlinked and or added to path #
    parser.add_argument(
        "--upx",
        type=str,
        help="Absoloute path to the upx binary if left none program will assume upx is sym linked and attempt the 'upx' command"
    )

    print(
        f"Note: This Program Deletes your old executable\nUsage: {usage}\n"
    )

    return _validate(parser.parse_args())

def _validate(args):

    # validate arguments #
    paths = args.files


    # check that build directory does not already exist #
    if os.path.exists(os.path.abspath(os.getcwd() + direc)):
        print(
            debug(
                f"Directory {direc} Already Exists",
                "None"
            )
        )
        exit(1)
    
    os.mkdir(os.path.abspath(os.getcwd() + direc))

    if not any(os.path.exists(path) for path in paths):
        print(
            debug(
                "Invalid path provied in list provided by --files",
                "None"
            )
        )
        exit(1)

    # upx path is empty
    if not args.upx:
        
        # attempt to find the upx path
        path_to_upx = run("which upx").stdout.decode().strip()
        
        if not path_to_upx:
            print(
                debug(
                    "Could not find the upx path please specify one", 
                    "None"
                )
            )
            exit(1)
        
    # check to make sure upx path is exists
    if not os.path.exists(path_to_upx):
        print(
            debug(
                "Invalid path passed to --upx flag",
                "None"
            )
        )
        exit(1)

    # check thart the path is actually pointing to upx
    if (out := run(f"{path_to_upx} --version")).returncode != 0:
        print(
            debug(
                "Upx path is valid but does not point to a valid upx binary", 
                out.stdout.decode().strip()
            )
        )
        exit(1)

    # check all files in the list are elf executables
    for bin_path in paths:
        if not is_elf(bin_path):
            print(
                debug(
                    "Invalid ELF path passed near %s" % bin_path, 
                    "None"
                )
            )
            exit(1)

    # return all the valid paths and the path to the upx bin
    return paths, path_to_upx

def main(upx, files):
    """
    Main function of the program loops through 
    all the files and calls the
    Build and edit classess
    """

    # loop through all files and build them #
    for file in files:
        if not Build(file, upx).run(): 
            print(
                debug(
                    f"Build Failed: {file}",
                    "None"
                )
            )
            continue  
        print(
            debug(
                f"Build Succeeded: {file}",
                "None"
            )
        )
    
    # loop through all files and attempt to edit the bin #
    for file in files:
        if not Edit(file).run():
            print(
                debug(
                    f"Bin Edit Failed: {file}",
                    "None"
                )
            )
            continue
        print(
            debug(
                f"Bin Edit Succeeded: {file}",
                "None"
            )
        )

    # program finsihed #
    print(
        f"\033[35mFinished: Coded By {author}\033[0m",
    )

    exit(0)

class Build:
    """Main Class For Building the elf with upx"""
    def __init__(self, path, upx_path):
        self.file = path
        self.upx_path = upx_path

    def pack_files(self):
        """attempt to run upx on all the files in the directory"""
        if (out := run(f"{os.path.abspath(self.upx_path)} --ultra-brute {os.path.abspath(self.file)}")).returncode != 0:
            print(
                debug(
                    f"Failed To Run upx on {self.file}",
                    out.stderr.decode()
                )
            )
            return False
        return True

    def run(self):
        """run the program"""
        return self.pack_files()

class Edit:
    # class Variables #
    copyright_string = r"$Info: This file is packed with the UPX executable packer http://upx.sf.net $\n\x00$Id: UPX 3.95 Copyright (C) 1996-2018 the UPX Team. All Rights Reserved.".encode()
    magic_constant_string = "UPX!".encode()
    replace_string = "9812".encode()

    """Main Class for opening and editing all the files"""
    def __init__(self, file):
        self.file = file 
        self.file_name = self.file.split('/')[-1].strip('/')


    def edit(self):
        
        # use os.abspath here just to be safe #
        # open the file in binary mode as we need to work with raw bytes# #
        with open(os.path.abspath(self.file), "rb") as original, \
            open(f"temp", "wb+") as new:

            # replace all data from the raw byte strings 
            data = original.\
                read() \
                    .replace(
                        Edit.magic_constant_string, 
                        Edit.replace_string
                    ) \
                    .replace(
                        Edit.copyright_string,
                        b''
                    )

            # write the edited data to the new file #
            new.write(data)

        # remove the old file # 
        if (out := run(f"rm {os.path.abspath(self.file)}")).returncode != 0:
            print(
                debug(
                    "Failed To Delete %s after editing" % self.file,
                    out.stderr.decode().strip()
                )
            )
            return False
        return True
            
    def add_to_direc(self):
        """function to move the file into the specified directory"""
        if (out := run(f"mv temp {os.path.abspath(os.getcwd() + direc + self.file_name)}")).returncode != 0:
            print(
                debug(
                    "Failed To Move %s into %s" % (self.file_name, direc),
                    out.stderr.decode().strip()
                )
            )
            return False
        return True
    
    def run(self):
        """"call the edit and add_to_direc functions"""
        return False if not any([self.edit(), self.add_to_direc()]) else True

if __name__ == '__main__':
    """Entry Point of program"""
    files, upx = _init()
    main(upx, files)
