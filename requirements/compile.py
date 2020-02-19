#!/usr/bin/env python
import os
import subprocess
import sys
import functools
from pathlib import Path


if __name__ == "__main__":
    common_args = ["-m", "piptools", "compile", "--generate-hashes"] + sys.argv[1:]
    run = functools.partial(
        subprocess.run,
        check=True,
        cwd=Path(__file__).parent,
        env={**os.environ, "CUSTOM_COMPILE_COMMAND": "requirements/compile.py"},
    )
    run(["python3.5", *common_args, "-o", "py35.txt"])
    run(["python3.6", *common_args, "-o", "py36.txt"])
    run(["python3.7", *common_args, "-o", "py37.txt"])
    run(["python3.8", *common_args, "-o", "py38.txt"])
