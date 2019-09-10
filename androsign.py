#!/usr/bin/env python

# This file is part of Androguard.
#
# Copyright (C) 2012, Anthony Desnos <desnos at t0t0.fr>
# All rights reserved.
#
# Androguard is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Androguard is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Androguard.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys
import traceback

import click
from androguard.core import androconf
from androguard.misc import AnalyzeAPK, AnalyzeDex

from elsim import ELSIM_VERSION
from elsim.elsign import dalvik_elsign


@click.command()
@click.version_option(ELSIM_VERSION)
@click.option('-b', '--database', required=True, help='use this database')
@click.option('-c', '--config', required=True, help='use this configuration')
@click.option('-v', '--verbose', is_flag=True, help='display debug information')
@click.argument('comp')
def cli(comp, database, config, verbose):
    s = dalvik_elsign.MSignature(database, config, verbose)

    def display(ret):
        click.echo("----> {}".format(ret[0]))

    def check_file(filename):
        ret_type = androconf.is_android(filename)

        click.echo("{}:".format(os.path.basename(filename)), nl=False)
        if ret_type == "APK":
            try:
                a, _, dx = AnalyzeAPK(filename)
                if a.is_valid_APK():
                    display(s.check(dx))
                else:
                    click.echo("INVALID APK", err=True)
            except Exception as e:
                click.echo("ERROR: {}".format(e), err=True)
                print("-"*60)
                traceback.print_exc(file=sys.stdout)
                print("-"*60)

        elif ret_type == "DEX":
            _, _, dx = AnalyzeDex(filename)
            display(s.check(dx))
        else:
            click.echo("Unknown filetype!", err=True)

    if os.path.isfile(comp):
        check_file(comp)
    else:
        for root, _, files in os.walk(comp, followlinks=True):
            for f in files:
                check_file(os.path.join(root, f))


if __name__ == "__main__":
    cli()
