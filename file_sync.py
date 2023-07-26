"""Sync service for copying the content of source folder into a given
replica folder. All operations on the files are logged depending on the 
indicators of given changes.

Args:
    source_path (str): Path of folder to keep track of
    replica_path (str): Path of folder where synched copy will be stored
    log_path (str): Path to store the log file at
    sync_interval (float): Number of minutes in between checks on the source folder

Raises:
    argparse.ArgumentTypeError: when validation of the input did not succeed

Returns:
    None
"""

import argparse
import hashing
import logging
import os
import pathlib
import shutil
import sys
import time
from typing import Any, Dict


replica_mapping: Dict[pathlib.Path, Any] = {}
source_mapping: Dict[pathlib.Path, Any] = {}


def update_replica_mapping(replica_path: str):
    """Method to update the list of files on the replica directory.
    It also generates the hash of the file contents for posterior checks.

    Args:
        replica_path (str): path of the folder to be checked for files
    """
    files_list = [
        file
        for file in pathlib.Path(replica_path).rglob("*")
        if pathlib.Path.is_file(file)
    ]
    replica_mapping.clear()
    for file in files_list:
        replica_mapping[file.relative_to(replica_path)] = hashing.hash_file(
            str(file)
        ).hexdigest()


def generate_source_mapping(source_path: str):
    """Method to update the list of files on the source directory.
    It also generates the hash of the file contents for posterior checks.

    Args:
        source_path (str): path of the folder to be checked for files
    """
    files_list = [
        file
        for file in pathlib.Path(source_path).rglob("*")
        if pathlib.Path.is_file(file)
    ]
    source_mapping.clear()
    for file in files_list:
        source_mapping[file.relative_to(source_path)] = hashing.hash_file(
            str(file)
        ).hexdigest()


def main(arguments):
    """main module

    Args:
        arguments (Namespace): parsed arguments
    """
    source_path: pathlib.Path = pathlib.Path(arguments.source_path)
    replica_path: pathlib.Path = pathlib.Path(arguments.replica_path)

    if not pathlib.Path.exists(source_path):
        logger.fatal(
            "Source path % is not present. No synchronization will be executed",
            source_path,
        )
        sys.exit(1)

    try:
        shutil.rmtree(replica_path, ignore_errors=True)
    except FileNotFoundError:
        pass

    shutil.copytree(src=source_path, dst=replica_path)

    try:
        while True:
            if not pathlib.Path.exists(pathlib.Path(source_path)):
                logger.fatal(
                    "Source path % is not present. No synchronization will be executed",
                    source_path,
                )
                sys.exit(1)

            generate_source_mapping(source_path)
            update_replica_mapping(replica_path)

            key: pathlib.Path
            value: Any
            for key, value in replica_mapping.items():
                if key in list(source_mapping.keys()):
                    if value in list(source_mapping.values()):
                        # NOTE: filename match, content match -> ignore
                        continue

                    # NOTE: filename match, content not match -> modification
                    logger.info("File % content has been modified.", key)
                    shutil.copy2(source_path / key, replica_path / key)
                    continue

                elif value in list(source_mapping.values()):
                    # NOTE: filename not match, content match -> rename/move
                    source_file_new_path: pathlib.Path = list(source_mapping.keys())[
                        list(source_mapping.values()).index(value)
                    ]
                    logger.info("File % has been moved to %", key, source_file_new_path)
                    # NOTE: rename using pathlib
                    (replica_path / key).rename(replica_path / source_file_new_path)
                    continue

                # NOTE: filename and content not match -> removal
                logger.info("File % has been removed", key)
                os.remove(replica_path / key)
                continue
            for key, value in source_mapping.items():
                if key not in replica_mapping.keys():
                    if value not in replica_mapping.values():
                        # NOTE: path and content not match -> creation
                        logger.info("Created new file at %", key)
                        shutil.copy2(source_path / key, replica_path / key)
                        continue

            time.sleep(arguments.sync_interval * 60)
    except KeyboardInterrupt:
        logger.info("Exiting sync process...")


if __name__ == "__main__":

    def argstr2bool(v):
        if isinstance(v, bool):
            return v
        if v.lower() in ("yes", "true", "t", "y", "1"):
            return True
        elif v.lower() in ("no", "false", "f", "n", "0"):
            return False
        else:
            raise argparse.ArgumentTypeError("Boolean value expected.")

    parser = argparse.ArgumentParser(
        description="Keep a synced copy of the source path at the replica \
        path and log all changes ocurring to the contenct of source",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--source_path",
        type=str,
        help="Path to keep sync of",
        required=True,
    )
    parser.add_argument(
        "--replica_path",
        type=str,
        help="Path to store the synched copy of source",
        required=True,
    )
    parser.add_argument(
        "--sync_interval",
        type=float,
        default=0.5,
        help="interval of minutes between syncs",
    )
    parser.add_argument(
        "--log_path",
        type=str,
        default=pathlib.Path(__file__).parent.absolute() / "file_sync.log",
        help="path to be used for storing of log-file",
    )

    args = parser.parse_args()

    logging.basicConfig(
        format="%(asctime)s %(message)s",
        filename=args.log_path,
        encoding="utf-8",
        level=logging.DEBUG,
    )
    logger = logging.getLogger("File Sync")

    logger.info(f"{args=}")
    main(args)
