import pandas as pd
import folium
from folium.plugins import HeatMap
import plotly.graph_objs as go
import plotly.io as pio
import os
import numpy as np
import json
import matplotlib.pyplot as plt
import base64
from io import BytesIO

import pandas as pd
import folium
from folium.plugins import HeatMap
import plotly.graph_objs as go
import plotly.io as pio
import os
import numpy as np
import json
import matplotlib.pyplot as plt
import base64
from io import BytesIO

def generate_visualization(uploads_folder="uploads"):
    """Generate visualizations based on uploaded data files"""
    try:
        # Clear any existing visualization files
        viz_files = [
            'population_map.html', 'cancer_map.html', 'race_demographics.html',
            'age_distribution.html', 'cancer_trends.html', 'cancer_distribution.html',
            'custom_cancer_map_v12_4.html'
        ]
        
        for file in viz_files:
            if os.path.exists(file):
                try:
                    os.remove(file)
                except Exception as e:
                    print(f"Error removing existing visualization file {file}: {e}")

        # Dictionary to track which files exist and which visualizations to create
        uploaded_files = {
            'cancer': os.path.exists(os.path.join(uploads_folder, 'cancer_data.csv')),
            'countyRace': os.path.exists(os.path.join(uploads_folder, 'countyRace_data.csv')),
            'ageSex': os.path.exists(os.path.join(uploads_folder, 'ageSex_data.csv'))
        }
        
        # Check if any files were uploaded
        if not any(uploaded_files.values()):
            print("No data files were uploaded. Cannot generate visualizations.")
            # Still create the HTML with a message
            generate_html_output(None, None, [], {})
            return True

        # Dictionary to track successfully created visualizations
        created_visualizations = {
            'population_map': False,
            'cancer_map': False,
            'race_demographics': False,
            'age_distribution': False,
            'cancer_trends': False,
            'cancer_distribution': False
        }

        population_map = None
        cancer_map = None
        extra_charts = []

        # Process census data to get city, state, lat, lng, population
        census_data_path = os.path.join(uploads_folder, 'processed_census_data.csv')
        if not os.path.exists(census_data_path):
            # Try project root directory if not found in uploads
            census_data_path = 'processed_census_data.csv'
            if not os.path.exists(census_data_path):
                print("Processed census data not found. Please ensure uscities.csv is processed.")
                return False

        census_data = pd.read_csv(census_data_path)

        # Only process cancer data if it exists
        if uploaded_files['cancer']:
            try:
                cancer_data = pd.read_csv(os.path.join(uploads_folder, 'cancer_data.csv'))
                
                # Identify cancer type columns (non-year columns)
                cancer_cols = [col for col in cancer_data.columns[2:] if not str(col).isdigit()]
                year_cols = [col for col in cancer_data.columns[2:] if str(col).isdigit()]
                
                # Merge cancer data with census data
                merged_data = pd.merge(
                    cancer_data,
                    census_data,
                    left_on=['City', 'State'],
                    right_on=['city', 'state_id'],
                    how='inner'
                )
                
                if not merged_data.empty:
                    # Create population heatmap
                    population_map = create_population_heatmap(merged_data)
                    created_visualizations['population_map'] = True
                    print("Population map created successfully")
                    
                    # Create cancer incidence map
                    if cancer_cols:
                        cancer_map = create_cancer_incidence_map(merged_data, cancer_cols)
                        created_visualizations['cancer_map'] = True
                        print("Cancer incidence map created successfully")
            except Exception as e:
                print(f"Error processing cancer data: {str(e)}")

        # Only process age/sex data if it exists
        if uploaded_files['ageSex']:
            try:
                age_sex_data = pd.read_csv(os.path.join(uploads_folder, 'ageSex_data.csv'))
                age_chart = create_age_distribution_chart(age_sex_data)
                extra_charts.append(age_chart)
                created_visualizations['age_distribution'] = True
                print("Age distribution chart created successfully")
            except Exception as e:
                print(f"Error creating age distribution chart: {str(e)}")

        # Only process county race data if it exists
        if uploaded_files['countyRace']:
            try:
                county_race_data = pd.read_csv(os.path.join(uploads_folder, 'countyRace_data.csv'))
                race_chart = create_race_demographics_chart(county_race_data)
                extra_charts.append(race_chart)
                created_visualizations['race_demographics'] = True
                print("Race demographics chart created successfully")
            except Exception as e:
                print(f"Error creating race demographics chart: {str(e)}")

        # Only process cancer trends if cancer data exists and year columns are present
        if uploaded_files['cancer'] and year_cols:
            try:
                trend_chart = create_trend_analysis(merged_data, year_cols)
                extra_charts.append(trend_chart)
                created_visualizations['cancer_trends'] = True
                print("Cancer trends chart created successfully")
            except Exception as e:
                print(f"Error creating cancer trends chart: {str(e)}")

        # Only process cancer distribution if cancer data exists and cancer columns are present
        if uploaded_files['cancer'] and cancer_cols:
            try:
                dist_chart = create_cancer_distribution_chart(merged_data, cancer_cols)
                extra_charts.append(dist_chart)
                created_visualizations['cancer_distribution'] = True
                print("Cancer distribution chart created successfully")
            except Exception as e:
                print(f"Error creating cancer distribution chart: {str(e)}")

        # Generate the final HTML output
        generate_html_output(population_map, cancer_map, extra_charts, created_visualizations)
        
        return True
        
    except Exception as e:
        print(f"Error generating visualizations: {str(e)}")
        return False

def create_population_heatmap(city_data):
    """Create a heatmap showing city populations"""
    # Calculate mean coordinates from the city data for map centering
    mean_lat = city_data['lat'].mean()
    mean_long = city_data['lng'].mean()
    map_center = [mean_lat, mean_long]
    
    # Create the map centered on the mean coordinates of the cities
    m = folium.Map(location=map_center, zoom_start=10)
    
    # Create heat data from city populations
    heat_data = []
    for idx, row in city_data.iterrows():
        # Add [latitude, longitude, population] for each city
        heat_data.append([row['lat'], row['lng'], row['population']])
    
    # Add heatmap to the Folium map
    HeatMap(heat_data, radius=55, blur=15, max_zoom=13).add_to(m)
    
    # Add a title
    title_html = '''
    <div style="position: fixed;
    top: 10px; left: 50px; width: 300px; height: 30px;
    background-color: rgba(27, 38, 59, 0.8); border-radius: 5px;
    z-index: 900;">
    <h4 style="text-align:center; margin-top: 5px; color: white;">Population Distribution</h4>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    # Save to a temporary HTML file
    map_file = 'population_map.html'
    m.save(map_file)
    return map_file

def create_cancer_incidence_map(merged_data, cancer_cols):
    """Create a heatmap of cancer incidence rates"""
    # Calculate mean coordinates from the data for map centering
    mean_lat = merged_data['lat'].mean()
    mean_long = merged_data['lng'].mean()
    map_center = [mean_lat, mean_long]
    
    # Create the map centered on the mean coordinates
    m = folium.Map(location=map_center, zoom_start=10)
    
    # Calculate total cancer incidence for each city
    merged_data['TotalCancer'] = merged_data[cancer_cols].sum(axis=1)
    
    # Calculate cases per capita (cases per 1000 people)
    merged_data['CancerRate'] = (merged_data['TotalCancer'] / merged_data['population']) * 1000
    heat_metric = 'CancerRate'
    popup_metric = 'Cancer Rate per 1,000'
    
    # Prepare heat data
    heat_data = merged_data[['lat', 'lng', heat_metric]].values.tolist()
    
    # Add heatmap to the map
    HeatMap(
        heat_data,
        radius=55,
        blur=15,
        max_zoom=13
    ).add_to(m)
    
    # Create markers for each city with popups
    for idx, row in merged_data.iterrows():
        # Create table for cancer data
        table_html = f"""
        <table style="width: 100%; border-collapse: collapse; color: white;">
            <tr>
                <th style="border: 1px solid #415a77; padding: 5px; background-color: #415a77;">Cancer Type</th>
                <th style="border: 1px solid #415a77; padding: 5px; background-color: #415a77;">Cases</th>
            </tr>
        """
        
        for cancer in cancer_cols:
            if row[cancer] > 0:
                table_html += f"""
                <tr>
                    <td style="border: 1px solid #415a77; padding: 5px;">{cancer}</td>
                    <td style="border: 1px solid #415a77; padding: 5px; text-align: center;">{int(row[cancer])}</td>
                </tr>
                """
        
        table_html += "</table>"
        
        # Create popup content
        popup_html = f"""
        <div style="font-family: 'Roboto', Arial, sans-serif; color: white; background-color: #1b263b; padding: 10px; border-radius: 5px; border: 1px solid #415a77; width: 300px;">
            <h3 style="color: white; margin-top: 0;">{row['City']}, {row['State']}</h3>
            <p><strong>{popup_metric}:</strong> {round(row[heat_metric], 1)}</p>
            <p><strong>Population:</strong> {row['population']:,}</p>
            <p><strong>Total Cancer Cases:</strong> {int(row['TotalCancer'])}</p>
            <h4 style="color: white; margin-bottom: 5px;">Cancer Type Breakdown:</h4>
            {table_html}
        </div>
        """
        
        # Add marker with popup
        popup = folium.Popup(popup_html, max_width=500)
        folium.Marker(
            location=[row['lat'], row['lng']],
            popup=popup,
            icon=folium.Icon(color='blue', icon='info-sign')
        ).add_to(m)
    
    # Add title
    title_html = '''
    <div style="position: fixed; top: 10px; left: 50px; width: 300px; height: 30px; 
             background-color: rgba(27, 38, 59, 0.8); border-radius: 5px; z-index: 900;">
        <h4 style="text-align:center; margin-top: 5px; color: white;">Cancer Incidence Heatmap</h4>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    # Save to HTML
    map_file = 'cancer_map.html'
    m.save(map_file)
    
    return map_file

def create_race_demographics_chart(county_race_data):
    """Create a chart showing race/ethnicity demographics by county"""
    race_cols = [col for col in county_race_data.columns if col != 'County']
    
    fig = go.Figure()
    
    colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99', '#c2c2f0', '#ffb3e6', '#ffd700']
    
    for idx, row in county_race_data.iterrows():
        county = row['County']
        values = [row[col] for col in race_cols]
        
        fig.add_trace(go.Bar(
            y=race_cols,
            x=values,
            name=county,
            orientation='h',
            marker_color=colors[idx % len(colors)],
            hovertemplate="<b>%{y}</b><br>Population: %{x:,}<extra></extra>"
        ))
    
    fig.update_layout(
        title={
            'text': 'Race/Ethnicity Demographics by County',
            'font': {'size': 24, 'color': 'white'}
        },
        xaxis_title={'text': 'Population', 'font': {'size': 18, 'color': 'white'}},
        yaxis_title={'text': 'Race/Ethnicity', 'font': {'size': 18, 'color': 'white'}},
        barmode='group',
        height=600,
        margin=dict(l=150, r=20, t=50, b=50),
        plot_bgcolor='#1b263b',
        paper_bgcolor='#1b263b',
        font={'color': 'white'},
        legend={'font': {'size': 14, 'color': 'white'}},
        yaxis={'gridcolor': '#415a77'},
        xaxis={'gridcolor': '#415a77'},
        hovermode='closest',
        dragmode='pan'
    )
    
    # Add download buttons
    fig.update_layout(
        modebar_add=[
            'toImage',
            'zoom2d',
            'pan2d',
            'select2d',
            'lasso2d',
            'zoomIn2d',
            'zoomOut2d',
            'autoScale2d',
            'resetScale2d'
        ]
    )
    
    chart_file = 'race_demographics.html'
    pio.write_html(fig, file=chart_file, full_html=True, include_plotlyjs='cdn', config={
        'displayModeBar': True,
        'scrollZoom': True,
        'modeBarButtonsToAdd': ['v1hovermode', 'hoverclosest', 'hovercompare']
    })
    
    return chart_file

def create_age_distribution_chart(age_sex_data):
    """Create a chart showing age distribution by sex"""
    age_cols = [col for col in age_sex_data.columns if col != 'Sex']
    
    fig = go.Figure()
    
    colors = ['#66b3ff', '#ff9999']  # Blue for male, pink for female
    
    for idx, row in age_sex_data.iterrows():
        sex = row['Sex']
        values = [row[col] for col in age_cols]
        
        fig.add_trace(go.Bar(
            x=age_cols,
            y=values,
            name=sex,
            marker_color=colors[idx % len(colors)],
            hovertemplate="<b>%{x}</b><br>Population: %{y:,}<extra></extra>"
        ))
    
    fig.update_layout(
        title={
            'text': 'Age Distribution by Sex',
            'font': {'size': 24, 'color': 'white'}
        },
        xaxis_title={'text': 'Age Group', 'font': {'size': 18, 'color': 'white'}},
        yaxis_title={'text': 'Population', 'font': {'size': 18, 'color': 'white'}},
        barmode='group',
        height=500,
        plot_bgcolor='#1b263b',
        paper_bgcolor='#1b263b',
        font={'color': 'white'},
        legend={'font': {'size': 14, 'color': 'white'}},
        xaxis={'gridcolor': '#415a77'},
        yaxis={'gridcolor': '#415a77'},
        hovermode='closest',
        dragmode='pan'
    )
    
    # Add download buttons
    fig.update_layout(
        modebar_add=[
            'toImage',
            'zoom2d',
            'pan2d',
            'select2d',
            'lasso2d',
            'zoomIn2d',
            'zoomOut2d',
            'autoScale2d',
            'resetScale2d'
        ]
    )
    
    chart_file = 'age_distribution.html'
    pio.write_html(fig, file=chart_file, full_html=True, include_plotlyjs='cdn', config={
        'displayModeBar': True,
        'scrollZoom': True
    })
    
    return chart_file

def create_trend_analysis(cancer_data, year_cols):
    """Create a line chart showing cancer trends over time"""
    year_data = cancer_data.melt(
        id_vars=['City'], 
        value_vars=year_cols,
        var_name='Year',
        value_name='Cases'
    )
    year_data['Year'] = year_data['Year'].astype(int)
    
    fig = go.Figure()
    
    from plotly.colors import qualitative
    colors = qualitative.Plotly
    
    for i, city in enumerate(year_data['City'].unique()):
        city_data = year_data[year_data['City'] == city]
        
        fig.add_trace(go.Scatter(
            x=city_data['Year'],
            y=city_data['Cases'],
            mode='lines+markers',
            name=city,
            line=dict(color=colors[i % len(colors)], width=3),
            marker=dict(size=10),
            hovertemplate="<b>%{x}</b><br>Cases: %{y:,}<extra></extra>"
        ))
    
    fig.update_layout(
        title={
            'text': 'Cancer Cases Trend by City',
            'font': {'size': 24, 'color': 'white'}
        },
        xaxis_title={'text': 'Year', 'font': {'size': 18, 'color': 'white'}},
        yaxis_title={'text': 'Number of Cases', 'font': {'size': 18, 'color': 'white'}},
        height=500,
        plot_bgcolor='#1b263b',
        paper_bgcolor='#1b263b',
        font={'color': 'white'},
        legend={'font': {'size': 14, 'color': 'white'}},
        xaxis={'gridcolor': '#415a77'},
        yaxis={'gridcolor': '#415a77'},
        hovermode='closest',
        dragmode='pan'
    )
    
    # Add download buttons
    fig.update_layout(
        modebar_add=[
            'toImage',
            'zoom2d',
            'pan2d',
            'select2d',
            'lasso2d',
            'zoomIn2d',
            'zoomOut2d',
            'autoScale2d',
            'resetScale2d'
        ]
    )
    
    chart_file = 'cancer_trends.html'
    pio.write_html(fig, file=chart_file, full_html=True, include_plotlyjs='cdn', config={
        'displayModeBar': True,
        'scrollZoom': True
    })
    
    return chart_file

def create_cancer_distribution_chart(cancer_data, cancer_cols):
    """Create a chart showing distribution of cancer types"""
    cancer_totals = {}
    for cancer in cancer_cols:
        cancer_totals[cancer] = cancer_data[cancer].sum()
    
    colors = ['#ff9999','#66b3ff','#99ff99','#ffcc99','#c2c2f0','#ffb3e6', '#ffd700']
    
    fig = go.Figure(data=[go.Pie(
        labels=list(cancer_totals.keys()),
        values=list(cancer_totals.values()),
        hole=.3,
        marker_colors=colors[:len(cancer_totals)],
        hovertemplate="<b>%{label}</b><br>Cases: %{value:,}<br>Percentage: %{percent}<extra></extra>"
    )])
    
    fig.update_layout(
        title={
            'text': 'Distribution of Cancer Types',
            'font': {'size': 24, 'color': 'white'}
        },
        height=500,
        plot_bgcolor='#1b263b',
        paper_bgcolor='#1b263b',
        font={'color': 'white'},
        legend={'font': {'size': 14, 'color': 'white'}}
    )
    
    # Add download buttons
    fig.update_layout(
        modebar_add=[
            'toImage',
            'zoom2d',
            'pan2d',
            'select2d',
            'lasso2d',
            'zoomIn2d',
            'zoomOut2d',
            'autoScale2d',
            'resetScale2d'
        ]
    )
    
    chart_file = 'cancer_distribution.html'
    pio.write_html(fig, file=chart_file, full_html=True, include_plotlyjs='cdn', config={
        'displayModeBar': True,
        'scrollZoom': True
    })
    
    return chart_file

def generate_html_output(population_map, cancer_map, extra_charts, created_visualizations):
    """Combine all visualizations into a single HTML file"""
    # Start building the HTML template
    html_template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Cancer Data Visualization Report</title>
        <style>
            body {
                font-family: 'Roboto', Arial, sans-serif;
                margin: 0;
                padding: 0;
                background-color: #0d1b2a; /* Dark navy blue background */
                color: #ffffff; /* White text for readability */
            }
            .container {
                display: flex;
                flex-direction: column;
                padding: 20px;
            }
            .section {
                margin-bottom: 40px;
                background-color: #1b263b; /* Medium blue for sections */
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 4px 10px rgba(0, 0, 0, 0.5);
                border: 1px solid #415a77; /* Blue-gray border */
            }
            .map-container {
                height: 500px;
                width: 100%;
                margin: 20px 0;
                border-radius: 8px;
                overflow: hidden;
                border: 2px solid #415a77; /* Blue-gray border */
            }
            .chart-container {
                height: 500px;
                width: 100%;
                margin: 20px 0;
                border-radius: 8px;
                overflow: hidden;
                background-color: #1b263b; /* Medium blue background */
                border: 2px solid #415a77; /* Blue-gray border */
            }
            h1, h2, h3 {
                color: #ffffff; /* White text for headings */
                margin-top: 0;
            }
            .button {
                background-color: #415a77; /* Blue-gray for buttons */
                color: #ffffff;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                cursor: pointer;
                font-size: 16px;
                transition: background-color 0.3s ease;
                margin: 5px;
                text-decoration: none;
                display: inline-block;
            }
            .button:hover {
                background-color: #566c86; /* Lighter blue-gray on hover */
            }
            .nav-buttons {
                display: flex;
                justify-content: center;
                gap: 20px;
                margin-bottom: 20px;
            }
            iframe {
                border: none;
                width: 100%;
                height: 100%;
            }
            .two-column {
                display: flex;
                gap: 20px;
                flex-wrap: wrap;
            }
            .column {
                flex: 1;
                min-width: 300px;
            }
            .no-data-message {
                background-color: #1b263b;
                padding: 20px;
                border-radius: 8px;
                text-align: center;
                margin: 20px 0;
                border: 1px solid #415a77;
            }
            @media (max-width: 768px) {
                .two-column {
                    flex-direction: column;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="nav-buttons">
                <a href="/" class="button">Home</a>
                <a href="/import" class="button">Import</a>
            </div>
            
            <h1>Cancer Data Visualization Report</h1>
    """
    
    # Check if any visualizations were created
    if not any(created_visualizations.values()):
        html_template += """
            <div class="no-data-message">
                <h2>No data available for visualization</h2>
                <p>Please upload valid data files to generate visualizations.</p>
            </div>
        """
    else:
        # Add population and cancer maps section - only if at least one exists
        if created_visualizations.get('population_map', False) or created_visualizations.get('cancer_map', False):
            html_template += '<div class="two-column">'
            
            # Add population map if created
            if created_visualizations.get('population_map', False) and population_map:
                html_template += f"""
                <div class="column">
                    <div class="section">
                        <h2>Population Distribution</h2>
                        <div class="map-container">
                            <iframe src="/{population_map}"></iframe>
                        </div>
                    </div>
                </div>
                """
            
            # Add cancer map if created
            if created_visualizations.get('cancer_map', False) and cancer_map:
                html_template += f"""
                <div class="column">
                    <div class="section">
                        <h2>Cancer Incidence Heatmap</h2>
                        <div class="map-container">
                            <iframe src="/{cancer_map}"></iframe>
                        </div>
                    </div>
                </div>
                """
            
            html_template += '</div>'
        
        # Now handle the additional chart files
        chart_mapping = {
            'race_demographics.html': ('Race/Ethnicity Demographics', 'race_demographics'),
            'age_distribution.html': ('Age Distribution', 'age_distribution'),
            'cancer_trends.html': ('Cancer Trends Over Time', 'cancer_trends'),
            'cancer_distribution.html': ('Cancer Type Distribution', 'cancer_distribution')
        }
        
        # Group charts in pairs for the two-column layout
        charts_to_display = []
        for chart_file, (title, key) in chart_mapping.items():
            if created_visualizations.get(key, False) and chart_file in [os.path.basename(c) for c in extra_charts]:
                charts_to_display.append((chart_file, title))
        
        # Process charts in pairs for the two-column layout
        for i in range(0, len(charts_to_display), 2):
            html_template += '<div class="two-column">'
            
            # First chart in the pair
            first_chart, first_title = charts_to_display[i]
            html_template += f"""
            <div class="column">
                <div class="section">
                    <h2>{first_title}</h2>
                    <div class="chart-container">
                        <iframe src="/{first_chart}"></iframe>
                    </div>
                </div>
            </div>
            """
            
            # Second chart in the pair (if exists)
            if i + 1 < len(charts_to_display):
                second_chart, second_title = charts_to_display[i + 1]
                html_template += f"""
                <div class="column">
                    <div class="section">
                        <h2>{second_title}</h2>
                        <div class="chart-container">
                            <iframe src="/{second_chart}"></iframe>
                        </div>
                    </div>
                </div>
                """
            
            html_template += '</div>'
    
    # Close the HTML
    html_template += """
        </div>
    </body>
    </html>
    """
    
    # Write the final HTML
    output_file = "custom_cancer_map_v12_4.html"
    with open(output_file, "w") as f:
        f.write(html_template)
    
    print(f"{output_file} has been created with successfully generated visualizations.")
    return output_file

# This allows the script to be run directly or imported as a module
if __name__ == "__main__":
    generate_visualization()