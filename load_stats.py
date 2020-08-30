import pandas as pd
import json
from datenguidepy import get_statistics, Query

# # Define functions to load datenguide data into data frames

# default values (for testing)
selected_stats = 'AI1903'
year = 2013

def get_data_all_years(selected_stats=selected_stats):
    '''
    For a given `selected_stats` returns data and unit, where
    data [dataframe]: the chosen statistics from datenguide.py with columns 'name', 'year', 'id' and stat values
    units [string]: name of corresponding unit
    '''
    q = Query.all_regions(parent='06')
    stat = q.add_field(selected_stats)

    data = q.results(verbose_enums=True, add_units = True)
    # for some reason entries are produced twice; remove them
    data.drop_duplicates(inplace=True)
    data, unit = data[['name', 'year', 'id', selected_stats]], data[selected_stats+'_unit'].iloc[0]

    return data, unit

def get_statistics_description(selected_stats=selected_stats):
    '''
    get the description string for statistics 'selected_stats'
    '''
    q = Query.all_regions(parent='06')
    stat = q.add_field(selected_stats)
    return stat.description()


# # load geoJSON data

# the geoJSON file was obtained from http://opendatalab.de/projects/geojson-utilities/  
# (contains only data for Hessen on level NUTS3)
geojson_data = json.load(open('data/landkreise_simplify200.geojson','r'))

# set property 'name' for the county name to make it consistent with datenguide data
for feature in geojson_data['features']:
    feature['properties']['name'] = feature['properties']['BEZ']

# write to `geo_data` with identifier key named as `id`  
# TODO: why introduce a new variable here?

geo_data = {'features':[], 'id':[]}
for f in geojson_data['features']:
    f.update(id=f['properties']['AGS']) #f['properties']['GEN'])
    geo_data['features'].append(f)


# # define and load all statistics that will be available in the app
stat_ids = ['AI1903', 'AI1904', 'FLC048']
stat_descriptions = [get_statistics_description(si) for si in stat_ids]
stat_tuple = tuple(zip(stat_descriptions, stat_ids))
stat_dict = dict((y, x) for x, y in stat_tuple)

choro_data_complete, units = dict(), dict()
for st in stat_ids:
    choro_data_complete[st], units[st] = get_data_all_years(st)
    
c = choro_data_complete[stat_ids[0]] # take one statistics data set for generating name/id mapping
id_to_name = {ids: c.loc[c['id']==ids, 'name'][0] for ids in c['id'].unique()}