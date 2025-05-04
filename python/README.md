# README

- `nwgeom_out2xyz.py` this script extracts geometries from NWChem output
  files and stores them in the extended XYZ format.<BR>
  Currently, each geometry
  can be stored in a separate file with the `--separate` flag,<BR>
  all geometries from a particular output can be stored as a sequence of
  XYZ structures in a single file with `--together` flag,<BR>
  or all the geometries
  from multiple outputs can be stored in a single file with the `--alltogether`  flag. With the `--alltogether` flag the `--prefix` flag is important to
  specify the basename of the resulting file.<BR>
  Run `nwgeom_out2xyz.py --help` for more information.
