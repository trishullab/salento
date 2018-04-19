"""
# ****************************************************************************
#
# GOVERNMENT PURPOSE RIGHTS
#
# Contract Number: FA8750-15-2-0270 (Prime: William Marsh Rice University)
# Contractor Name: GrammaTech, Inc. (Right Holder - subaward R18683)
# Contractor Address: 531 Esty Street, Ithaca, NY  14850
# Expiration Date: 22 September 2023
#
# The Government's rights to use, modify, reproduce, release, perform,
# display, or disclose this software are restricted by DFARS 252.227-7014
# Rights in Noncommercial Computer Software and Noncommercial Computer Software
# Documentation clause contained in the above identified contract.
# No restrictions apply after the expiration date shown above.
# Any reproduction of the software or portions thereof marked with this legend
# must also reproduce the markings and any copyright.
#
# ****************************************************************************
# ****************************************************************************
#
# (c) 2014-2018 GrammaTech, Inc.  All rights reserved.
#
# ****************************************************************************

"""

# Script usage : This script converts sarif file generated remotely to local folder

import argparse
import json
import subprocess
import os


def process_file(sarif_file, local_folder, prefix_location):
    """
    script to convert the process file
    :param sarif_file: sarif file name
    :param local_folder: local folder to store the files
    :param prefix_location: the prefix location to remove
    :return: list of files
    """

    file_list = set()
    with open(sarif_file, 'r') as fread:
        sarif_data = json.load(fread)
        runs_data = sarif_data["runs"]
        for data in runs_data:
            for result in data["results"]:
                # update the location
                for loc in result["locations"]:
                    filename = loc["resultFile"]["uri"]
                    local_file = filename.replace(prefix_location, local_folder)
                    file_list.add(filename.replace("file://", ""))
                    loc["resultFile"]["uri"] = local_file
                # update  the codeflows
                for code_loc in result["codeFlows"]:
                    for loc in code_loc["locations"]:
                        filename = loc["physicalLocation"]["uri"]
                        local_file = filename.replace(prefix_location, local_folder)
                        file_list.add(filename.replace("file://", ""))
                        loc["physicalLocation"]["uri"] = local_file
    with open(sarif_file, 'w') as fwrite:
        json.dump(sarif_data, fwrite, indent=2)

    return file_list


def copy_files(filelist, local_folder, prefix_location, remote_server):
    """
    function to copy the filename
    :param filelist: list of the files to copy
    :param local_folder: the destination of the local folder
    :param prefix_location: the prefix location to remove
    :return: list of files that failed to copy
    """
    # list of files that were not copied
    failing_set = set()
    for files in filelist:
        # create intermediate directories
        local_file = files.replace(prefix_location, local_folder)
        dir_name = os.path.dirname(local_file)
        # if directory doesn't exists create one
        if not os.path.exists(dir_name):
            cmd = ['mkdir', '-p', dir_name]
            subprocess.check_call(cmd)
        remote_file = remote_server + ":" + files
        if not os.path.exists(local_file):
            cmd = ['scp', remote_file, local_file]
            status = subprocess.call(cmd)
            if status != 0:
                failing_set.add(remote_file)
    return failing_set


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=
        "Modify and sarif file to set local file path, copy the relevant file")
    parser.add_argument(
        '--sarif_file',
        required=True,
        type=str,
        help="Data file with forward raw probabilities")
    parser.add_argument(
        '--local_folder',
        required=True,
        type=str,
        help="Local folder where to copy the file")
    parser.add_argument(
        '--remote_server',
        required=True,
        type=str,
        help="Remote Server")
    parser.add_argument(
        '--prefix_location',
        required=True,
        type=str,
        help="prefix location to remove")

    args = parser.parse_args()
    if not os.path.exists(args.local_folder):
        os.mkdir(args.local_folder)
    files_list = process_file(args.sarif_file, args.local_folder, args.prefix_location)
    failing_cpy = copy_files(files_list, args.local_folder, args.prefix_location, args.remote_server)
    if len(failing_cpy):
        print("the files that could be copied \n", json.dumps(list(failing_cpy), indent=2))
