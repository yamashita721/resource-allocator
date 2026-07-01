import json
import os
import networkx as nx
import numpy as np
from typing import List, Tuple, Dict, Any, Optional

DATA_DIR = "data"

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates direct great-circle distance in km."""
    r = 6371.0
    phi1 = np.radians(lat1)
    phi2 = np.radians(lat2)
    delta_phi = np.radians(lat2 - lat1)
    delta_lambda = np.radians(lon2 - lon1)
    
    a = np.sin(delta_phi/2)**2 + np.cos(phi1) * np.cos(phi2) * np.sin(delta_lambda/2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    return round(r * c, 2)

class RouteOptimizer:
    def __init__(self, data_dir: str = DATA_DIR):
        self.data_dir = data_dir
        self.road_network_path = os.path.join(data_dir, "road_network.json")
        self.nodes = {}
        self.base_graph = nx.Graph()
        self.load_network()

    def load_network(self):
        if not os.path.exists(self.road_network_path):
            return
            
        with open(self.road_network_path, "r") as f:
            network = json.load(f)
            
        for node in network["nodes"]:
            node_id = node["id"]
            self.nodes[node_id] = node
            self.base_graph.add_node(node_id, **node)
            
        for edge in network["edges"]:
            self.base_graph.add_edge(
                edge["from_node"], 
                edge["to_node"], 
                weight=edge["distance_km"]
            )

    def get_route(
        self,
        start_id: str,
        end_id: str,
        vehicle_name: str,
        road_accessibility: Dict[str, float],
        blocked_nodes: List[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Computes the route between start and end node.
        If Truck: Computes shortest path on the road network, avoiding blocked nodes and roads.
        If Air/Water: Direct path (Haversine).
        """
        blocked_nodes = blocked_nodes or []
        
        # Verify node existence
        if start_id not in self.nodes or end_id not in self.nodes:
            return None
            
        start_node = self.nodes[start_id]
        end_node = self.nodes[end_id]
        
        # Direct route calculation
        direct_dist = haversine_distance(
            start_node["latitude"], start_node["longitude"],
            end_node["latitude"], end_node["longitude"]
        )
        
        if vehicle_name != "Truck":
            # Direct path
            coords = [
                (start_node["latitude"], start_node["longitude"]),
                (end_node["latitude"], end_node["longitude"])
            ]
            return {
                "distance_km": direct_dist,
                "path_nodes": [start_id, end_id],
                "path_coordinates": coords
            }
            
        # Truck routing (NetworkX path search)
        # Copy the base graph to prune nodes dynamically
        g = self.base_graph.copy()
        
        # Remove blocked nodes or nodes with bad accessibility
        # Let's say if accessibility is <= 0.2, the node is blocked for truck traffic.
        nodes_to_remove = []
        for n in g.nodes:
            # Do not block the start or end nodes unless they are in the blocked scenario list
            if n in [start_id, end_id]:
                if n in blocked_nodes:
                    nodes_to_remove.append(n)
                continue
                
            # If road accessibility is <= 0.2 or blocked by scenario
            acc = road_accessibility.get(n, 1.0)
            if acc <= 0.2 or n in blocked_nodes:
                nodes_to_remove.append(n)
                
        for n in nodes_to_remove:
            g.remove_node(n)
            
        # Run shortest path Dijkstra
        try:
            path = nx.shortest_path(g, source=start_id, target=end_id, weight='weight')
            distance = nx.shortest_path_length(g, source=start_id, target=end_id, weight='weight')
            
            coords = [(self.nodes[node_id]["latitude"], self.nodes[node_id]["longitude"]) for node_id in path]
            return {
                "distance_km": round(distance, 2),
                "path_nodes": path,
                "path_coordinates": coords
            }
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            # No road network path available for the Truck
            return None
