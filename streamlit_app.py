import streamlit as st
import pandas as pd
import json
import pickle
from pathlib import Path
import plotly.graph_objects as go
import networkx as nx

# Page config
st.set_page_config(
    page_title="UPR Network Analysis",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS to match your design
st.markdown("""
<style>
    :root {
        --teal: #5eadbd;
        --teal-light: #e6f7f9;
        --gray: #6b6b6b;
        --gray-light: #a3a3a3;
        --gray-lighter: #e5e5e5;
        --text: #2a2a2a;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Match your font and spacing */
    .stApp {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
    }
    
    /* Country selector styling */
    .stSelectbox > div > div {
        background-color: white;
        border: 2px solid #e5e5e5;
        border-radius: 8px;
    }
    
    /* Metric cards */
    .metric-card {
        background: white;
        border: 1px solid #e5e5e5;
        border-radius: 8px;
        padding: 25px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        height: 100%;
    }
    
    .metric-card h3 {
        font-size: 1.3rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        color: #2a2a2a;
        margin-bottom: 20px;
        padding-bottom: 15px;
        border-bottom: 2px solid #5eadbd;
    }
    
    /* Fix metric grid alignment */
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 15px;
    }
    
    .metric-item {
        background: #e6f7f9;
        border: 1px solid #e5e5e5;
        padding: 18px;
        border-radius: 6px;
        text-align: center;
    }
    
    .metric-value {
        font-size: 1.6rem;
        font-weight: 700;
        color: #2a2a2a;
    }
    
    .metric-label {
        color: #6b6b6b;
        font-size: 0.85rem;
        margin-top: 5px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 600;
    }
    
    /* Top list styling */
    .top-list {
        list-style: none;
        padding: 0;
    }
    
    .top-list-item {
        padding: 15px;
        margin-bottom: 10px;
        background: #e6f7f9;
        border: 1px solid #e5e5e5;
        border-radius: 6px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 12px;
    }
    
    .rank-badge {
        background: #5eadbd;
        color: white;
        width: 28px;
        height: 28px;
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 0.85rem;
    }
    
    .org-name {
        flex: 1;
        font-weight: 600;
        color: #2a2a2a;
    }
    
    .org-value {
        color: #5eadbd;
        font-weight: 700;
        font-family: 'Monaco', 'Courier New', monospace;
        font-size: 0.85rem;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 15px;
        border-bottom: 1px solid #e5e5e5;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 12px 20px;
        color: #6b6b6b;
        font-weight: 600;
        border-bottom: 2px solid transparent;
    }
    
    .stTabs [aria-selected="true"] {
        color: #5eadbd;
        border-bottom-color: #5eadbd;
    }
</style>
""", unsafe_allow_html=True)

# Load available countries
@st.cache_data
def load_countries():
    """Load list of available countries from graph_objects folder"""
    graph_dir = Path("graph_objects")
    if not graph_dir.exists():
        return []
    
    countries = []
    for file in graph_dir.glob("*.pkl"):
        country = file.stem.replace("_graph", "").replace("_", " ")
        countries.append(country)
    
    return sorted(countries)

# Load network data
@st.cache_data
def load_network(country):
    """Load network graph from pickle file"""
    country_code = country.replace(" ", "_")
    graph_path = Path(f"graph_objects/{country_code}_graph.pkl")
    
    if not graph_path.exists():
        return None
    
    with open(graph_path, 'rb') as f:
        G = pickle.load(f)
    
    return G

# Load metrics
@st.cache_data
def load_metrics(country):
    """Load network metrics from JSON file"""
    country_code = country.replace(" ", "_")
    metrics_path = Path(f"network_metrics/{country_code}_metrics.json")
    
    if not metrics_path.exists():
        return None
    
    with open(metrics_path, 'r') as f:
        metrics = json.load(f)
    
    return metrics

# Create network visualization
def create_network_visualization(G):
    """Create interactive network visualization using Plotly"""
    if G is None or len(G.nodes()) == 0:
        return None
    
    # Use spring layout
    pos = nx.spring_layout(G, k=0.5, iterations=50, seed=42)
    
    # Create edge traces
    edge_trace = go.Scatter(
        x=[],
        y=[],
        line=dict(width=0.5, color='#e5e5e5'),
        hoverinfo='none',
        mode='lines'
    )
    
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_trace['x'] += tuple([x0, x1, None])
        edge_trace['y'] += tuple([y0, y1, None])
    
    # Create node traces
    node_trace = go.Scatter(
        x=[],
        y=[],
        text=[],
        mode='markers',
        hoverinfo='text',
        marker=dict(
            showscale=True,
            colorscale='Teal',
            size=10,
            color=[],
            colorbar=dict(
                thickness=15,
                title='Degree',
                xanchor='left',
                titleside='right'
            ),
            line=dict(width=1, color='white')
        )
    )
    
    for node in G.nodes():
        x, y = pos[node]
        node_trace['x'] += tuple([x])
        node_trace['y'] += tuple([y])
        node_trace['text'] += tuple([f"{node}<br>Degree: {G.degree(node)}"])
        node_trace['marker']['color'] += tuple([G.degree(node)])
    
    # Create figure
    fig = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            showlegend=False,
            hovermode='closest',
            margin=dict(b=0, l=0, r=0, t=0),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='white',
            height=800
        )
    )
    
    return fig

# Display metric grid
def display_metric_grid(metrics_dict):
    """Display metrics in a 2x2 grid with consistent sizing"""
    html = '<div class="metric-grid">'
    
    for label, value in metrics_dict.items():
        if isinstance(value, float):
            formatted_value = f"{value:.3f}" if value < 10 else f"{value:.1f}"
        else:
            formatted_value = str(value)
        
        html += f'''
        <div class="metric-item">
            <div class="metric-value">{formatted_value}</div>
            <div class="metric-label">{label}</div>
        </div>
        '''
    
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

# Display top organizations list
def display_top_list(items, label_suffix=""):
    """Display ranked list of organizations"""
    html = '<div class="top-list">'
    
    for i, (name, value) in enumerate(items[:5], 1):
        formatted_value = f"{value:.3f}"
        html += f'''
        <div class="top-list-item">
            <span class="rank-badge">{i}</span>
            <span class="org-name">{name}</span>
            <span class="org-value">{formatted_value}</span>
        </div>
        '''
    
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

# Main app
def main():
    # Header
    st.markdown("""
    <div style='background: linear-gradient(135deg, rgba(94, 173, 189, 0.08) 0%, rgba(94, 173, 189, 0.03) 100%); 
                padding: 50px 0; margin: -5rem -5rem 2rem -5rem; border-bottom: 1px solid #e5e5e5;'>
        <div style='max-width: 1600px; margin: 0 auto; padding: 0 40px;'>
            <h1 style='font-size: 2.5rem; font-weight: 800; letter-spacing: -0.03em; margin-bottom: 10px; color: #2a2a2a;'>
                UPR Network Analysis
            </h1>
            <p style='font-size: 1.05rem; color: #6b6b6b;'>
                Explore civil society organization collaboration networks in UN Human Rights Council submissions
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Country selector
    countries = load_countries()
    
    if not countries:
        st.error("No network data found. Please ensure graph_objects/ folder contains .pkl files.")
        return
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        selected_country = st.selectbox(
            "Select a country to explore its CSO network",
            countries,
            index=0
        )
    
    if not selected_country:
        st.info("Please select a country to view its network.")
        return
    
    # Load data
    with st.spinner(f"Loading network for {selected_country}..."):
        G = load_network(selected_country)
        metrics = load_metrics(selected_country)
    
    if G is None:
        st.error(f"Network data not found for {selected_country}")
        return
    
    # Display country name
    st.markdown(f"""
    <h2 style='font-size: 2rem; font-weight: 700; margin: 30px 0 10px 0; color: #2a2a2a;'>
        {selected_country}
    </h2>
    <p style='font-size: 1.05rem; color: #6b6b6b; margin-bottom: 30px;'>
        Civil Society Organization Collaboration Network
    </p>
    """, unsafe_allow_html=True)
    
    # Main layout: Visualization + Metrics
    viz_col, metrics_col = st.columns([2, 1], gap="large")
    
    # Left: Visualization
    with viz_col:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        fig = create_network_visualization(G)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Network visualization unavailable")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Right: Metrics
    with metrics_col:
        if metrics:
            # Network Overview
            st.markdown('<div class="metric-card"><h3>Network Overview</h3>', unsafe_allow_html=True)
            display_metric_grid({
                'Organizations': metrics['num_nodes'],
                'Collaborations': metrics['num_edges'],
                'Density': metrics['density'],
                'Transitivity': metrics['transitivity']
            })
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Structure
            st.markdown('<div class="metric-card"><h3>Structure</h3>', unsafe_allow_html=True)
            structure_metrics = {
                'Components': metrics['num_components'],
                'Triangles': metrics['num_triangles']
            }
            if metrics.get('diameter'):
                structure_metrics['Diameter'] = metrics['diameter']
                structure_metrics['Avg Path Length'] = metrics['avg_path_length']
            display_metric_grid(structure_metrics)
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Key Organizations
            st.markdown('<div class="metric-card"><h3>Key Organizations</h3>', unsafe_allow_html=True)
            
            tab1, tab2, tab3 = st.tabs(["Degree", "Betweenness", "Brokers"])
            
            with tab1:
                display_top_list(metrics['top_degree_centrality'])
            
            with tab2:
                display_top_list(metrics['top_betweenness_centrality'])
            
            with tab3:
                display_top_list(metrics['top_brokers'])
                st.markdown('<p style="font-size: 0.9rem; color: #a3a3a3; margin-top: 15px; font-style: italic;">Lower constraint values indicate better brokerage positions</p>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Degree Distribution
            st.markdown('<div class="metric-card"><h3>Degree Distribution</h3>', unsafe_allow_html=True)
            display_metric_grid({
                'Mean': metrics['degree_distribution']['mean'],
                'Median': metrics['degree_distribution']['median'],
                'Maximum': metrics['degree_distribution']['max'],
                'Minimum': metrics['degree_distribution']['min']
            })
            st.markdown('</div>', unsafe_allow_html=True)
        
        else:
            st.info("Metrics not available for this country")

if __name__ == "__main__":
    main()