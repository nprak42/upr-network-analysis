import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import json
import pickle
from pathlib import Path
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
        --teal: #2c7a8a;
        --teal-light: #f0f8fa;
        --teal-accent: #3d9aad;
        --gray: #4a4a4a;
        --gray-light: #7a7a7a;
        --gray-lighter: #e5e5e5;
        --text: #1a1a1a;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Match your font and spacing */
    .stApp {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
        background-color: #fafafa;
    }

    /* Country selector styling */
    .stSelectbox > div > div {
        background-color: white;
        border: 2px solid #d0d0d0;
        border-radius: 8px;
        font-size: 1.05rem;
    }

    .stSelectbox label {
        font-weight: 600;
        color: #1a1a1a;
        font-size: 1rem;
    }

    /* Metric cards */
    .metric-card {
        background: white;
        border: 1px solid #e5e5e5;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        height: 100%;
    }

    .metric-card h3 {
        font-size: 1.1rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        color: #1a1a1a;
        margin-bottom: 15px;
        padding-bottom: 12px;
        border-bottom: 2px solid #2c7a8a;
    }

    /* Fix metric grid alignment */
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 12px;
    }

    .metric-item {
        background: #f0f8fa;
        border: 1px solid #c5e3ea;
        padding: 14px;
        border-radius: 6px;
        text-align: center;
    }

    .metric-value {
        font-size: 1.4rem;
        font-weight: 700;
        color: #1a1a1a;
    }

    .metric-label {
        color: #4a4a4a;
        font-size: 0.75rem;
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
        padding: 10px 12px;
        margin-bottom: 6px;
        background: #f0f8fa;
        border: 1px solid #c5e3ea;
        border-radius: 6px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 10px;
    }

    .rank-badge {
        background: #2c7a8a;
        color: white;
        width: 24px;
        height: 24px;
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 0.75rem;
        flex-shrink: 0;
    }

    .org-name {
        flex: 1;
        font-weight: 600;
        color: #1a1a1a;
        font-size: 0.85rem;
    }

    .org-value {
        color: #2c7a8a;
        font-weight: 700;
        font-family: 'Monaco', 'Courier New', monospace;
        font-size: 0.75rem;
        flex-shrink: 0;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        border-bottom: 1px solid #e5e5e5;
    }

    .stTabs [data-baseweb="tab"] {
        padding: 8px 14px;
        color: #7a7a7a;
        font-weight: 600;
        border-bottom: 2px solid transparent;
        font-size: 0.85rem;
    }

    .stTabs [aria-selected="true"] {
        color: #2c7a8a;
        border-bottom-color: #2c7a8a;
    }

    /* Description text */
    .description-text {
        color: #4a4a4a;
        font-size: 0.95rem;
        line-height: 1.6;
        margin-bottom: 25px;
    }

    /* Compact metrics column */
    .metrics-column {
        max-height: 900px;
        overflow-y: auto;
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
        # Changed from _network to _graph
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

# Load network visualization HTML
@st.cache_data
def load_network_html(country):
    """Load pre-generated pyvis HTML visualization"""
    country_code = country.replace(" ", "_")
    html_path = Path(f"network_visualizations/{country_code}_network.html")
    
    if not html_path.exists():
        return None
    
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    return html_content

# Display metric grid using Streamlit columns
def display_metric_grid(metrics_dict):
    """Display metrics in a 2x2 grid with Streamlit native components"""
    items = list(metrics_dict.items())
    
    # Display in 2x2 grid
    for i in range(0, len(items), 2):
        col1, col2 = st.columns(2)
        
        # First metric
        if i < len(items):
            label, value = items[i]
            with col1:
                if isinstance(value, float):
                    formatted_value = f"{value:.3f}" if value < 10 else f"{value:.1f}"
                else:
                    formatted_value = str(value)
                
                st.markdown(f"""
                <div style="background: #f0f8fa; border: 1px solid #c5e3ea; padding: 14px;
                            border-radius: 6px; text-align: center;">
                    <div style="font-size: 1.4rem; font-weight: 700; color: #1a1a1a;">
                        {formatted_value}
                    </div>
                    <div style="color: #4a4a4a; font-size: 0.75rem; margin-top: 5px;
                                text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600;">
                        {label}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        # Second metric
        if i + 1 < len(items):
            label, value = items[i + 1]
            with col2:
                if isinstance(value, float):
                    formatted_value = f"{value:.3f}" if value < 10 else f"{value:.1f}"
                else:
                    formatted_value = str(value)
                
                st.markdown(f"""
                <div style="background: #f0f8fa; border: 1px solid #c5e3ea; padding: 14px;
                            border-radius: 6px; text-align: center;">
                    <div style="font-size: 1.4rem; font-weight: 700; color: #1a1a1a;">
                        {formatted_value}
                    </div>
                    <div style="color: #4a4a4a; font-size: 0.75rem; margin-top: 5px;
                                text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600;">
                        {label}
                    </div>
                </div>
                """, unsafe_allow_html=True)

# Display top organizations list
def display_top_list(items, label_suffix=""):
    """Display ranked list of organizations"""
    for i, (name, value) in enumerate(items[:5], 1):
        formatted_value = f"{value:.3f}"
        
        st.markdown(f"""
        <div style="padding: 10px 12px; margin-bottom: 6px; background: #f0f8fa;
                    border: 1px solid #c5e3ea; border-radius: 6px; display: flex;
                    justify-content: space-between; align-items: center; gap: 10px;">
            <span style="background: #2c7a8a; color: white; width: 24px; height: 24px;
                         border-radius: 50%; display: inline-flex; align-items: center;
                         justify-content: center; font-weight: 700; font-size: 0.75rem;">
                {i}
            </span>
            <span style="flex: 1; font-weight: 600; color: #1a1a1a; font-size: 0.85rem;">
                {name}
            </span>
            <span style="color: #2c7a8a; font-weight: 700;
                         font-family: 'Monaco', 'Courier New', monospace; font-size: 0.75rem;">
                {formatted_value}
            </span>
        </div>
        """, unsafe_allow_html=True)

# Main app
def main():
    # Header
    st.markdown("""
    <div style='background: linear-gradient(135deg, rgba(44, 122, 138, 0.08) 0%, rgba(44, 122, 138, 0.03) 100%);
                padding: 50px 0; margin: -5rem -5rem 2rem -5rem; border-bottom: 1px solid #e5e5e5;'>
        <div style='max-width: 1600px; margin: 0 auto; padding: 0 40px;'>
            <h1 style='font-size: 2.5rem; font-weight: 800; letter-spacing: -0.03em; margin-bottom: 10px; color: #1a1a1a;'>
                UPR Network Analysis
            </h1>
            <p style='font-size: 1.05rem; color: #4a4a4a;'>
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

    # Description and selector
    st.markdown("""
    <div class="description-text">
        This interactive tool visualizes collaboration networks between civil society organizations (CSOs)
        submitting stakeholder reports to the United Nations Universal Periodic Review (UPR).
        Each network represents organizations that have jointly submitted reports for a specific country's review,
        revealing patterns of cooperation and key organizational actors in the human rights monitoring ecosystem.
    </div>
    """, unsafe_allow_html=True)

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
        html_viz = load_network_html(selected_country)
        metrics = load_metrics(selected_country)
    
    if html_viz is None:
        st.error(f"Network data not found for {selected_country}")
        return
    
    # Display country name
    st.markdown(f"""
    <h2 style='font-size: 1.8rem; font-weight: 700; margin: 25px 0 8px 0; color: #1a1a1a;'>
        {selected_country}
    </h2>
    <p style='font-size: 0.95rem; color: #4a4a4a; margin-bottom: 25px;'>
        Civil Society Organization Collaboration Network
    </p>
    """, unsafe_allow_html=True)

    # Main layout: Visualization + Metrics
    viz_col, metrics_col = st.columns([2, 1], gap="large")

    # Left: Visualization
    with viz_col:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        if html_viz:
            # Embed the pyvis HTML
            components.html(html_viz, height=850, scrolling=False)
        else:
            st.info("Network visualization unavailable")
        st.markdown('</div>', unsafe_allow_html=True)

    # Right: Metrics
    with metrics_col:
        if metrics:
            # Network Overview
            st.markdown('<h3 style="font-size: 1.1rem; font-weight: 800; color: #1a1a1a; margin-bottom: 15px; padding-bottom: 12px; border-bottom: 2px solid #2c7a8a;">Network Overview</h3>', unsafe_allow_html=True)
            display_metric_grid({
                'Organizations': metrics['num_nodes'],
                'Collaborations': metrics['num_edges'],
                'Density': metrics['density'],
                'Transitivity': metrics['transitivity']
            })

            st.markdown("<br>", unsafe_allow_html=True)

            # Structure
            st.markdown('<h3 style="font-size: 1.1rem; font-weight: 800; color: #1a1a1a; margin-bottom: 15px; padding-bottom: 12px; border-bottom: 2px solid #2c7a8a;">Structure</h3>', unsafe_allow_html=True)
            structure_metrics = {
                'Components': metrics['num_components'],
                'Triangles': metrics['num_triangles']
            }
            if metrics.get('diameter'):
                structure_metrics['Diameter'] = metrics['diameter']
                structure_metrics['Avg Path Length'] = metrics['avg_path_length']
            display_metric_grid(structure_metrics)

            st.markdown("<br>", unsafe_allow_html=True)

            # Key Organizations
            st.markdown('<h3 style="font-size: 1.1rem; font-weight: 800; color: #1a1a1a; margin-bottom: 15px; padding-bottom: 12px; border-bottom: 2px solid #2c7a8a;">Key Organizations</h3>', unsafe_allow_html=True)

            tab1, tab2, tab3 = st.tabs(["Degree", "Betweenness", "Brokers"])

            with tab1:
                display_top_list(metrics['top_degree_centrality'])

            with tab2:
                display_top_list(metrics['top_betweenness_centrality'])

            with tab3:
                display_top_list(metrics['top_brokers'])
                st.markdown('<p style="font-size: 0.8rem; color: #7a7a7a; margin-top: 10px; font-style: italic;">Lower constraint values indicate better brokerage positions</p>', unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Degree Distribution
            st.markdown('<h3 style="font-size: 1.1rem; font-weight: 800; color: #1a1a1a; margin-bottom: 15px; padding-bottom: 12px; border-bottom: 2px solid #2c7a8a;">Degree Distribution</h3>', unsafe_allow_html=True)
            display_metric_grid({
                'Mean': metrics['degree_distribution']['mean'],
                'Median': metrics['degree_distribution']['median'],
                'Maximum': metrics['degree_distribution']['max'],
                'Minimum': metrics['degree_distribution']['min']
            })

        else:
            st.info("Metrics not available for this country")

if __name__ == "__main__":
    main()