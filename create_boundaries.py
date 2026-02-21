import geopandas as gpd
from shapely.geometry import Polygon

# Create sample protected areas in Rondônia
areas = [
    {
        'NAME': 'Pacaás Novos National Park',
        'DESIG': 'National Park',
        'geometry': Polygon([
            (-63.5, -10.5),
            (-63.0, -10.5),
            (-63.0, -10.0),
            (-63.5, -10.0),
            (-63.5, -10.5)
        ])
    },
    {
        'NAME': 'Jaru Biological Reserve',
        'DESIG': 'Biological Reserve',
        'geometry': Polygon([
            (-61.5, -10.0),
            (-61.0, -10.0),
            (-61.0, -9.5),
            (-61.5, -9.5),
            (-61.5, -10.0)
        ])
    }
]

gdf = gpd.GeoDataFrame(areas, crs="EPSG:4326")
gdf.to_file('protected-areas.geojson', driver='GeoJSON')
print("✅ Created protected-areas.geojson")
