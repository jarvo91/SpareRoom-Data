# =============================================================================
# Heat-Map on Geographical Area
# =============================================================================

import matplotlib.cm
sns.set(style="white", color_codes=True)
from mpl_toolkits.basemap import Basemap
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection
from matplotlib.colors import Normalize

'''
-- Matplotlib Basemap --
To draw a map in Basemap I had to define a few things:
- Where I wanted the map to be centred
- The latitude and longitude of the lower left corner of the "bounding box"
    around the area that I wanted to map.
- The latitude and longitude of the upper right corner of the bounding box
    around this area
- Instead of the corners of the bounding box it is also possible to use the
     width and height of the area I wanted to map in metres.

To get the bounding box of the map I used the following website:
    http://boundingbox.klokantech.com/
    (use DublinCore coordinates type)


# Test: Draw basic empty map -------
# From:
# http://basemaptutorial.readthedocs.io/en/latest/basic_functions.html
fig, ax = plt.subplots(figsize=(10,20))
m = Basemap(resolution = 'l', # c (crude), l, i, h, f (full) or None
            projection = 'merc', # see: http://matplotlib.org/basemap/users/mapsetup.html
            # westlimit=-0.134854; southlimit=51.359999; eastlimit=0.196795; northlimit=51.53308
            lat_0 = 51.42, lon_0 = 0.03, # centre point of your map
            llcrnrlon = -0.14, llcrnrlat = 51.36,#lower left corner
            urcrnrlon = 0.2, urcrnrlat = 51.53) #uper right corner
m.drawmapboundary(fill_color = '#46bcec')
m.fillcontinents(color = '#f2f2f2', lake_color = '#46bcec')
m.drawcoastlines()
'''

# Plot datapoints on map:

# WHERE ARE PEOPLE LOOKING FOR ROOMS?
# If we want to plot where people are looking,
#   we need to match their postcodes to an approximate lat. and long.
# The following website contains a dataset to match outcodes with latitude and longitude:
# https://www.freemaptools.com/download-uk-postcode-lat-lng.htm
postcodes = pd.read_csv('data/postcode-outcodes.csv', index_col='id')
postcodes = postcodes.loc[postcodes['postcode'].isin(mates_areas_df.index.values)]
postcodes.head()

# Merge dataframes using the postcode as a reference
mates_areas_df['postcode'] = mates_areas_df.index.values
mates_areas_df = mates_areas_df.merge(postcodes, on='postcode')
mates_areas_df.head()


# Let's plot the 'scattered' points on a map,
# the size correlates to how many new houses are in that area.
fig7, ax7 = plt.subplots(figsize=(16,12))

# Let's also expand the Basemap class, so that we can add a custom
#   "labelling" function that reads a dataframe with area labels
#   with their longitudes and latitudes and plots them onto our map
# It will be useful to label postcode areas
# (inspired by country labelling "hack" proposed here:
#  https://stackoverflow.com/questions/30963189/country-labels-on-basemap)
class MyBasemap(Basemap):
    def printlabels(self, df_filepath, col_id='postcode', d=0.025, lon_correct=0, lat_correct = 0):
        data = pd.read_csv(df_filepath)
        data = data[(data.latitude > self.llcrnrlat+d) & (data.latitude < self.urcrnrlat-d) &
                    (data.longitude > self.llcrnrlon+d) & (data.longitude < self.urcrnrlon-d)]
        for ix, area in data.iterrows():
                self.ax.text(*self(area.longitude+lon_correct,
                                    area.latitude+lat_correct), s=area[col_id],
                                    fontsize='small', weight='bold')

# Draw basic empty map:
m2 = MyBasemap(resolution = 'i', # c (crude), l, i, h, f (full) or None
            projection = 'merc', # see: http://matplotlib.org/basemap/users/mapsetup.html
            # westlimit=-3.070616; southlimit=53.354529; eastlimit=-2.82742; northlimit=53.462588
            lat_0 = 53.40856, lon_0 = -2.94904, # centre point of your map
            llcrnrlon = -3.07, llcrnrlat = 53.35,# lower left corner
            urcrnrlon = -2.82, urcrnrlat = 53.47, ax=ax7) # upper right corner

m2.drawmapboundary(fill_color = '#46bcec')
m2.fillcontinents(color = '#f2f2f2', lake_color = '#46bcec')
m2.drawcoastlines()

m2.printlabels('data/postcode-outcodes.csv', lon_correct=-0.01)

def plot_area(in_df, in_map):
    count = in_df['count']
    x, y = in_map(in_df.longitude, in_df.latitude)
    size = (count/1000) ** 2 * 2 + 3
    in_map.plot(x, y, 'o', markersize = size,
                color = '#dd4422', alpha=0.8)

# Uncomment the below line to visualise the
# bubble plot
# mates_areas_df.apply(plot_area, args=(m2,), axis=1)


# Draw boundary (county) lines:
# Use SHAPEFILES to do this
# (http://www.opendoorlogistics.com/downloads/)
m2.readshapefile('data/uk_areas_svg/Districts', 'postcodes')
m2.postcodes_info

# USE DATA TO COLOUR MAP:
df_poly = pd.DataFrame( {
            'shapes' : [Polygon(np.array(shape), True) for shape in m2.postcodes],
            'postcode' : [area['name'] for area in m2.postcodes_info]})
df_poly = df_poly.merge(mates_areas_df, on='postcode', how='left')
df_poly = df_poly[~df_poly['count'].isin([np.NaN])]
df_poly.head()

# Color map ideas: http://matplotlib.org/examples/color/colormaps_reference.html
cmap = plt.get_cmap('Oranges')
pc = PatchCollection(df_poly.shapes, zorder=2)
# The ‘zorder’ argument just makes sure that the patches that we are creating
#   end up on top of the map, not underneath it.
norm = Normalize()
# normalise values to match the colormap specs
pc.set_facecolor(cmap(norm(df_poly['count'].fillna(0).values)))
ax7.add_collection(pc)

#  Add a colorbar, this makes it at lot easier to
#   interpret the colours of the map and relate them to a number.
mapper = matplotlib.cm.ScalarMappable(norm = norm, cmap = cmap)
mapper.set_array(df_poly['count'])
plt.colorbar(mapper, shrink=0.4)
plt.title('Room Demand as no of "room wanted" ads per postcode', fontsize=18)

fig7.set_tight_layout(True)

plt.show()
