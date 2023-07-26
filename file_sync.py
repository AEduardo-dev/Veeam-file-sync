import shutil
import pathlib
import argparse
import logging
import pathlib
from typing import Any, Dict
import time
import hashing
import os

replica_mapping: Dict[pathlib.Path, Any] = {}
source_mapping: Dict[pathlib.Path, Any] = {}


def update_replica_mapping(replica_path: str):
    files_list = [
        file
        for file in pathlib.Path(replica_path).rglob("*")
        if pathlib.Path.is_file(file)
    ]
    replica_mapping.clear()
    for file in files_list:
        replica_mapping[file.relative_to(replica_path)] = hashing.hash_file(
            file.__str__()
        ).hexdigest()


def generate_source_mapping(source_path: str):
    files_list = [
        file
        for file in pathlib.Path(source_path).rglob("*")
        if pathlib.Path.is_file(file)
    ]
    source_mapping.clear()
    for file in files_list:
        source_mapping[file.relative_to(source_path)] = hashing.hash_file(
            file.__str__()
        ).hexdigest()


def main(args):
    logger.info(f"{args=}")

    source_path: pathlib.Path = pathlib.Path(args.source_path)
    replica_path: pathlib.Path = pathlib.Path(args.replica_path)

    if not pathlib.Path.exists(source_path):
        logger.fatal(
            f"Source path {source_path} is not present. No synchronization will be executed"
        )
        exit(1)

    try:
        shutil.rmtree(replica_path, ignore_errors=True)
    except FileNotFoundError:
        pass

    shutil.copytree(src=source_path, dst=replica_path)

    try:
        while True:
            if not pathlib.Path.exists(pathlib.Path(source_path)):
                logger.fatal(
                    f"Source path {source_path} is not present. No synchronization will be executed"
                )
                exit(1)
            else:
                generate_source_mapping(source_path)
                update_replica_mapping(replica_path)

                key: pathlib.Path
                value: Any
                for key, value in replica_mapping.items():
                    if key in source_mapping.keys():
                        if value in source_mapping.values():
                            # NOTE: filename match, content match -> ignore
                            continue
                        else:
                            # NOTE: filename match, content not match -> modification
                            logger.info(f"File {key} content has been modified.")
                            shutil.copy2(source_path / key, replica_path / key)
                            continue
                    else:
                        if value in source_mapping.values():
                            # NOTE: filename not match, content match -> rename/move
                            source_file_new_path: pathlib.Path = list(
                                source_mapping.keys()
                            )[list(source_mapping.values()).index(value)]
                            logger.info(
                                f"File {key} has been moved to {list(source_mapping.keys())[list(source_mapping.values()).index(value)]}"
                            )
                            # NOTE: rename using pathlib
                            (replica_path / key).rename(
                                replica_path / source_file_new_path
                            )
                            continue
                        else:
                            # NOTE: filename not match, content not match -> removal or double change (cannot tell depending on timing)
                            logger.info(f"File {key} has been removed")
                            os.remove(replica_path / key)
                            continue
                for key, value in source_mapping.items():
                    if key not in replica_mapping.keys():
                        if value not in replica_mapping.values():
                            # NOTE: origin path not in replica and origin content not in replica -> creation
                            logger.info(f"Created new file at {key}")
                            shutil.copy2(source_path / key, replica_path / key)
                            continue

            time.sleep(args.sync_interval * 60)
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
        description="Keep a synced copy of the source path at the replica path and log all changes ocurring to the contenct of source",
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
    print(f"{args=}")
    main(args)
