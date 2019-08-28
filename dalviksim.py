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

from elsim import ELSIM_VERSION
from elsim.similarity import Compress
from elsim.dalvik import ProxyDalvikString, FILTERS_DALVIK_SIM_STRING
from elsim.dalvik import ProxyDalvik, FILTERS_DALVIK_SIM
import elsim
import sys
import os
import click

from androguard.core import androconf
from androguard.misc import AnalyzeAPK, AnalyzeDex


def check_one_file(dx1, dx2, FS, threshold, compressor, details, view_strings, new, removed):
    """
    Show similarities between two dalvik containers

    :param androguard.core.analysis.analysis.Analysis dx1: first file
    :param androguard.core.analysis.analysis.Analysis dx2: second file
    :param dict FS: the filter basis
    :param str compressor: compressor name
    :param bool details: should extra information be shown
    :param bool view_strings: also calculate the similarities based on strings
    :param bool new: should the similarity score include new elements
    :param bool removed: should the similarity score include deleted elements
    """
    el = elsim.Elsim(ProxyDalvik(dx1), ProxyDalvik(dx2), FS, threshold, compressor)
    print("Calculating similarity based on methods")
    el.show(new, removed, details)

    if view_strings:
        els = elsim.Elsim(ProxyDalvikString(dx1), ProxyDalvikString(dx2), FILTERS_DALVIK_SIM_STRING, threshold, compressor)
        print("Calculating similarity based on strings")
        els.show(new, removed, details)


def load_analysis(filename):
    """Return an AnalysisObject depding on the filetype"""
    ret_type = androconf.is_android(filename)
    if ret_type == "APK":
        _, _, dx = AnalyzeAPK(filename)
        return dx
    elif ret_type == "DEX":
        _, _, dx = AnalyzeDex(filename)
        return dx
    return None


@click.command()
@click.version_option(ELSIM_VERSION)
@click.option("-d", "--details", is_flag=True, help="display detailed information about the changes")
@click.option("-c", "--compressor", default="SNAPPY", type=click.Choice([x.name for x in Compress]),
        show_default=True,
        show_choices=True,
        help="Set the compression method")
@click.option("-t", "--threshold", default=0.6, type=click.FloatRange(0, 1), help="Threshold when sorting interesting items")
@click.option("-s", "--size", type=int, help='exclude specific method below the specific size (specify the minimum size of a method to be used (it is the length (bytes) of the dalvik method)')
@click.option("-e", "--exclude", type=str, help="exlude class names (python regex string)")
@click.option("--new/--no-new", help="calculate similarity score by including new elements", show_default=True)
@click.option("--removed/--no-removed", help="calculate similarity score by using removed elementes", show_default=True)
@click.option("-x", "--xstrings", is_flag=True, help="display similarites of strings")
@click.argument('comp', nargs=2)
def cli(details, compressor, threshold, size, exclude, new, removed, xstrings, comp):
    """
    Compare a Dalvik based file against another file or a whole directory.

    The first argument must be an APK or a single DEX file.
    The second argument might be another APK or DEX or a folder containing
    APK or DEX files.
    In the latter case, the first file is compared against all files in the folder
    recursively.
    """
    dx1 = load_analysis(comp[0])
    if dx1 is None:
        raise click.BadParameter("The supplied file '{}' is not an APK or a DEX file!".format(comp[0]))

    FS = FILTERS_DALVIK_SIM
    if exclude:
        FS[elsim.FILTER_SKIPPED_METH].set_regexp(exclude)
    if size:
        FS[elsim.FILTER_SKIPPED_METH].set_size(size)

    if os.path.isdir(comp[1]):
        for root, _, files in os.walk(comp[1], followlinks=True):
            for f in files:
                real_filename = os.path.join(root, f)
                print("filename: %s ..." % real_filename)
                dx2 = load_analysis(real_filename)
                if dx2 is None:
                    click.echo(click.style("The file '{}' is not an APK or DEX. Skipping.".format(real_filename), fg='red'), err=True)
                check_one_file(dx1, dx2, FS, threshold, compressor, details, xstrings, new, removed)
    else:
        dx2 = load_analysis(comp[1])
        if dx2 is None:
            raise click.BadParameter("The supplied file '{}' is not an APK or a DEX file!".format(comp[1]))
        check_one_file(dx1, dx2, FS, threshold, compressor, details, xstrings, new, removed)


if __name__ == "__main__":
    cli()

