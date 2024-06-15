#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to generate the required CMakeLists.txt and swig interface file for a project.
"""


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument("project", help="Project name")
    parser.add_argument(
        "-v", "--version", help="Project version. Default is 0.1", default="0.1"
    )
    parser.add_argument(
        "-n",
        "--use-numpy",
        help="If given, include numpy interface file",
        action="store_true",
    )
    parser.add_argument('-I', '--include', help='Additional include paths', action='append')

    args = parser.parse_args()

    print(args)