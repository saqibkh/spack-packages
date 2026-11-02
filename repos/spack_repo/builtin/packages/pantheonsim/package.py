# Copyright Spack Project Developers. See COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

import os

from spack_repo.builtin.build_systems.cmake import CMakePackage

from spack.package import *


class Pantheonsim(CMakePackage):
    """PantheonSim is a CPU-side simulator of NVIDIA and AMD GPUs. It runs CUDA
    and HIP programs built with the real nvcc or hipcc on a machine without a
    GPU, by presenting a simulated card (a T4, an H100, an MI300X) to them. It
    checks what a program does, not how fast it runs: there is no timing model."""

    homepage = "https://pantheonsim.com"
    git = "https://github.com/pantheongpu/pantheonsim.git"

    maintainers("saqibkh")

    license("Apache-2.0", checked_by="saqibkh")

    version("main", branch="main")
    version("0.2.0", tag="v0.2.0", commit="840bbf6c281b973d62ea300d27c9c3fd6e929941")

    # The simulator's CUDA libraries are built against the headers of the
    # toolkit found on PATH, and carry its soname (libcudart.so.12 or .13). A
    # program only loads them when it asks for that same soname, so build with
    # the toolkit the programs will be compiled with.
    variant("cuda", default=True, description="Build the simulated CUDA libraries against CUDA")

    depends_on("c", type="build")
    depends_on("cxx", type="build")
    depends_on("cmake@3.20:", type="build")
    depends_on("cuda@12:", type="build", when="+cuda")
    depends_on("bash", type="build")

    # The simulator is written in C++20.
    conflicts("%gcc@:10", msg="PantheonSim needs a C++20 compiler (GCC 11 or newer)")
    conflicts("platform=darwin", msg="PantheonSim runs on Linux")
    conflicts("platform=windows", msg="PantheonSim runs on Linux")

    def install(self, spec, prefix):
        # The project has no install rules. It ships the build tree's layout
        # (vgpu, bin/, shim/ and the libraries the shim's links lead to) with a
        # script that copies it out, and vgpu finds its shim beside itself.
        script = join_path(self.stage.source_path, "scripts", "package-build.sh")
        bash = which("bash", required=True)
        bash(script, self.build_directory, prefix)
        # vgpu sits at the top of the prefix; give it a place on PATH too.
        if not os.path.exists(join_path(prefix.bin, "vgpu")):
            symlink(join_path("..", "vgpu"), join_path(prefix.bin, "vgpu"))

    def setup_run_environment(self, env: EnvironmentModifications) -> None:
        env.set("VGPU_SHIM_DIR", self.prefix.shim)

    def test_list_gpus(self):
        """vgpu lists the simulated GPUs"""
        vgpu = which(self.prefix.vgpu, required=True)
        out = vgpu("list-gpus", output=str.split, error=str.split)
        assert "nvidia/" in out
