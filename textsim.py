# This file is part of Elsim.
#
# Copyright (C) 2012, Anthony Desnos <desnos at t0t0.fr>
# All rights reserved.
#
# Elsim is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Elsim is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Elsim.  If not, see <http://www.gnu.org/licenses/>.
import click
from elsim.text import ProxyText, FILTERS_TEXT
from elsim import Elsim, ELSIM_VERSION
from elsim.similarity import Compress


@click.command()
@click.version_option(ELSIM_VERSION)
@click.option("-d", "--display", is_flag=True, help="display detailed information about the changes")
@click.option("-c", "--compressor", default="SNAPPY", type=click.Choice([x.name for x in Compress]),
        show_default=True,
        show_choices=True,
        help="Set the compression method")
@click.option("-t", "--threshold", type=click.FloatRange(0, 1), help="Threshold for similarity measure, defines when two items are similar, overwrites the default")
@click.argument('comp', nargs=2)
def cli(display, compressor, threshold, comp):
    """
    Run a similarity measure on two text files
    """
    with open(comp[0], 'rb') as fp:
        b1 = fp.read()
    with open(comp[1], 'rb') as fp:
        b2 = fp.read()

    el = Elsim(ProxyText(b1), ProxyText(b2), FILTERS_TEXT, threshold=threshold, compressor=compressor)
    el.show()

    if display:
        print("SIMILAR sentences:")
        diff_methods = el.get_similar_elements()
        for i in diff_methods:
            el.show_element(i)

        print("IDENTICAL sentences:")
        new_methods = el.get_identical_elements()
        for i in new_methods:
            el.show_element(i)

        print("NEW sentences:")
        new_methods = el.get_new_elements()
        for i in new_methods:
            el.show_element(i, False)

        print("DELETED sentences:")
        del_methods = el.get_deleted_elements()
        for i in del_methods:
            el.show_element(i)

        print("SKIPPED sentences:")
        skip_methods = el.get_skipped_elements()
        for i in skip_methods:
            el.show_element(i)


if __name__ == "__main__":
    cli()
