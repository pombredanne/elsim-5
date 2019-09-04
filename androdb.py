import os
import click
from androguard.core import androconf
from androguard.misc import AnalyzeAPK, AnalyzeDex

from elsim import ELSIM_VERSION
from elsim import db


def load_analysis(filename):
    """Return an AnalysisObject depding on the filetype"""
    ret_type = androconf.is_android(filename)
    if ret_type == "APK":
        _, _, dx = AnalyzeAPK(filename)
        return dx
    if ret_type == "DEX":
        _, _, dx = AnalyzeDex(filename)
        return dx
    return None


def process_single_file(database, filename):
    dx = load_analysis(filename)
    if not dx:
        print(filename, "ERROR")

    print(filename, database.percentages(dx))


@click.group()
@click.version_option(ELSIM_VERSION)
@click.option("-d", "--database", type=str, required=True, help="Use this database file")
@click.pass_context
def cli(ctx, database):
    ctx.obj = database


@cli.command()
@click.option("-n", "--name", type=str, required=True, help="use this name")
@click.option("-s", "--subname", type=str, required=True, help="Use this subname")
@click.argument("filename")
@click.pass_obj
def add(database, name, subname, filename):
    """
    Import the given file into the database

    Name and Subname are used to sort the given file into the database.
    The database is a tree-like structure and contains:
    name -> subname -> classname -> methods as simhash
    """
    dx = load_analysis(filename)
    if not dx:
        raise click.BadParameter("Not a valid APK or DEX file!")

    with db.ElsimDB(database) as edi:
        edi.add(dx, name, subname)


@cli.command()
@click.argument("filename", nargs=-1)
@click.pass_obj
def isin(database, filename):
    db_file = db.ElsimDB(database)

    for f in filename:
        if os.path.isfile(f):
            process_single_file(db_file, f)
        elif os.path.isdir(f):
            for root, _, files in os.walk(f):
                for fname in files:
                    process_single_file(db_file, os.path.join(root, fname))


@cli.command()
@click.pass_obj
def show(database):
    """
    Shows the content of the database
    """
    db.DBFormat(database).show()


if __name__ == "__main__":
    cli()
