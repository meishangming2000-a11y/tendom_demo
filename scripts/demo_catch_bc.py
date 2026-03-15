#!/usr/bin/env python3
"""One-command viewer demo for the current catch-and-hold BC baseline."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scripts import demo_bc


def main():
    argv = ["--enable-catch-task", *sys.argv[1:]]
    return demo_bc.main(argv)


if __name__ == "__main__":
    sys.exit(main())
