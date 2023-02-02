### MeshRanger.py
# Author: tcm <spam@noclip.sh>
#
# Description: Process a log file from MeshLogger.py to visualize GPS points.
#              Output an HTML file from Plotly with an interactive graphic.
# Reference:
#   https://pandas.pydata.org/pandas-docs/stable/reference/api/
#   https://plotly.com/python/builtin-colorscales/#named-builtin-continuous-color-scales
#   https://www.shanelynn.ie/pandas-drop-delete-dataframe-rows-columns/
#
# Usage: output a plotly map with the input data.
#   python MeshRanger.py <location_to_mesh_log_file>
#   python MeshRanger.py /home/user/not_porn/grandmas/mesh.log

import sys, re, math, os
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly


# simple arg check
if len(sys.argv) < 2:
    print(f"usage:\n  {sys.argv[0]} <file_to_process>\n  {sys.argv[0]} ../../MeshLoggerPython/mesh.log\n")

    pathToMeshLog = '../../MeshLoggerPython/mesh.log'
else:
    pathToMeshLog = sys.argv[1]

# Base station coordinate
BASE_LAT = 39.047612
BASE_LON = -77.474337






# Produce vertices around circumference of center to draw a trace in Plotly
# radius in meters
def create_circle(center_lon, center_lat, radius):
    points = []
    R = 6371e3  # Earth's radius in meters
    for i in range(361):
        bearing = math.pi * i / 180.0
        lat = math.asin(math.sin(math.radians(center_lat)) * math.cos(radius / R) + 
              math.cos(math.radians(center_lat)) * math.sin(radius / R) *
              math.cos(bearing))
        lon = math.radians(center_lon) + math.atan2(math.sin(bearing) *
              math.sin(radius/R) * math.cos(math.radians(center_lat)), 
              math.cos(radius/R) - math.sin(math.radians(center_lat)) * math.sin(lat))
        points.append((math.degrees(lon), math.degrees(lat)))
    return points


print("Starting...",end='')

coords = []

### iterate thru file to find valid coordinates to splat on map
with open( pathToMeshLog, 'r' ) as f:
    for line in f:
        match = re.search(r"([\d]+),(-?\d+\.\d+),(-?\d+\.\d+),(\d+)", line)
        if match:
            epoch = int(match.group(1))
            lat = float(match.group(2))
            lon = float(match.group(3))
            alt = int(match.group(4))
            coords.append([epoch, lat, lon, alt])

# Create the Dataframe from the list
df = pd.DataFrame(coords, columns=['epoch', 'lat', 'lon','alt'])

df['date'] = ['{}'.format( datetime.fromtimestamp(i).strftime('%Y-%m-%d') ) for i in df['epoch'] ]
df['time'] = ['{}'.format( datetime.fromtimestamp(i).strftime('%H:%M:%S') ) for i in df['epoch'] ]

### render map elements

# GPS events
fig = px.scatter_mapbox(
    df,
    lat="lat", lon="lon",
    zoom=12,
    color="date",
    size='alt',
    # animation_frame="time",
    # animation_group="date",
    # text = df['time'],
    hover_data={
        'epoch':False,
        'lat':':.5f',
        'lon':':.5f',
        'alt':True,
        'date':True,
        'time':True,
    },
    size_max=10,
    color_continuous_scale=px.colors.sequential.Viridis,
)

# BASE STATION marker
fig.add_trace(go.Scattermapbox(
    mode = "markers",
    lat = [ BASE_LAT ],
    lon = [ BASE_LON ],
    hoverinfo = 'name',
    name= "Base",
    showlegend = True,
    marker = {
                'symbol': 'circle',
                'color': "darkred", 
                'size': 7,
    },
))


### RANGE RINGS
# draw circles at intervals from base station
# radius in meters
RANGE_RING_RADII = range(1,6,1)

for radius in RANGE_RING_RADII:
    vertices = create_circle( BASE_LON, BASE_LAT, radius*1000 )
    fig.add_trace(go.Scattermapbox(
        mode='lines',
        name="{}km".format(radius),
        hoverinfo='name+text',text='',
        lon=[point[0] for point in vertices],
        lat=[point[1] for point in vertices],
        marker=go.scattermapbox.Marker( size=1, color='#bb9' )
    ))
    del vertices


# update map details
fig.update_layout(
    mapbox = dict(
        accesstoken = open( "{}/.mapbox_token".format( os.path.dirname(os.path.realpath(__file__)) ) ).read(),
        center = { 'lat': BASE_LAT, 'lon': BASE_LON },
        style = "light", # 'basic', 'streets', 'outdoors', 'light', 'dark', 'satellite', 'satellite-streets'
        zoom=12,
    ),
    width=1300,
    height=950,
    showlegend = True,
)

# update layout with title and shifting legend
fig.update_layout(
    coloraxis_colorbar_x=1,
    coloraxis_colorbar_len=0.7,
    legend_y=.96,
    title=dict(
    text='Mesh Ranger -- Position data for meshtastic device',
    ))

now = datetime.now().strftime("%c")

# add footnote
fig.add_annotation(
    text = (f"Source: spam@noclip.sh<br />© nobody<br />{now}")
    , showarrow=False
    , x = 0.05
    , y = 0.008
    , xref='paper'
    , yref='paper' 
    , xanchor='left'
    , yanchor='bottom'
    , xshift=0
    , yshift=0
    , font=dict( size=10, color="darkgoldenrod")
    , align="left"
    ,)


# html file
fig.write_html( "{}/../html/plot.html".format( os.path.dirname(os.path.realpath(__file__)) ) )
print( "Done." )



