import os
import sys
import subprocess
import warnings
from pathlib import Path

try:
    from setuptools.command.build_ext import build_ext
except ImportError:
    from distutils.command.build_ext import build_ext


class CMakeBuild(build_ext):
    user_options = build_ext.user_options + [
        ("suitesparse-root=", None, "suitesparse source location"),
        ("sundials-root=", None, "sundials source location"),
    ]

    def initialize_options(self):
        build_ext.initialize_options(self)
        self.suitesparse_root = None
        self.sundials_root = None

    def finalize_options(self):
        build_ext.finalize_options(self)
        # Determine the calling command to get the
        # undefined options from.
        # If build_ext was called directly then this
        # doesn't matter.
        try:
            self.get_finalized_command("install", create=0)
            calling_cmd = "install"
        except AttributeError:
            calling_cmd = "bdist_wheel"
        self.set_undefined_options(
            calling_cmd,
            ("suitesparse_root", "suitesparse_root"),
            ("sundials_root", "sundials_root"),
        )
        if not self.suitesparse_root:
            self.suitesparse_root = "KLU_module_deps/SuiteSparse-5.6.0"
        if not self.sundials_root:
            self.sundials_root = "KLU_module_deps/sundials5"

    def run(self):
        try:
            subprocess.run(["cmake", "--version"])
        except OSError:
            raise RuntimeError(
                "CMake must be installed to build the KLU python module."
            )

        try:
            assert os.path.isfile("third-party/pybind11/tools/pybind11Tools.cmake")
        except AssertionError:
            print(
                "Error: Could not find "
                "third-party/pybind11/pybind11/tools/pybind11Tools.cmake"
            )
            print("Make sure the pybind11 repository was cloned in ./third-party/")
            print("See installation instructions for more information.")

        cmake_args = ["-DPYTHON_EXECUTABLE={}".format(sys.executable)]
        if self.suitesparse_root:
            print(self.suitesparse_root)
            cmake_args.append(
                "-DSuiteSparse_ROOT={}".format(os.path.abspath(self.suitesparse_root))
            )
        if self.sundials_root:
            print(self.sundials_root)
            cmake_args.append(
                "-DSUNDIALS_ROOT={}".format(os.path.abspath(self.sundials_root))
            )

        if not os.path.exists(self.build_temp):
            os.makedirs(self.build_temp)

        # The CMakeError.log file is generated by cmake is the configure step
        # encounters error. In the following the existence of this file is used
        # to determine whether or not the cmake configure step went smoothly.
        # So must make sure this file does not remain from a previous failed build.
        if os.path.isfile(os.path.join(self.build_temp, "CMakeError.log")):
            os.remove(os.path.join(self.build_temp, "CMakeError.log"))

        cmake_list_dir = os.path.abspath(os.path.dirname(__file__))
        print("-" * 10, "Running CMake for idaklu solver", "-" * 40)
        subprocess.run(["cmake", cmake_list_dir] + cmake_args, cwd=self.build_temp)

        if os.path.isfile(os.path.join(self.build_temp, "CMakeError.log")):
            msg = (
                "cmake configuration steps encountered errors, and the idaklu module"
                " will not be built.\nIgnore this warning if you don't plan to use the "
                "idaklu module.\nIf you plan to use the idaklu module, make sure the "
                "dependencies are correctly installed.\nSee "
                "https://github.com/pybamm-team/PyBaMM/blob/develop/"
                "INSTALL-LINUX-MAC.md"
            )
            warnings.warn(msg)
        else:
            print("-" * 10, "Building idaklu module", "-" * 40)
            subprocess.run(["cmake", "--build", "."], cwd=self.build_temp)

            # Move from build temp to final position
            for ext in self.extensions:
                self.move_output(ext)

    def move_output(self, ext):
        # Copy built module to dist/ directory
        build_temp = Path(self.build_temp).resolve()
        source_path = build_temp / self.get_ext_filename(ext.name)
        # Get destination location
        # self.get_ext_fullpath(ext.name) -->
        # build/lib.linux-x86_64-3.5/idaklu.cpython-37m-x86_64-linux-gnu.so
        # using resolve() with python < 3.6 will result in a FileNotFoundError
        # since the location does not yet exists.
        dest_path = Path(self.get_ext_fullpath(ext.name)).resolve()
        source_path = build_temp / self.get_ext_filename(ext.name)
        dest_directory = dest_path.parents[0]
        dest_directory.mkdir(parents=True, exist_ok=True)
        self.copy_file(source_path, dest_path)
