#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to generate the required CMakeLists.txt and swig interface file for a project.
"""

from pathlib import Path
import urllib.request
import os


class CMakeGenerator:
    """
    Class to create CMakeLists.txt files, and optionally SWIG interface file.

    Parameters
    ----------
    project_name : str
        Project name
    project_version : str
        Project version
    generate_interface_file : bool
        If True, also create [project_name].i file. Default is True.
    top_level_dir : Path
        Top level dir to write files to. Default is current directory.
    src_dir : Path
        Path to source files. If it does not exist, it will be created. Default is "./src".
    use_numpy : bool
        If True, download numpy.i file and automatically add numpy include dir.
        Default is False.
    include : {list[str|Path], str, Path}, optional
        Additional include path(s)
    cxx_std : str
        C++ standard. Default is "17".
    cmake_version : str
        Minimum cmake version. Default is "3.18".
    """

    def __init__(
        self,
        project_name,
        project_version,
        generate_interface_file=True,
        top_level_dir=".",
        src_dir="src",
        use_numpy=False,
        include=None,
        cxx_std="17",
        cxx_flags=None,
        cmake_version="3.18",
    ):
        self._project_name = project_name
        self._project_version = project_version

        self._generate_interface_file = generate_interface_file

        self._top_level_dir = Path(top_level_dir)
        if not self._top_level_dir.exists():
            self._top_level_dir.mkdir(parents=True)

        self._src_dir = self._top_level_dir.joinpath(Path(src_dir))
        if not self._src_dir.exists():
            self._src_dir.mkdir(parents=True)

        self._swig_dir = self._src_dir.joinpath("swig")
        if not self._swig_dir.exists():
            self._swig_dir.mkdir(parents=True, exist_ok=True)

        self._use_numpy = use_numpy

        if include is None:
            include = []
        elif isinstance(include, str):
            include = [include]
        elif isinstance(include, Path):
            include = [str(include)]
        if not isinstance(include, list):
            msg = f"`include` must be path or list of paths, not '{include}'"
            raise TypeError(msg)
        self._include = include

        self._cxx_std = cxx_std
        self._cxx_flags = "" if cxx_flags is None else cxx_flags
        self._min_cmake_version = cmake_version

    def generate(self):
        """
        Generate CMakeLists.txt files and SWIG interface files, if requested.
        """
        
        self._generate_top_level_cmakelists()
        self._generate_src_cmakelists()
        self._generate_swig_cmakelists()

        if self._generate_interface_file:
            self._generate_interface()

        if self._use_numpy:
            self._generate_numpy()

    def _generate_interface(self):
        """
        Write default [top_level_dir]/[src_dir]/swig/[project_name].i file.
        """

        path_to_header = self._src_dir.joinpath(f"{self._project_name}.h")

        text = [f"%module {self._project_name}", ""]
        if self._use_numpy:
            numpy_text = [
                "%{",
                "#define SWIG_FILE_WITH_INIT",
                f'#include "{self._project_name}.h"',
                "%}",
                '%include "numpy.i"',
                "%init %{",
                "import_array();",
                "%}",
                ""
            ]

            text += numpy_text
        text.append(f'%include "{path_to_header}.h"')

        text = os.linesep.join(text)

        out_file = self._swig_dir.joinpath(f"{self._project_name}.i")

        with open(out_file, "w") as fileobj:
            fileobj.write(text)

    def _generate_numpy(self):
        """
        Add numpy include path to include list, if required, and download numpy.i.

        Raises
        ------
        RuntimeError
            If the numpy include path could not de determined.
        """
        if not self._numpy_in_include(self._include):
            try:
                numpy_include = self._get_numpy_include()
            except Exception as err:
                msg = f"Could not find numpy include path: {err}. "
                msg += "Please provide path to numpy include dir with '--include' flag."
                raise RuntimeError(msg)
            else:
                self._include.append(numpy_include)
                print(f"Found numpy include path '{numpy_include}'")

        text = self._get_numpy_i()

        out_file = self._swig_dir.joinpath("numpy.i")
        with open(out_file, "w") as fileobj:
            fileobj.write(text)

    def _generate_top_level_cmakelists(self):
        source_subdir = self._src_dir.relative_to(self._top_level_dir)
        text = [
            f"cmake_minimum_required(VERSION {self._min_cmake_version})",
            f"project({self._project_name})",
            "",
            f"set(CMAKE_CXX_STANDARD {self._cxx_std})",
            f'set(CMAKE_CXX_FLAGS "${{CMAKE_CXX_FLAGS}}{self._cxx_flags}")',
            "set(CMAKE_POSITION_INDEPENDENT_CODE ON)",
            ""
            f"add_subdirectory({source_subdir})",
        ]

        text = os.linesep.join(text)

        out_file = self._top_level_dir.joinpath("CMakeLists.txt")

        with open(out_file, "w") as fileobj:
            fileobj.write(text)

    def _generate_src_cmakelists(self):
        pass

    def _generate_swig_cmakelists(self):
        pass

    @staticmethod
    def _numpy_in_include(include) -> bool:
        for p in include:
            if "numpy" in p:
                return True
        return False

    @staticmethod
    def _get_numpy_i(out_dir: Path) -> str:
        url = "https://raw.githubusercontent.com/numpy/numpy/main/tools/swig/numpy.i"
        r = urllib.request.urlopen(url)
        text = r.read().decode("utf-8")
        return text

    @staticmethod
    def _get_numpy_include() -> Path:
        try:
            import numpy as np
        except ImportError:
            raise Exception("NumPy is not installed")

        path = Path(np.__file__).parent
        include_path = path.joinpath("core", "include")

        if not include_path.exists():
            raise Exception(f"'{include_path}' does not exist")

        # additionally, check that numpy/arrayobject.h exists
        arrayobject_path = include_path.joinpath("numpy", "arrayobject.h")
        if not arrayobject_path.exists():
            raise Exception(f"'{arrayobject_path}' not found")

        return include_path


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument("project", help="Project name")
    parser.add_argument(
        "-v", "--version", help="Project version. Default is 0.1", default="0.1"
    )
    parser.add_argument(
        "--dont-generate-interface",
        help="If given, don't generate [project].i file",
        action="store_true",
    )
    parser.add_argument(
        "-n",
        "--use-numpy",
        help="If given, setup project to use numpy interface file and include path",
        action="store_true",
    )
    parser.add_argument(
        "-d",
        "--top-level-dir",
        help="Top level directory to write to. Default is current directory",
        default=".",
    )
    parser.add_argument(
        "-s",
        "--src",
        help=(
            "Name of directory of source files, to be appended to [top_level_dir]. "
            "If it does not exist, it will be created. "
            "Default is src"
        ),
        default="src",
    )
    parser.add_argument(
        "-I", "--include", help="Additional include path", action="append"
    )
    parser.add_argument(
        "--cxx", help="C++ standard to use. Default is 17", default="17"
    )
    parser.add_argument("--cxx_flags", help="Additional C++ compiler flags")
    parser.add_argument(
        "--cmake-version", help="Minimum cmake version. Default is 3.18", default="3.18"
    )

    args = parser.parse_args()

    print(args)

    generate_interface_file = not args.dont_generate_interface

    cmake_gen = CMakeGenerator(
        args.project,
        args.version,
        generate_interface_file=generate_interface_file,
        src_dir=args.src,
        use_numpy=args.use_numpy,
        include=args.include,
        cxx_std=args.cxx,
        cxx_flags=args.cxx_flags,
        cmake_version=args.cmake_version,
    )

    cmake_gen.generate()
