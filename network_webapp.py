"""
Simple Flask webapp for viewing and analyzing UPR country networks.

Run with: python network_webapp.py
Then visit: http://localhost:5000
"""

from flask import Flask, render_template, jsonify, send_from_directory
import os
import json
import glob

app = Flask(__name__)

# Configure paths
VISUALIZATIONS_FOLDER = 'network_visualizations'
METRICS_FOLDER = 'network_metrics'


def get_available_countries():
    """Get list of countries with available network data."""
    countries = []
    
    if os.path.exists(VISUALIZATIONS_FOLDER):
        html_files = glob.glob(os.path.join(VISUALIZATIONS_FOLDER, "*_network.html"))
        countries = [os.path.basename(f).replace("_network.html", "") for f in html_files]
    
    return sorted(countries)


def load_metrics(country_name):
    """Load metrics for a specific country."""
    metrics_path = os.path.join(METRICS_FOLDER, f"{country_name}_metrics.json")
    
    if os.path.exists(metrics_path):
        with open(metrics_path, 'r') as f:
            return json.load(f)
    
    return None


@app.route('/')
def index():
    """Home page listing all available countries."""
    countries = get_available_countries()
    return render_template('index.html', countries=countries)


@app.route('/network/<country_name>')
def view_network(country_name):
    """View network visualization for a specific country."""
    countries = get_available_countries()
    
    if country_name not in countries:
        return "Country not found", 404
    
    metrics = load_metrics(country_name)
    
    return render_template('network.html', 
                         country=country_name, 
                         metrics=metrics,
                         all_countries=countries)


@app.route('/api/countries')
def api_countries():
    """API endpoint to get list of countries."""
    return jsonify(get_available_countries())


@app.route('/api/metrics/<country_name>')
def api_metrics(country_name):
    """API endpoint to get metrics for a country."""
    metrics = load_metrics(country_name)
    
    if metrics:
        return jsonify(metrics)
    else:
        return jsonify({"error": "Metrics not found"}), 404


@app.route('/visualizations/<path:filename>')
def serve_visualization(filename):
    """Serve network visualization HTML files."""
    return send_from_directory(VISUALIZATIONS_FOLDER, filename)


if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    print("\n" + "="*60)
    print("UPR Network Analysis Webapp")
    print("="*60)
    print("\nStarting server...")
    print("Visit: http://localhost:5000")
    print("\nPress Ctrl+C to stop the server")
    print("="*60 + "\n")
    
    app.run(debug=True, port=5000)