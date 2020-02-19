#!/usr/bin/env python3.8
import functools
import os
import pathlib
import shlex
import subprocess
import sys

if __name__ == "__main__":
    common_args = ["-m", "piptools", "compile", "--generate-hashes"] + sys.argv[1:]
    run = functools.partial(
        subprocess.run,
        check=True,
        cwd=pathlib.Path(__file__).parent,
        env={**os.environ, "CUSTOM_COMPILE_COMMAND": shlex.join(sys.argv)},
    )
    run(["python3.5", *common_args, "-o", "py35.txt"])
    run(["python3.6", *common_args, "-o", "py36.txt"])
    run(["python3.7", *common_args, "-o", "py37.txt"])
    run(["python3.8", *common_args, "-o", "py38.txt"])
