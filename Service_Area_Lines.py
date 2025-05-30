# -*- coding: utf-8 -*-
"""
Simplified population and employment within 0.5 miles
Developed by Asher Cipinko for Kimley-Horn, May 2025
"""

import tkinter as tk
from tkinter import ttk

def update_progress(progress,message):
    progress_var.set(progress)
    message_var.set(message)
    root.update_idletasks()
    
def close_window():
    root.destroy()

root = tk.Tk()
root.title("Calculating Service Area")

progress_var = tk.DoubleVar()
progress_bar = ttk.Progressbar(root, variable=progress_var, maximum=100, length=300)
progress_bar.pack(padx=200, pady=30)

message_var = tk.StringVar()
message_label = tk.Label(root, textvariable=message_var)
message_label.pack(padx=200, pady=30)

close_button = tk.Button(root, text="Close", command=close_window)
close_button.pack(padx=200, pady=(0,30))

update_progress(progress=10,message="Loading Data")

import geopandas as gpd
import pandas as pd
import os
import sys

exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
linesfile = os.path.join(exe_dir, 'Lines.shp')
sedfile = os.path.join(exe_dir, 'ACS.shp')
acs = os.path.join(exe_dir, 'ACS.xlsx')
outputs = os.path.join(exe_dir, 'Outputs.xlsx')
lehdfile = os.path.join(exe_dir, 'lehd.csv')
lehd = pd.read_csv(lehdfile)

#prepare lehd
lehd['newgeo'] = lehd['w_geocode'].astype(str).str[:10]
lehdsum = lehd.groupby('newgeo', as_index=False)['C000'].sum()
lehdsum['newgeo'] = '0' + lehdsum['newgeo'].astype(str)

# Read lines
lines = gpd.read_file(linesfile)
lines = lines.set_crs('EPSG:3857')

# Read SED
sed = gpd.read_file(sedfile)
sed = sed.to_crs('EPSG:3857')

# Clean geometries
lines = lines[lines.is_valid & (~lines.is_empty)]
sed = sed[sed.is_valid & (~sed.is_empty)]

# Rename C000 to employment
lehdsum = lehdsum.rename(columns={'C000': 'totalemp'})

# Merge employment onto SED based on matching GEOID to newgeo
sed = sed.merge(lehdsum, how='left', left_on='GEOID', right_on='newgeo')

update_progress(progress=25,message="Creating Buffers")

# Buffer
lines['geometry'] = lines.buffer(804.5)

update_progress(progress=45,message="Analyzing Buffers")

sed['area_base']= sed.geometry.area

#Intersect buffers and SED
intersects = gpd.overlay(lines, sed, how='intersection', keep_geom_type=True)

#Give polygons sets area values ----------------------------------------------------- update proper field names
intersects['area_inter']= intersects.geometry.area

#Merge area values into one matrix
intersects['percent_area'] = intersects['area_inter'] / intersects['area_base']
intersects['population'] = intersects['percent_area'] * intersects['B01003_001']
intersects['employment'] = intersects['percent_area'] * intersects['totalemp']

# Summarize values by unique OBJECTID_1 (from the intersects GeoDataFrame)
summary = intersects.groupby('OBJECTID1', as_index=False)[['population', 'employment']].sum()

update_progress(progress=100,message="Analysis Complete and Files Updated")

root.mainloop()