import itertools
import numpy as np
import pandas as pd
import geopandas as gpd
import osmnx as ox

# *조회가 안 될때, https://www.openstreetmap.org 기입하고 싶은 지역명을 먼저 확인하고 실행하세요. 
# road_type : 1(고속도로), 2(간선도로), 3(집산도로)
class point_generator_with_OSM:
    def __init__(self):
        self.road_type = [2,3]
        
    # filter road 
    def filter_edges(self, edges):
        edges['highway'] = [i if type(i) != list else "-".join(i) for i in edges['highway']]

        highway_cat_lst = ['motorway', 'motorway_link', 'rest_area', 'services', 'trunk', 'trunk_link']
        mainRoad_cat_lst = ['primary', 'primary_link', 'secondary', 'secondary_link', 'tertiary', 'tertiary_link']
        minorRoad_cat_lst = list(set(edges['highway']) - set(highway_cat_lst + mainRoad_cat_lst))
        road_type_dict = {1: highway_cat_lst, 2: mainRoad_cat_lst, 3: minorRoad_cat_lst}

        target_road = list(itertools.chain(*[road_type_dict[i] for i in self.road_type]))
        edges = edges.loc[[i in target_road for i in edges['highway']]]
        edges = edges.loc[(edges['length'] >= 10)]    
        edges = edges.reset_index()
        return edges
    
    # generate point
    def generate_point(self, target_edges, count):
        # generate point geometry
        generated_nodes = []
        for _ in range(count):

            # choice edge, cutting ratio and linestring direction randomly.
            random_row = np.random.randint(len(target_edges))
            random_ratio = np.random.choice([0.1, 0.2, 0.3, 0.4, 0.5])
            random_reverse = np.random.choice([True, False])
            
            selected_row = target_edges.iloc[[random_row]].reset_index(drop=True)
            selected_row = selected_row.to_crs(5174)

            linestring = selected_row['geometry'].iloc[0]
            cut_length = selected_row['geometry'].length.iloc[0]  * random_ratio    
            
            if random_reverse:
                linestring = linestring.reverse()
            
            split_point = linestring.interpolate(cut_length)    
            generated_nodes.append(split_point)
            
        generated_nodes = gpd.GeoDataFrame(generated_nodes, columns=['geometry'], geometry='geometry', crs=5174)
        generated_nodes = generated_nodes.to_crs(4326)

        generated_nodes['lon'] = [i.x for i in generated_nodes['geometry']]
        generated_nodes['lat'] = [i.y for i in generated_nodes['geometry']]

        return generated_nodes
    
    def point_generator_about_placeName(self, place, count):
        # load road
        G = ox.graph_from_place(place, network_type="drive_service", simplify=True)
        _, edges = ox.graph_to_gdfs(G)
        edges = edges.reset_index(drop=True)

        # select road
        edges = self.filter_edges(edges)
        
        # generate point
        generated_nodes = self.generate_point(edges, count)
        return generated_nodes

    def point_generator_about_geometry(self, geoData):
        # load road
        place_lst = list(set(geoData['geoName']))
        edges_lst = []
        for plc in place_lst:
            G = ox.graph_from_place(plc, network_type='drive_service', simplify=True)
            _, edge = ox.graph_to_gdfs(G)
            # select road
            edge = self.filter_edges(edge)
            edges_lst.append(edge)
        edges = pd.concat(edges_lst).reset_index(drop=True)

        # generate point
        generated_nodes_lst = []
        for _, row in geoData.iterrows():
            sub_edges = edges.loc[(edges['geometry'].intersects(row['geometry']))].reset_index(drop=True)

            generated_nodes = self.generate_point(sub_edges, row['count'])
            generated_nodes['id'] = row['id']
            generated_nodes = generated_nodes[['id', 'geometry', 'lon', 'lat']]
            generated_nodes_lst.append(generated_nodes)
        generated_nodes_lst = pd.concat(generated_nodes_lst).reset_index(drop=True)
        return generated_nodes_lst