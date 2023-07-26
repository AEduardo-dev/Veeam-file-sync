import hashlib
from typing import Any
import logging

LOGGER = logging.getLogger(__name__)


def hash_file(file_path: str, buf_size: int = 65536) -> Any:
    # BUF_SIZE is totally arbitrary, change for your app!
    if buf_size <= 0:
        LOGGER.fatal(
            f"Impossible to parse file with buffer size smaller than 1 bit. Please check your settings and try again."
        )

    md5 = hashlib.md5()

    try:
        with open(file_path, "rb") as f:
            while True:
                data = f.read(buf_size)
                if not data:
                    break
                md5.update(data)
    except FileNotFoundError as e:
        LOGGER.warn(e.strerror)
        return 0

    # print("MD5: {0}".format(md5.hexdigest()))
    return md5
