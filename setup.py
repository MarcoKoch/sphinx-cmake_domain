# This file is part of the sphinx-cmake_domain Sphinx extension.
# See <https://github.com/marcokoch/sphinx-cmake_comain> for recent information.
#
# # Copyright 2020 Marco Koch
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
# 
# 3. Neither the name of the copyright holder nor the names of its contributors
# may be used to endorse or promote products derived from this software without
# specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import setuptools


setuptools.setup(
    name = "sphinx-cmake_domain",
    version = "0.1.0.dev1",
    author = "Marco Koch",
    author_email = "marco-koch@t-online.de",
    description = "A Sphinx extension that adds a CMake domain",
    url = "https://github.com/marcokoch/sphinx-cmake_domain",
    project_urls = {
        "Source": "https://github.com/marcokoch/sphinx-cmake_domain",
        "Tracker": "https://github.com/marcokoch/sphinx-cmake_domain/issues"
    }
    classifiers = [
        "Development Status :: 3 - Alpha",
        "Framework :: Sphinx :: Extension",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Topic :: Documentation :: Sphinx",
        "Topic :: Education",
        "Topic :: Software Development :: Documentation"
    ],
    keywords = "sphinx extension documentation cmake domain",
    install_requires = ["Sphinx>=3.1.2"],
    python_requires = ">=3.8, <4",
    packages = setuptools.find_packages()
)
