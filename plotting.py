from ipyleaflet import (Map, basemaps, WidgetControl, GeoJSON, Choropleth, LegendControl)
from ipywidgets import HTML, widgets, HBox, VBox
from branca.colormap import linear
import pandas as pd
pd.options.plotting.backend = "plotly"

import numpy as np
import plotly.graph_objs as go

# import from load_stats
from load_stats import (stat_ids, stat_tuple, stat_dict, id_to_name, 
                        choro_data_complete, geo_data, units)

# # Building the interface
# ## preparations

# define dropdown widgets for stats and year

stats_widget = widgets.Dropdown(
    options=stat_tuple,
    value= stat_ids[0],
    description='statistics:',
    disabled=False,
)

year_widget = widgets.Dropdown(
    options= range(2010,2019),
    value=2018,
    description='year:',
    disabled=False,
)

vb = VBox([stats_widget, year_widget])


# create initial bar chart figure with random values (later overwritten when map is created)
data = [go.Bar(x= np.arange(2010,2020), y=[0]*10)]
layout = {'xaxis':{'title':'year'}, 'title':{'text': 'Frankfurt'}}
fig = go.FigureWidget([data[0],data[0]], layout)
fig.update_layout(legend=dict(
    orientation='h',
    yanchor="bottom",
    y=1.,
    xanchor="center",
    x=0.5
));


# ## functions for callbacks and interactions
# set parameters

cm = linear.Purples_03 # color map for county area coloring


# Updating the bar charts on clicking a ditrict. Basic logic:
# - `fig.data` contains 2 entries, one for each county to be shown (1st is more recently clicked)
# - after clicking, new stats is passed via arguments `district_id, stats_name, stats_data_frame, current_year`
# - assign: new stats instead of oldest data; most recent data take place of previously old data **needs refinement!**
# - bar layout properties are updated accordingly

def update_figure(district_id, stats_name, stats_data_frame, current_year):
    # add new stattistics
    stats_to_add = stats_data_frame[stats_data_frame['id']==district_id].copy(deep=True)
    stats_to_add['colors'] = 'rgb(189, 112, 15)'
    stats_to_add.loc[stats_to_add['year']==current_year, 'colors'] = 'gray'
    
    bar = fig.data[1]
    bar.x = stats_to_add['year']
    bar.y = stats_to_add[stats_name]
    bar.marker.color= stats_to_add['colors']
    bar.opacity= 1.
    
    fig.data = (bar,fig.data[0])
    
    fig.data[1].opacity=.5
    fig.data[0].name= id_to_name[district_id]

    fig.update_layout(title=f"{fig.data[0].name} vs. {fig.data[1].name}", template='plotly_white')

def show_map(selected_stats, year):
    html = HTML('''district''')
    html.layout.margin = '-5px 5px 5px 5px'    
    control = WidgetControl(widget=html, position='topright', min_width = 250, max_width=500)

    # load selected stats into choro_data_all
    choro_data_all, unit = choro_data_complete[selected_stats], units[selected_stats]
    # for geo plot extract chosen year and assign to choro_data
    choro_data = choro_data_all[choro_data_all['year']==year]
    choro_data = dict(choro_data.drop(columns=['year', 'name']).to_dict('split')['data'])
    
    # initialize bar chart with Frankfurt vs Offenbach
    update_figure('06412', selected_stats, choro_data_all, year)
    update_figure('06413', selected_stats, choro_data_all, year)
    
    # set y-axis label
    fig.update_layout(yaxis_title=f'{stat_dict[selected_stats]} [{unit} per capita]', yaxis={'range':[0,max(choro_data_all[selected_stats])]})
    

    # define chropleth layer for basic geo plotting
    layer = Choropleth(geo_data=geo_data,choro_data=choro_data,colormap=cm,
                       style={'fillOpacity': 0.65, 'dashArray': '0, 0', 'weight':1})
    
    # define GeoJSON layer for click and hover event interactions
    geo_json = GeoJSON(data=geo_data,
                       style={'opacity': 0, 'dashArray': '9', 'fillOpacity': .0, 'weight': 1},
                       hover_style={'color': 'blue', 'dashArray': '0', 'fillOpacity': 0.7})

    # needed for HTML update    
    for f in geo_data['features']:
        f['value'] = choro_data[f['id']] # choro_data[f['properties']['GEN']]

    # on hover, the html text filed is updated to show properties of the hovered county
    def update_html(feature,  **kwargs):
        html.value = '''
            <center><p><b>{}</b>:</p> {} {} {}</center>
        '''.format(id_to_name[feature['id']],
                   feature['value'],
                   unit,
                  'per capita')
    
    # this function is called upon a click events and triggers figure update with the arguments passed from the map
    def update_fig_on_click(feature, **kwags):
        update_figure(feature['id'], selected_stats, choro_data_all, year)
    geo_json.on_hover(update_html)
    geo_json.on_click(update_fig_on_click)

    # add layers and controls; set layout parameters
    m = Map(basemap=basemaps.OpenStreetMap.Mapnik, center=(50.5,9), zoom=8)
    m.add_layer(layer)
    m.add_layer(geo_json)
    m.add_control(control)
    m.layout.width = '40%'
    m.layout.height = '700px'

    # custom made legend using min/max normalization
    min_value, max_value = min(choro_data.values()), max(choro_data.values())
    legend = LegendControl(
          {str(min_value)+' '+str(unit)+' per capita': cm(0), #hier
          str(min_value+0.5*(max_value-min_value))+' '+str(unit)+' per capita': cm(.5),
          str(max_value)+' '+str(unit)+' per capita': cm(1)},
          name= f"{stat_dict[selected_stats]} ({year})", position="bottomleft")
    m.add_control(legend)
    return HBox([m, fig])