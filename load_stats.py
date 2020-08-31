import pandas as pd
import json
from datenguidepy import get_statistics, Query

# # Define functions to load datenguide data into data frames

# default values (for testing)
selected_stats = 'AI1903'
year = 2013

def get_population_all_years():
    '''
    Returns pop [dataframe]: the population for all Hesse regions from datenguide.py with columns 'name', 'year', 'id' and stat values
    '''
    selected_stats = 'BEVSTD' # Bevölkerungsstand (population statistic)
    selected_stats1 = 'R12411' # Fortschreibung des Bevölkerungsstandes (forward projection of populatin statistic)
    
    q = Query.all_regions(parent='06')
    stat = q.add_field(selected_stats)
    stat.add_args({'statistics' : selected_stats1}) # One more level in this stat (exact source of the stat)

    pop = q.results(verbose_enums=True, add_units = True)
    # for some reason entries are produced twice; remove them
    pop.drop_duplicates(inplace=True)
    
    pop = pop[['year', 'id', selected_stats]]
    
    return pop

pop = get_population_all_years()

def get_data_all_years(selected_stats=selected_stats, norm=0, pop=pop):
    '''
    For a given `selected_stats` returns data and unit, where
    data [dataframe]: the chosen statistics from datenguide.py with columns 'name', 'year', 'id' and stat values
    units [string]: name of corresponding unit
    
    Input:
    norm [int]: 0 if no normalization requested, else normalization by population and multiplied by factor norm
    pop [datafram]: dataframe with the population of all Hesse regions
    '''
    q = Query.all_regions(parent='06')
    stat = q.add_field(selected_stats)

    data = q.results(verbose_enums=True, add_units = True)
    # for some reason entries are produced twice; remove them
    data.drop_duplicates(inplace=True)
    
    data, unit = data[['name', 'year', 'id', selected_stats]], data[selected_stats+'_unit'].iloc[0]

    if norm != 0:
        # Normalize dataframe data here by modifying selected_stats with the population dataframe
        df = pd.merge(data, pop)
        df[[selected_stats]] = df[selected_stats] / df['BEVSTD'] * norm
    
        data = df[['name', 'year', 'id', selected_stats]]
        
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
stat_ids = ['AI1903', 'AI1904', 'BEV083']
normalize = [0, 0, 1000]
stat_descriptions = [get_statistics_description(si) for si in stat_ids]
stat_tuple = tuple(zip(stat_descriptions, stat_ids))
stat_dict = dict((y, x) for x, y in stat_tuple)

choro_data_complete, units = dict(), dict()
for ix in range(len(stat_ids)):
    st = stat_ids[ix]
    norm = normalize[ix]
    choro_data_complete[st], units[st] = get_data_all_years(st, norm, pop)
        
c = choro_data_complete[stat_ids[0]] # take one statistics data set for generating name/id mapping
id_to_name = {ids: c.loc[c['id']==ids, 'name'][0] for ids in c['id'].unique()}