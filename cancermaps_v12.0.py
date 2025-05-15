import folium
from folium.plugins import HeatMap
import matplotlib.pyplot as plt
import pandas as pd
import plotly.graph_objs as go
import plotly.io as pio
import base64
from io import BytesIO

# Load cancer data from the CSV file (dynamically adjust to cancer types)
df = pd.read_csv('no_pop_cancer_data.csv')

# Load city coordinates and population data from the external CSV file

import os

# Dynamically read the uploaded file or use default data
uploaded_file_path = "city_population_data.csv"
if os.path.exists(uploaded_file_path):
    city_data = pd.read_csv(uploaded_file_path)
else:
    raise FileNotFoundError(f"Expected file {uploaded_file_path} not found.")

# Convert city data into two dictionaries: one for coordinates and one for population
city_coordinates = {row['City']: [row['Latitude'], row['Longitude']] for index, row in city_data.iterrows()}
population_data = {row['City']: row['Population'] for index, row in city_data.iterrows()}

# Extract years from the CSV column headers (assuming they are numeric year columns)
years = [col for col in df.columns if col.isdigit()]

# Extract cancer types dynamically by excluding the 'Location' and year columns
cancer_types = [col for col in df.columns if col not in ['Location'] + years]

# Function to create a graph representing the total number of cancers per year
def create_total_cancer_chart(location_name):
    location_data = df[df['Location'] == location_name]
    if location_data.empty:
        print(f"No data available for {location_name}. Skipping chart generation.")
        return ""  # Return an empty string if no data is available

    try:
        total_cases = location_data[years].astype(int).values.flatten()
        if len(total_cases) != len(years):
            print(f"Data length mismatch for {location_name}. Skipping chart.")
            return ""

        with plt.ioff():  # Disable interactive mode to avoid showing figures
            fig, ax = plt.subplots()
            ax.plot(years, total_cases, marker="o", color="blue")
            ax.set_title(f"Total Cancer Trend in {location_name}")
            ax.set_xlabel("Year")
            ax.set_ylabel("Number of Cases")

            buf = BytesIO()
            plt.savefig(buf, format="png")
            plt.close(fig)  # Explicitly close the figure
            buf.seek(0)
            image = base64.b64encode(buf.read()).decode('utf-8')
            img_html = f'<img src="data:image/png;base64,{image}" width="300" height="200">'
            return img_html

    except KeyError as e:
        print(f"Missing data for some years in {location_name}: {e}. Skipping chart.")
        return ""

# Function to create an interactive comparative graph showing all cities' trends together using Plotly
def create_interactive_comparative_chart():
    traces = []

    for city in city_coordinates.keys():
        location_data = df[df['Location'] == city]
        if location_data.empty:
            continue  # Skip if no data available
        
        try:
            total_cases = location_data[years].astype(int).values.flatten()
            if len(total_cases) != len(years):
                continue  # Skip if there's a data mismatch

            # Create a trace for each city
            trace = go.Scatter(
                x=years,
                y=total_cases,
                mode='lines+markers',
                name=city
            )
            traces.append(trace)

        except KeyError:
            continue  # Skip if there's a missing year for the city

    # Create layout for the plot
    layout = go.Layout(
        title='Interactive Comparative Cancer Trends Across Cities in RI',
        xaxis=dict(title='Year'),
        yaxis=dict(title='Number of Cases'),
        hovermode='closest',
        width=700,   # Set the desired width of the graph
        height=500   # Set the desired height of the graph
    )

    # Create the figure
    fig = go.Figure(data=traces, layout=layout)

    # Render the figure as an HTML div element
    interactive_chart_html = pio.to_html(fig, full_html=False)
    
    return interactive_chart_html

# Function to dynamically create an HTML table with clickable links for cancer types
def create_cancer_table(location_name):
    location_data = df[df['Location'] == location_name]
    population = population_data[location_name]
    
    # Dynamically generate links for cancer types present in the CSV file
    base_url = "https://example.com/"  # Base URL for the links (replace with actual base URL)
    
    # Generate cancer links based on cancer types found in the CSV file
    cancer_links = {cancer: f"{base_url}{cancer.lower().replace(' ', '-')}-cancer" for cancer in cancer_types}
    
    # Create table headers and rows dynamically based on cancer types with clickable links
    table_html = f"""
    <table border="1" style="width: 100%;">
        <tr><th>Cancer Type</th><th>Number of Cases</th></tr>
    """
    
    for cancer in cancer_types:
        cancer_link = cancer_links.get(cancer, '#')  # Get link, default to '#' if not found
        num_cases = int(location_data[cancer].values[0])
        table_html += f"<tr><td><a href='{cancer_link}' target='_blank'>{cancer}</a></td><td>{num_cases}</td></tr>"
    
    # Add population information
    table_html += f"<tr><td>Population</td><td>{population}</td></tr>"
    table_html += "</table>"
    
    return table_html

# Function to generate HTML table for the entire CSV data
def create_csv_table():
    return df.to_html(index=False, border=1)

# Function to add graphs into table cells
def generate_graph_table():
    num_graphs_per_row = 2  # Set how many graphs per row
    graph_html = "<table style='width:100%; border-collapse: collapse;'>"
    
    graphs = []  # Store each graph's HTML
    for city in city_coordinates.keys():
        graph_html_code = create_total_cancer_chart(city)
        if graph_html_code:
            graphs.append(graph_html_code)
    
    # Generate rows of graphs
    for i in range(0, len(graphs), num_graphs_per_row):
        graph_html += "<tr>"  # Start a new row
        row_graphs = graphs[i:i+num_graphs_per_row]  # Get the graphs for this row
        for graph in row_graphs:
            graph_html += f"<td style='border: 1px solid black; padding: 10px;'>{graph}</td>"
        graph_html += "</tr>"  # Close the row
    
    graph_html += "</table>"
    return graph_html

# Create Folium Map centered on Rhode Island
rhode_island_coordinates = [41.5801, -71.4774]
map_rhode_island = folium.Map(location=rhode_island_coordinates, zoom_start=10)

# Generate a heatmap of total cancer cases for each city, correlated with the population
heat_data = []
for city, coord in city_coordinates.items():
    location_data = df[df['Location'] == city]
    
    # Calculate the total cancer cases across the years (2015-2021)
    total_cases = location_data[years].astype(int).sum().sum()  # Sum all years
    
    # Get the population for the city
    population = population_data.get(city)
    
    if population is None:
        print(f"Population data missing for {city}, skipping...")
        continue
    
    # Calculate cases per capita (cases per 1000 people)
    cases_per_capita = (total_cases / population) * 1000
    
    # Add to heatmap data, using cases per capita as the intensity value
    heat_data.append([coord[0], coord[1], cases_per_capita])

# Add heatmap to the Folium map
HeatMap(heat_data, radius=55, blur=15, max_zoom=13).add_to(map_rhode_island)

# Add markers with popups for each city
for city, coord in city_coordinates.items():
    chart_html = create_total_cancer_chart(city)
    if chart_html:
        table_html = create_cancer_table(city)
        popup_html = f"""
        <h4>{city}</h4>
        {table_html}
        <br><br>
        {chart_html}
        """
        popup = folium.Popup(popup_html, max_width=500)
        folium.Marker(location=coord, popup=popup, icon=folium.Icon(color='blue', icon='info-sign')).add_to(map_rhode_island)

# Add layer control
folium.LayerControl().add_to(map_rhode_island)

# Create the main HTML structure with side-by-side layout (table/graphs on left, map on right)
html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Rhode Island Cancer Data Map</title>
    <style>
        body {{
            font-family: 'Roboto', Arial, sans-serif;
            margin: 0;
            padding: 0;
            display: flex;
            height: 100vh;
            background-color: #0d1b2a; /* Dark navy blue background */
            color: #ffffff; /* White text for readability */
        }}
        .left-side {{
            flex: 1;
            padding: 20px;
            overflow-y: scroll;
            height: 100vh;
            background-color: #1b263b; /* Medium blue for left panel */
            box-shadow: inset 0 0 10px rgba(0, 0, 0, 0.5);
        }}
        .right-side {{
            flex: 1;
            height: 100vh;
            padding: 20px;
            background-color: #162c49; /* Slightly lighter blue for right panel */
            border-left: 3px solid #415a77; /* Muted blue-gray border */
        }}
        h1, h2 {{
            color: #ffffff; /* Keep headings white */
            margin-bottom: 10px;
        }}
        #map-container {{
            height: 90%;
            max-width: 600px;
            max-height: 800px;
            border: 2px solid #415a77; /* Blue-gray border */
            border-radius: 8px;
            overflow: hidden;
            margin: 0 auto;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.5);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            text-align: left;
            background-color: #162c49; /* Darker blue for table */
            border: 1px solid #415a77; /* Blue-gray borders */
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.5);
        }}
        th, td {{
            padding: 10px;
            border: 1px solid #415a77;
            text-align: center;
            font-size: 0.9em;
            color: #ffffff; /* Keep table text white */
        }}
        th {{
            background-color: #415a77; /* Muted blue-gray for header */
            font-weight: bold;
        }}
        td {{
            background-color: #1b263b; /* Medium blue for table cells */
        }}
        /* Interactive chart container */
        div {{
            margin: 15px 0;
        }}
    </style>
</head>
<body>

    <!-- Left Side: Table and Graphs -->
    <div class="left-side">
        <h1>Rhode Island Cancer Data Visualization</h1>
        
        <!-- Cancer Data Table -->
        <h2>Cancer Data Table</h2>
        {create_csv_table()}

        <!-- Interactive Comparative Graph -->
        <div>
            {create_interactive_comparative_chart()}
        </div>

        <!-- Individual city graph section (organized in table cells) -->
        <h2>Individual Cancer Trends by City</h2>
        <div>
            {generate_graph_table()}
        </div>
    </div>

    <!-- Right Side: Map -->
    <div class="right-side">
        <h2>Interactive Map</h2>
        <div id="map-container">
            {map_rhode_island.get_root().render()}
        </div>
    </div>

</body>
</html>
"""

# Save the full HTML to a file
with open("rhode_island_cancer_map_v12.html", "w") as f:
    f.write(html_content)

print("Cancer map with data table, interactive graph, and popups created and saved as 'rhode_island_cancer_map_v12.html'")