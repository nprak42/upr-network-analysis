import pandas as pd
import networkx as nx
from pyvis.network import Network
import os
import pickle
import json
from collections import defaultdict


def calculate_network_metrics(G):
    """
    Calculate comprehensive network metrics for analysis.
    
    Args:
        G: NetworkX graph object
        
    Returns:
        dict: Dictionary containing various network metrics
    """
    metrics = {}
    
    # Basic metrics
    metrics['num_nodes'] = G.number_of_nodes()
    metrics['num_edges'] = G.number_of_edges()
    metrics['density'] = nx.density(G)
    
    # Only calculate if graph has nodes
    if G.number_of_nodes() > 0:
        # Centrality measures
        degree_centrality = nx.degree_centrality(G)
        betweenness_centrality = nx.betweenness_centrality(G)
        closeness_centrality = nx.closeness_centrality(G)
        eigenvector_centrality = nx.eigenvector_centrality(G, max_iter=1000)
        
        # Store top 10 for each centrality measure
        metrics['top_degree_centrality'] = sorted(
            degree_centrality.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        metrics['top_betweenness_centrality'] = sorted(
            betweenness_centrality.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        metrics['top_closeness_centrality'] = sorted(
            closeness_centrality.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        metrics['top_eigenvector_centrality'] = sorted(
            eigenvector_centrality.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        # Degree distribution
        degree_sequence = sorted([d for n, d in G.degree()], reverse=True)
        metrics['degree_distribution'] = {
            'mean': sum(degree_sequence) / len(degree_sequence),
            'max': max(degree_sequence),
            'min': min(degree_sequence),
            'median': degree_sequence[len(degree_sequence)//2]
        }
        
        # Clustering coefficient
        metrics['avg_clustering_coefficient'] = nx.average_clustering(G)
        
        # Connected components
        if nx.is_connected(G):
            metrics['num_components'] = 1
            metrics['diameter'] = nx.diameter(G)
            metrics['avg_path_length'] = nx.average_shortest_path_length(G)
        else:
            components = list(nx.connected_components(G))
            metrics['num_components'] = len(components)
            largest_cc = max(components, key=len)
            subgraph = G.subgraph(largest_cc)
            metrics['largest_component_size'] = len(largest_cc)
            metrics['diameter'] = nx.diameter(subgraph)
            metrics['avg_path_length'] = nx.average_shortest_path_length(subgraph)
        
        # Edgewise shared partners (triadic closure)
        # Count triangles
        triangles = sum(nx.triangles(G).values()) / 3
        metrics['num_triangles'] = int(triangles)
        metrics['transitivity'] = nx.transitivity(G)
        
        # Brokerage analysis - structural holes
        # Using constraint as a measure (lower constraint = more brokerage)
        constraint = nx.constraint(G)
        metrics['top_brokers'] = sorted(
            constraint.items(),
            key=lambda x: x[1]
        )[:10]  # Lower constraint = better broker
        
    return metrics


def create_network_visualization(edgelist_path, country_name, 
                                output_folder="network_visualizations1",
                                graph_objects_folder="graph_objects",
                                metrics_folder="network_metrics"):
    """
    Creates an interactive network visualization from an edgelist CSV file
    and saves the graph object and metrics for later analysis.
    
    Args:
        edgelist_path: Path to the edgelist CSV file
        country_name: Name of the country for labeling
        output_folder: Folder to save HTML visualization
        graph_objects_folder: Folder to save NetworkX graph objects
        metrics_folder: Folder to save network metrics
    """
    
    # Create output directories if they don't exist
    for folder in [output_folder, graph_objects_folder, metrics_folder]:
        if not os.path.exists(folder):
            os.makedirs(folder)
    
    # Read the edgelist
    try:
        edgelist = pd.read_csv(edgelist_path)
    except Exception as e:
        print(f"Error reading edgelist: {e}")
        return None
    
    if edgelist.empty:
        print(f"Empty edgelist for {country_name}")
        return None
    
    # Create NetworkX graph
    G = nx.Graph()
    
    # Add edges with weights
    for _, row in edgelist.iterrows():
        G.add_edge(row['Source'], row['Target'], weight=row['Weight'])
    
    # Save graph object
    graph_object_path = os.path.join(graph_objects_folder, f"{country_name}_graph.pkl")
    with open(graph_object_path, 'wb') as f:
        pickle.dump(G, f)
    print(f"Graph object saved to: {graph_object_path}")
    
    # Calculate network statistics
    print(f"\n--- Network Statistics for {country_name} ---")
    metrics = calculate_network_metrics(G)
    
    # Print key metrics
    print(f"Number of nodes: {metrics['num_nodes']}")
    print(f"Number of edges: {metrics['num_edges']}")
    print(f"Network density: {metrics['density']:.4f}")
    
    if metrics['num_nodes'] > 0:
        print(f"Average clustering coefficient: {metrics['avg_clustering_coefficient']:.4f}")
        print(f"Number of components: {metrics['num_components']}")
        print(f"Transitivity: {metrics['transitivity']:.4f}")
        print(f"Number of triangles: {metrics['num_triangles']}")
        
        print(f"\nTop 5 most connected organizations (degree centrality):")
        for node, centrality in metrics['top_degree_centrality'][:5]:
            print(f"  - {node}: {centrality:.4f}")
        
        print(f"\nTop 5 broker organizations (lowest constraint):")
        for node, constraint_val in metrics['top_brokers'][:5]:
            print(f"  - {node}: {constraint_val:.4f}")
    
    # Save metrics to JSON
    # Convert tuples to lists for JSON serialization
    metrics_json = metrics.copy()
    for key in ['top_degree_centrality', 'top_betweenness_centrality', 
                'top_closeness_centrality', 'top_eigenvector_centrality', 'top_brokers']:
        if key in metrics_json:
            metrics_json[key] = [(str(k), float(v)) for k, v in metrics_json[key]]
    
    metrics_path = os.path.join(metrics_folder, f"{country_name}_metrics.json")
    with open(metrics_path, 'w') as f:
        json.dump(metrics_json, f, indent=2)
    print(f"Metrics saved to: {metrics_path}")
    
    # Create PyVis network visualization
    net = Network(
        height="750px",
        width="100%",
        bgcolor="#ffffff",
        font_color="black",
        notebook=False
    )
    
    # Configure physics for better layout
    net.barnes_hut(
        gravity=-5000,
        central_gravity=0.3,
        spring_length=100,
        spring_strength=0.001,
        damping=0.09,
        overlap=0
    )
    
    # Add nodes with size based on degree
    degrees = dict(G.degree())
    max_degree = max(degrees.values()) if degrees else 1
    
    # Get betweenness centrality for color coding
    if G.number_of_nodes() > 0:
        betweenness = nx.betweenness_centrality(G)
        max_betweenness = max(betweenness.values()) if betweenness else 1
        # Prevent division by zero if all betweenness values are 0
        if max_betweenness == 0:
            max_betweenness = 1
    
    for node in G.nodes():
        degree = degrees[node]
        # Scale node size based on degree (min 10, max 50)
        node_size = 10 + (degree / max_degree) * 40
        
        # Color based on betweenness centrality (brokers are redder)
        if G.number_of_nodes() > 0:
            betweenness_val = betweenness[node]
            red_intensity = int(255 * (betweenness_val / max_betweenness))
            blue_intensity = int(255 * (1 - betweenness_val / max_betweenness))
            color = f'#{red_intensity:02x}66{blue_intensity:02x}'
        else:
            color = '#97c2fc'
        
        net.add_node(
            node,
            label=node,
            size=node_size,
            title=f"{node}<br>Connections: {degree}<br>Betweenness: {betweenness.get(node, 0):.4f}",
            color=color
        )
    
    # Add edges with width based on weight
    max_weight = edgelist['Weight'].max() if not edgelist.empty else 1
    
    for _, row in edgelist.iterrows():
        # Scale edge width based on weight (min 1, max 10)
        edge_width = 1 + (row['Weight'] / max_weight) * 9
        
        net.add_edge(
            row['Source'],
            row['Target'],
            value=edge_width,
            title=f"Collaborations: {row['Weight']}"
        )
    
    # Save the visualization
    output_filename = f"{country_name}_network.html"
    output_path = os.path.join(output_folder, output_filename)
    net.save_graph(output_path)
    
    print(f"\nVisualization saved to: {output_path}")
    print("-" * 60)
    
    return G, metrics


def visualize_all_countries(edgelist_folder="edgelists", 
                           output_folder="network_visualizations1",
                           graph_objects_folder="graph_objects",
                           metrics_folder="network_metrics"):
    """
    Creates visualizations for all edgelist files in the specified folder.
    
    Args:
        edgelist_folder: Folder containing edgelist CSV files
        output_folder: Folder to save visualizations
        graph_objects_folder: Folder to save graph objects
        metrics_folder: Folder to save network metrics
        
    Returns:
        dict: Dictionary mapping country names to (graph, metrics) tuples
    """
    
    if not os.path.exists(edgelist_folder):
        print(f"Edgelist folder '{edgelist_folder}' not found.")
        return {}
    
    edgelist_files = [f for f in os.listdir(edgelist_folder) if f.endswith("_js_edgelist.csv")]
    
    if not edgelist_files:
        print(f"No edgelist files found in '{edgelist_folder}'")
        return {}
    
    print(f"Found {len(edgelist_files)} edgelist file(s). Creating visualizations...\n")
    
    results = {}
    
    for filename in edgelist_files:
        country_name = filename.replace("_js_edgelist.csv", "")
        edgelist_path = os.path.join(edgelist_folder, filename)
        
        print(f"Processing {country_name}...")
        result = create_network_visualization(
            edgelist_path, 
            country_name, 
            output_folder,
            graph_objects_folder,
            metrics_folder
        )
        
        if result is not None:
            results[country_name] = result
    
    print(f"\nAll visualizations complete! Check the following folders:")
    print(f"  - Visualizations: '{output_folder}'")
    print(f"  - Graph objects: '{graph_objects_folder}'")
    print(f"  - Metrics: '{metrics_folder}'")
    
    return results


def load_saved_graph(country_name, graph_objects_folder="graph_objects"):
    """
    Load a previously saved graph object.
    
    Args:
        country_name: Name of the country
        graph_objects_folder: Folder containing saved graph objects
        
    Returns:
        NetworkX graph object or None if not found
    """
    graph_path = os.path.join(graph_objects_folder, f"{country_name}_graph.pkl")
    
    if not os.path.exists(graph_path):
        print(f"Graph file not found: {graph_path}")
        return None
    
    with open(graph_path, 'rb') as f:
        G = pickle.load(f)
    
    print(f"Loaded graph for {country_name}")
    print(f"Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}")
    
    return G


if __name__ == "__main__":
    # Process all countries and save results
    results = visualize_all_countries()
    
    # Example: Load a saved graph later
    # G = load_saved_graph("Korea")