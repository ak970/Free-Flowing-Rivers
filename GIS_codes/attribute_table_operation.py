import arcpy

# --- Paths ---
hydro_fc = r"D:\RiverATLAS\HydroRIVERS_v10_as_shp\HydroRIVERS_v10_as_shp\HydroRIVERS_v10_peninsular2.shp"   # standalone shapefile
ffr_fc   = r"D:\RiverATLAS\Free_Flowing_Rivers\Mapping the worlds free-flowing rivers_Data_Geodatabase\Mapping the worlds free-flowing rivers_Data_Geodatabase\FFR_river_peninsular.gdb\FFR_river_peninsular"        # in geodatabase
dam_fc = r"D:\RiverATLAS\Global_Dam_Watch_GDW\GDW_filtered\GDW_barriers_filtered.shp"    # dam shapefile

for f in arcpy.ListFields(dam_fc):
    print(f.name, f.type)

# --- Field names ---
hydro_rivid_field = "HYRIV_ID"
hydro_basin_field = "HYBAS_L12"

ffr_rivid_field   = "REACH_ID"     # change this if your river ID field has another name
ffr_basin_field   = "HYBAS_L12"     # new field to be added to FFR

original_field_to_copy = "GOID" 
field_to_copy = "GOID"
dam_rivid_field = "HYRIV_ID"

shapefile_to_copy_from = ffr_fc
shapefile_to_copy_to = dam_fc

# --- 1. Build lookup dictionary from shapefile to copy from ---
# Create a dictionary common_field:field_to_copy
print("Building lookup dictionary from HydroRIVERS...")

lookup = {}

with arcpy.da.SearchCursor(shapefile_to_copy_from, [ffr_rivid_field, original_field_to_copy]) as scur:
    for rivid, fieldid in scur:
        if rivid is not None:
            lookup[int(rivid)] = fieldid   # ensure int key
            

print(f"Loaded {len(lookup)} river ID → basin ID pairs.")

lookup

# --- 2. Add new field to the shapefile if it does not exist ---
existing_fields = [f.name for f in arcpy.ListFields(shapefile_to_copy_to)]

if field_to_copy not in existing_fields:
    print(f"Adding field {field_to_copy} to {shapefile_to_copy_to} shapefile...")
    # Adjust field type if needed (LONG is typical for HYBAS_L12)
    arcpy.AddField_management(shapefile_to_copy_to, field_to_copy, "DOUBLE")
else:
    print(f"Field {field_to_copy} already exists in {shapefile_to_copy_to}.")

# --- 3. Update FFR using the lookup dictionary ---
print("Updating FFR with basin IDs...")

updated = 0
not_found = 0

# with arcpy.da.UpdateCursor(ffr_fc, [ffr_rivid_field, ffr_basin_field]) as ucur:
#     for rivid, basinid in ucur:
#         if rivid in lookup:
#             ucur.updateRow((rivid, lookup[rivid]))
#             updated += 1
#         else:
#             # Leave as NULL
#             not_found += 1
        
            
with arcpy.da.UpdateCursor(shapefile_to_copy_to, [dam_rivid_field, field_to_copy]) as ucur:
    for rivid_dec, fieldid in ucur:
        if rivid_dec is None:
            not_found += 1
            continue

        rivid_int = int(rivid_dec)  # <-- key step: 12345.000 -> 12345

        if rivid_int in lookup:
            ucur.updateRow((rivid_dec, lookup[rivid_int]))
            updated += 1
        else:
            not_found += 1
            
            
            
print(f"Done.")
print(f"Updated features: {updated}")
print(f"No match found (left NULL): {not_found}")


# Check field type

for f in arcpy.ListFields(dam_fc):
    if f.name.upper() == "HYBAS_L12":
        print(f.name, f.type)


# Delete and add the same field
field_name = "HYBAS_L12"

# Check if field exists
fields = [f.name for f in arcpy.ListFields(ffr_fc)]

if field_name in fields:
    print("Deleting existing field:", field_name)
    arcpy.DeleteField_management(ffr_fc, field_name)

# Now add it again with the CORRECT type
# Change type here based on HydroRIVERS field type:
# "LONG", "DOUBLE", or "TEXT"
arcpy.AddField_management(ffr_fc, field_name, "DOUBLE")

print("Field recreated with correct type.")


# Sample check... check the first few features

print("Sample HYRIV_ID from HydroRIVERS:")
with arcpy.da.SearchCursor(shapefile_to_copy_to, [field_to_copy]) as cur:
    for i, (v,) in enumerate(cur):
        print(v)
        if i >= 9:
            break

print("\nSample river IDs from FFR:")
with arcpy.da.SearchCursor(ffr_fc, [ffr_rivid_field]) as cur:
    for i, (v,) in enumerate(cur):
        print(v)
        if i >= 9:
            break


# BAS_ID -> BAS_ID_old
old_name = "BAS_ID"
new_name = "BAS_ID_old"
new_alias = "Basin ID updated"  # optional, can be more descriptive

arcpy.AlterField_management(ffr_fc, old_name, new_name, new_alias)

print("Field renamed successfully.")


# HYBAS_L12 -> BAS_ID
old_name = "HYBAS_L12"
new_name = "BAS_ID"
new_alias = "Basin ID new"  # optional, can be more descriptive

arcpy.AlterField_management(ffr_fc, old_name, new_name, new_alias)

print("Field renamed successfully.")


# 3. Delete old field
arcpy.DeleteField_management(dam_fc, "BAS_ID")

old_field = "HYBAS_L12"
new_field = "BAS_ID"

# 1. Add new field (use correct type!)
arcpy.AddField_management(dam_fc, new_field, "DOUBLE")  # or DOUBLE / TEXT



# 2. Copy values
arcpy.CalculateField_management(shapefile_to_copy_to, new_field, f"!{old_field}!", "PYTHON3")

print("Field renamed via add-copy-delete method.")

# Sample check... check the first few features

print("Sample HYRIV_ID from HydroRIVERS:")
with arcpy.da.SearchCursor(dam_fc, ["HYBAS_L12"]) as cur:
    for i, (v,) in enumerate(cur):
        print(v)
        if i >= 9:
            break

# print("\nSample river IDs from FFR:")
# with arcpy.da.SearchCursor(ffr_fc, [ffr_rivid_field]) as cur:
#     for i, (v,) in enumerate(cur):
#         print(v)
#         if i >= 9:
#             break

