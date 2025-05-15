import folium
from folium.plugins import HeatMap
import matplotlib.pyplot as plt
import pandas as pd
import plotly.graph_objs as go
import plotly.io as pio
import base64
from io import BytesIO
import numpy as np

# Load age and sex data from the CSV file
age_sex_data = pd.read_csv('age_sex_population.csv')

# Function to convert DataFrame to HTML table
def create_age_sex_population_table():
    table_html = age_sex_data.to_html(
        index=False, 
        border=1, 
        justify='center',
        classes="wide-table"
    )
    return table_html

# Load data on each race's populations from the CSV file
county_race_data = pd.read_csv("county_population_data.csv")

# Load city coordinates and population data from the external CSV file
city_data = pd.read_csv('city_population_data_og.csv')

# Convert city data into two dictionaries: one for coordinates and one for population
city_coordinates = {row['City']: [row['Latitude'], row['Longitude']] for index, row in city_data.iterrows()}
population_data = {row['City']: row['Population'] for index, row in city_data.iterrows()}

# Function to create an HTML table from the population data
def create_population_table():
    # Convert the DataFrame to an HTML table with a specific class for styling
    table_html = county_race_data.to_html(index=False, border=1, justify='center', classes="full-width-table")
    return table_html

# Function to create a pie chart representing the racial distribution of Rhode
# Island's population data
def create_population_pie_chart():
    labels = ['White', 'Black', 'Native', 'Asian', 'Pacific Islander', 'Two or more', 'Other alone']
    sizes = [71.3, 5.7, 0.7, 3.6, 0.0, 9.3, 9.4]
    colors = ['#ff9999','#66b3ff','#99ff99','#ffcc99','#c2c2f0','#ffb3e6', '#ffd700']

    with plt.ioff():
        # Adjust the figure size
        fig, ax = plt.subplots(figsize=(12, 8))  # Larger size for more prominence

        # Create the pie chart
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors, wedgeprops={'edgecolor': 'black'},
               textprops={'fontsize': 18})  # Increase font size for visibility

        ax.axis("equal")  # Keep proportions equal
        plt.tight_layout()  # Reduce extra whitespace

        buf = BytesIO()
        plt.savefig(buf, format="png", bbox_inches='tight')  # Save without excessive borders
        plt.close(fig)
        buf.seek(0)
        image = base64.b64encode(buf.read()).decode('utf-8')

        # Center the image with a responsive size
        img_html = f'<img src="data:image/png;base64,{image}" style="width: 100%; height: auto; max-width: 1200px; margin: 0 auto;">'

        return img_html

def create_age_pie_chart():
    age_labels = age_sex_data.columns[1:]
    total_by_age = age_sex_data[age_labels].sum()

    with plt.ioff():
        fig, ax = plt.subplots(figsize=(12, 8))
        ax.pie(total_by_age, labels=age_labels, autopct='%1.1f%%', startangle=90, 
               colors=plt.cm.Pastel1(np.linspace(0, 1, len(age_labels))), textprops={'fontsize': 20})
        ax.axis("equal")
        plt.tight_layout()

        buf = BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        image = base64.b64encode(buf.read()).decode('utf-8')
        return f'<img src="data:image/png;base64,{image}" style="width: 100%; height: auto; max-width: 1200px; margin: 0 auto;">'
    
def create_sex_pie_charts():
    sizes = [
        age_sex_data.loc[age_sex_data['Sex'] == 'Male', '0-9':'80+'].sum().sum(),
        age_sex_data.loc[age_sex_data['Sex'] == 'Female', '0-9':'80+'].sum().sum()
    ]
    labels = ['Male', 'Female']
    colors = ['#66b3ff', '#ff9999']

    with plt.ioff():
        fig, ax = plt.subplots(figsize=(12, 8))
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors, textprops={'fontsize': 20})
        ax.set_title("Population by Sex", fontsize=22)
        ax.axis("equal")
        plt.tight_layout()

        buf = BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        image = base64.b64encode(buf.read()).decode('utf-8')
        return f'<img src="data:image/png;base64,{image}" style="width: 100%; height: auto; max-width: 1200px; margin: 0 auto;">'

def create_hispanic_population_pie_chart():
    labels = ['Hispanic or Latino', 'Non Hispanic or Latino']
    sizes = [16.6, 83.4]
    colors = ['#c2c2f0', '#8fbc8f']

    with plt.ioff():
        fig, ax = plt.subplots(figsize=(12, 8))
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors, 
               wedgeprops={'edgecolor': 'black'}, textprops={'fontsize': 20})
        ax.axis("equal")
        plt.tight_layout()

        buf = BytesIO()
        plt.savefig(buf, format="png", bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        image = base64.b64encode(buf.read()).decode('utf-8')
        return f'<img src="data:image/png;base64,{image}" style="width: 100%; height: auto; max-width: 1200px; margin: 0 auto;">'


# Create Folium Map centered on Rhode Island
rhode_island_coordinates = [41.5801, -71.4774]
map_rhode_island = folium.Map(location=rhode_island_coordinates, zoom_start=10)

heat_data = []
for city, coord in city_coordinates.items():
    # Get the population for the city
    population = population_data.get(city)
    
    if population is None:
        print(f"Population data missing for {city}, skipping...")
        continue

    # Use population as the intensity value for the heat map
    heat_data.append([coord[0], coord[1], population])

# Add heatmap to the Folium map
HeatMap(heat_data, radius=55, blur=15, max_zoom=13).add_to(map_rhode_island)

# Add layer control
folium.LayerControl().add_to(map_rhode_island)

# Generating the pie chart html
race_population_pie_chart_html = create_population_pie_chart()

# Create the main HTML structure with side-by-side layout (table/graphs on left, map on right)
html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Rhode Island County Population Data</title>
    <style>
        body {{
            font-family: 'Roboto', Arial, sans-serif;
            margin: 0;
            padding: 0;
            display: flex;
            height: 100vh;
            background-color: #0d1b2a; /* Dark navy blue */
            color: #ffffff; /* White text for readability */
        }}
        .left-side {{
            flex: 1;
            padding: 20px;
            height: 100vh;
            overflow-y: auto;
            background-color: #1b263b; /* Medium blue for left panel */
            box-shadow: inset 0 0 10px rgba(0, 0, 0, 0.5);
        }}
        .right-side {{
            flex: 1;
            height: 100vh;
            padding: 20px;
            background-color: #162c49; /* Slightly lighter blue for the right panel */
            border-left: 3px solid #415a77; /* Muted blue-gray border */
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
        h1, h2 {{
            color: #ffffff; /* Keep headings white */
            margin-bottom: 10px;
        }}
        .full-width-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background-color: #1b263b; /* Medium blue for table background */
            border: 1px solid #415a77; /* Blue-gray border */
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.5);
        }}
        th, td {{
            padding: 10px;
            border: 1px solid #415a77;
            text-align: center;
            font-size: 14px;
            vertical-align: middle;
            color: #ffffff; /* White text in table */
        }}
        th {{
            background-color: #415a77; /* Blue-gray header */
            font-weight: bold;
        }}
        td {{
            background-color: #1b263b; /* Medium blue for table cells */
        }}
        div {{
            margin: 15px 0; /* Space between charts and tables */
        }}
    </style>
</head>
<body>

    <!-- Left Side: Table and Graphs -->
    <div class="left-side">
        <h1>Population Data</h1>

        <!-- Race Data Table by County -->
        <h2>Race Population by County</h2>
        {create_population_table()}

        <!-- Race Percentages Pie Chart -->
        <h2>Race Proportions</h2>
        <div style="margin-top: 0px">
            {create_population_pie_chart()}
            {create_hispanic_population_pie_chart()}
        </div>

        <!-- Age and Sex Population Table -->
        <h2>Rhode Island Population Data by Age and Sex</h2>
        <div class="wide-table">
            {create_age_sex_population_table()}
        </div>

        <!-- Age and Sex Pie Charts -->
        <h2>Age and Sex Proportions</h2>
        <div style="margin-top: 0px">
            {create_age_pie_chart()}
            {create_sex_pie_charts()}
        </div>
    </div>

    <!-- Right Side: Map -->
    <div class="right-side">
        <h2>Population Density Map</h2>
        <div id="map-container">
            {map_rhode_island.get_root().render()}
        </div>
    </div>

</body>
</html>
"""

# Save the full HTML to a file
with open("rhode_island_cancer_map_v12.1.html", "w") as f:
    f.write(html_content)

print("Cancer map with data table, interactive graph, and popups created and saved as 'rhode_island_cancer_map_v12.1.html'")