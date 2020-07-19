#! /usr/bin/env python

from distutils.command.build import build
from setuptools import setup


# Override the build command to automatically compile message catalogs
class BuildCmd(build):
    def run(self):
        from babel.messages.frontend import compile_catalog
        
        compiler = compile_catalog(self.distribution)
        options = self.distribution.get_option_dict("compile_catalog")
        compiler.domain = [options["domain"][1]]
        compiler.directory = options['directory'][1]
        compiler.run()
        
        super().run()


if __name__ == "__main__":
    setup(cmdclass = {"build": BuildCmd})
