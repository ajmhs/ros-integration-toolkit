#
# (c) 2025 Copyright, Real-Time Innovations.  All rights reserved.
# No duplications, whole or partial, manual or electronic, may be made
# without express written permission.  Any such copies, or revisions thereof,
# must display this notice unaltered.
# This code contains trade secrets of Real-Time Innovations, Inc.
#
import os
import sys
import json
from pathlib import Path
from rosp import rosparser
from idlp import idltypex
from sqldb import sql3db

def perform_headless_scan(output_dir=None):
    """Perform a headless scan and export.

    output_dir: optional path to place exported IDL files. If None, defaults to './'
    """

    ros_path = os.getenv('AMENT_PREFIX_PATH')
    db_filename = os.path.abspath('./headless.db')
    # use provided output_dir or default to current directory './'
    base_path = os.path.abspath(output_dir) if output_dir else os.path.abspath('./')

    rosparser.scan_paths_for_datatype_files([ros_path], ['.msg', '.srv', '.action'], [''], False, db_filename)

    # Collect all types from all loaded databases
    types_to_export = []
            
    types_db = sql3db.SQL3Util(db_filename)
    # Get all datatypes from this database
    all_data_types = types_db.datatypes_reftree()
			
    for type_id in all_data_types:
        # Get the full type record with members
        type_rec = types_db.get_record_tree_by_typename_or_idkey('', '', type_id)
            
        if type_rec:
            # a list of lists is returned
            for type_item in reversed(type_rec):
                # Check if this type is already in the export array
                include_type = True
                for checkItem in types_to_export:
                    if checkItem[0][0] == type_item[0][0]:
                        include_type = False
                        break
                if include_type:
                    types_to_export.append(type_item)
			
    types_db.database_close()
		
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
            
            # Export this single type
            idltypex.export_idl_type_file([type_item], export_filename)
                
        except Exception as e:
            print(f"Failed to export type: {str(e)}")
    

# --------------------------------------------------
if __name__ == "__main__":
    # allow optional output directory as first CLI argument
    out_dir = sys.argv[1] if len(sys.argv) > 1 else None
    perform_headless_scan(out_dir)
