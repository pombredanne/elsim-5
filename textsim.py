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
@click.option("-d", "--details", is_flag=True, help="display detailed information about the changes")
@click.option("-c", "--compressor", default="SNAPPY", type=click.Choice([x.name for x in Compress]),
        show_default=True,
        show_choices=True,
        help="Set the compression method")
@click.option("-t", "--threshold", default=0.6, type=click.FloatRange(0, 1), help="Threshold when sorting interesting items")
@click.argument('comp', nargs=2)
def cli(details, compressor, threshold, comp):
    """
    Run a similarity measure on two text files
    """
    with open(comp[0], 'rb') as fp:
        b1 = fp.read()
    with open(comp[1], 'rb') as fp:
        b2 = fp.read()

    el = Elsim(ProxyText(b1), ProxyText(b2), FILTERS_TEXT, threshold=threshold, compressor=compressor)
    el.show(details=details)


if __name__ == "__main__":
    cli()
