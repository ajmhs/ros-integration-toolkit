#
# (c) 2025 Copyright, Real-Time Innovations.  All rights reserved.
# No duplications, whole or partial, manual or electronic, may be made
# without express written permission.  Any such copies, or revisions thereof,
# must display this notice unaltered.
# This code contains trade secrets of Real-Time Innovations, Inc.
#
# This example module performs a headless scan of ROS2 messages/services/actions
# and exports to IDL files with the same directory structure. It can be run as
# a docker cmd. (See the Dockerfile in this directory.)
#
import os
import sys
import json
from pathlib import Path
from rosp import rosparser
from idlp import idltypex
from sqldb import sql3db

def collect_types_to_export(types_db):
    """Collect and return a list of type items to export.

    This takes the database handle and an iterable of datatype ids (as
    returned by `datatypes_reftree`) and returns a list of type_item
    entries (each is a list where index 0 is the type info tuple).
    """
    types_to_export = []
    all_data_types = types_db.datatypes_reftree()

    for type_id in all_data_types:
        # Get the full type record with members
        type_rec = types_db.get_record_tree_by_typename_or_idkey('', '', type_id)
        if not type_rec:
            continue
        # a list of lists is returned
        for type_item in reversed(type_rec):
            # Check if this type is already in the export array
            if not any(checkItem[0][0] == type_item[0][0] for checkItem in types_to_export):
                types_to_export.append(type_item)

    return types_to_export


def build_inherit_imports(types_db, inherits_field):
    """Return a list of IDL import lines for inherited type ids.

    `inherits_field` may be a JSON string or a Python list of ids.
    """
    imports = []
    if not inherits_field:
        return imports

    # normalize to a list of ids
    inherit_ids = []
    if isinstance(inherits_field, str):
        try:
            inherit_ids = json.loads(inherits_field)
        except Exception:
            inherit_ids = []
    elif isinstance(inherits_field, list):
        inherit_ids = inherits_field

    for iid in inherit_ids:
        try:
            type_rec = types_db.get_record_tree_by_typename_or_idkey('', '', iid)
            if not type_rec:
                continue
            ref_type_info = type_rec[0][0]
            ref_src = ref_type_info[2] if len(ref_type_info) > 2 else ''
            if not ref_src:
                filename = f"{ref_type_info[1]}.idl"
            else:
                ref_src = ref_src.strip('/')
                type_name = Path(ref_type_info[1]).stem
                filename = f"{os.path.join(ref_src, type_name)}.idl"
            imports.append(f'#import "{filename}"')
        except Exception:
            # ignore errors for missing referenced types
            continue

    return imports


def perform_headless_scan(*, output_dir, dds_ns_flag=True):
    """Perform a headless scan and export.

    Parameters:
    - output_dir (str): output directory where IDL files will be written (mandatory, keyword-only)
    - dds_ns_flag (bool): whether to include the `dds_` namespace in generated IDL (default: True)
    """

    ros_path = os.getenv('AMENT_PREFIX_PATH')
    db_filename = os.path.abspath('./headless.db')
    base_path = os.path.abspath(output_dir)

    rosparser.scan_paths_for_datatype_files([ros_path], ['.msg', '.srv', '.action'], [''], False, db_filename)
    types_db = sql3db.SQL3Util(db_filename)

    # Collect all types from the database
    types_to_export = collect_types_to_export(types_db)
		
    for type_item in types_to_export:
        try:
            # typeItem structure: [0] = type info tuple, [1:] = member info tuples
            type_info = type_item[0]  # (idkey, typeName, typePath, typeKind, inherits, memberList, tags, flags, notes, comments)
            type_src = type_info[2] if len(type_info) > 2 else ''
            
            # If no src path, use export path with type name
            if not type_src:
                output_dir = base_path
                filename = f"{type_info[1]}.idl"
            else:
                # Recreate directory structure from src path
                # Remove leading/trailing slashes and path separators
                type_src = type_src.strip('/')
                output_dir = os.path.join(base_path, type_src)
                # Remove file extension if present and add .idl
                type_name = Path(type_info[1]).stem
                filename = f"{type_name}.idl"
            
            # Create directory structure if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            export_filename = os.path.join(output_dir, filename)
            
            idlout = build_inherit_imports(types_db, type_info[4])

            # Export this single type
            idlout.extend(idltypex.export_idl_type([type_item], ddsNamespace=dds_ns_flag))

            f = open(export_filename, "w")
            for line in idlout:
                try:
                    f.write(line + '\n')
                except Exception:
                    pass
            f.close()
                
        except Exception as e:
            print(f"Failed to export type: {str(e)}")
    
    types_db.database_close()

# --------------------------------------------------
if __name__ == "__main__":
    # CLI usage: scan_headless.py <output_dir> [dds_ns_flag]
    if len(sys.argv) < 2:
        print("Usage: python scan_headless.py <output_dir> [dds_ns_flag]")
        print("  <output_dir> : required path where per-type IDL files will be written")
        print("  [dds_ns_flag] : optional true/false (default: true)")
        sys.exit(2)

    out_dir = sys.argv[1]
    dds_flag = True
    if len(sys.argv) > 2:
        arg = sys.argv[2].lower()
        if arg in ('0', 'false', 'no', 'off'):
            dds_flag = False

    perform_headless_scan(output_dir=out_dir, dds_ns_flag=dds_flag)
