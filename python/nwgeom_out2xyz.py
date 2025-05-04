#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vi:ts=4:et

# Extract geometry information from an NWChem output file, convert it to
# XYZ format, and manage storing it.

from argparse import ArgumentParser
import sys
from typing import *
from typing import TextIO

def parse_args():
    """Parse the command line arguments"""
    parser = ArgumentParser(description="""
       Extract geometries from an NWChem output file. The geometries are
       written out in a selection of a number of different ways. The
       geometries are written in the XYZ format.""")
    parser.add_argument("nwofilenames",action="extend",nargs="+",type=str,
                        help="NWChem output file(s)")
    parser.add_argument("--prefix",type=str,default="",
                        help="prefix for output filenames")
    parser.add_argument("--separate",action="store_true",default=False,
                        help="write separate XYZ file for each geometry")
    parser.add_argument("--together",action="store_true",default=True,
                        help="write one XYZ file per NWChem output file")
    parser.add_argument("--alltogether",action="store_true",default=False,
                        help="write one XYZ file for all NWChem output files")
    args = parser.parse_args()
    return vars(args)

class Geometry:
    """A class to hold the NWChem geometry data

    The main data piece of information is a list of lines with one atom
    per line, e.g. "Li  1.0 2.0 3.0".

    Further meta-data can also be associated with the structure:
    - source:  the file the geometry was extracted from
    - count:   the instance number of the geometry from the source file
    - section: the part of the output file the geometry came from
    - lattice: the lattice specification if the geometry came from a periodic calculation
    """

    def __init__(self, source: str, count: int, units: str, fp: TextIO):
        """Read the geometry from the current file position"""
        self.section: str = None
        self.lattice: str = None
        self.coords: list[str] = []
        self.source = source
        self.count = count
        if units == "au":
            fac = 1.0/1.889725989
        elif units == "angstrom":
            fac = 1.0
        elif units == "nm":
            fac = 10
        else:
            print(f"Unknown units: {units}")
            sys.exit()
        for line in fp:
            tokens = line.split()
            ntokens = len(tokens)
            if ntokens == 0:
                # Reached an empty line this is the end of the geometry
                break
            elif ntokens == 6:
                xx = float(tokens[3])*fac
                yy = float(tokens[4])*fac
                zz = float(tokens[5])*fac
                atom = f"{tokens[1]} {xx} {yy} {zz}"
            else:
                print("Invalid number of tokens for coordinates")
                print(f"Line is: {line}")
                sys.exit()
            self.coords.append(atom)

    def set_section(self, section: str):
        """Set the output file section"""
        self.section = section

    def set_lattice(self, lattice: str):
        """Set the lattice specification"""
        self.lattice = lattice

    def get_source(self) -> str:
        """Retrieve the source filename"""
        return self.source

    def get_count(self) -> int:
        """Retrieve the structure count"""
        return self.count

    def write(self, fp: TextIO):
        """Write the structure to a file

        This function can write both the regular XYZ file format as
        well as the extented XYZ format. The extended XYZ format
        is triggered by the lattice attribute being set.

        The regular XYZ format is described, for example, on
        Wikipedia: https://en.wikipedia.org/wiki/XYZ_file_format.
        The extended XYZ format is described, for example, in the
        Ovito documentation: https://www.ovito.org/docs/current/reference/file_formats/input/xyz.html#extended-xyz-format.
        """
        natoms = len(self.coords)
        comment = ""
        if self.lattice:
            # Write extended XYZ format
            comment += f"Lattice={self.lattice} Properties=species:S:1:pos:R:3"
        fp.write(f"{natoms}\n")
        fp.write(f"{comment}\n")
        for atom in self.coords:
            fp.write(f"{atom}\n")

def run_extractor(files: list[str]) -> list[Geometry]:
    """Extract geometries from a list of outputfiles

    The extracted geometries are returned in a list.
    """
    geometries: list[Geometry] = []
    for file in files:
        with open(file) as fp:
            geometries = append_geometries(geometries,file,fp)
    return geometries

def skip_lines(fp: TextIO, num: int) -> None:
    """Skip a number of lines"""
    while num > 0:
        line = fp.readline()
        num -= 1

def append_geometries(geom_in: list[Geometry], filename: str, fp: TextIO) -> list[Geometry]:
    """Go through a single output file and extract all geometries"""
    count = 0
    for line in fp:
       # Check if we're at a geometry
       if line.strip().startswith("Output coordinates in angstroms"):
          #DEBUG
          print("angstroms")
          #DEBUG
          count += 1
          units = "angstrom"
          skip_lines(fp,3)
          geom_in.append(Geometry(filename,count,units,fp))
       elif line.strip().startswith("Output coordinates in a.u."):
          #DEBUG
          print("a.u.")
          #DEBUG
          count += 1
          units = "au"
          skip_lines(fp,3)
          geom_in.append(Geometry(filename,count,units,fp))
    return geom_in

def get_basename(filename: str) -> str:
    """Get the base name of a file

    The base name is defined as the name of a file without a path,
    and without an extension. E.g. the base name of "/share/structure.txt"
    is "structure".
    """
    path = filename.split("/")
    basename = path[-1].split(".")
    return basename[0]

def write_separate(prefix: str, geometries: list[Geometry]) -> None:
    """Write every geometry to a separate file

    The filename is constructed from the prefix, the NWChem output filename,
    and the geometry number.
    """
    for geometry in geometries:
        source = geometry.get_source()
        number = geometry.get_count()
        basename = get_basename(source)
        filename = f"{prefix}{basename}_{number:04d}.xyz"
        with open(filename,"w") as fp:
            geometry.write(fp)

def write_together(prefix: str, geometries: list[Geometry]) -> None:
    """Write all geometries that came from the same output file to a single file

    The filename is constructed from the prefix, and the NWChem output filename.
    """
    oldfilename = ""
    for geometry in geometries:
        source = geometry.get_source()
        number = geometry.get_count()
        basename = get_basename(source)
        filename = f"{prefix}{basename}.xyz"
        if oldfilename == filename:
            with open(filename,"a") as fp:
                geometry.write(fp)
        else:
            oldfilename = filename
            with open(filename,"w") as fp:
                geometry.write(fp)


def write_all_together(prefix: str, geometries: list[Geometry]) -> None:
    """Write all geometries a single file

    The filename is constructed from the prefix.
    """
    filename = f"{prefix}.xyz"
    with open(filename,"w") as fp:
        for geometry in geometries:
           geometry.write(fp)

if __name__ == "__main__":
    args = parse_args()
    #DEBUG
    print(args["nwofilenames"])
    print(args["prefix"])
    print(args["separate"])
    print(args["together"])
    print(args["alltogether"])
    #DEBUG
    geometries = run_extractor(args["nwofilenames"])
    prefix = args["prefix"]
    if args["separate"]:
        write_separate(prefix,geometries)
    if args["together"]:
        write_together(prefix,geometries)
    if args["alltogether"]:
        write_all_together(prefix,geometries)
