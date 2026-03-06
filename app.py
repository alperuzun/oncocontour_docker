from flask import Flask, request, jsonify, render_template_string, send_from_directory, make_response
import folium
from folium.plugins import HeatMap
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import plotly.graph_objs as go
import plotly.io as pio
import base64
from io import BytesIO
import os
import re
import import_data as custom_cancer_map

app = Flask(__name__)

# Set up upload folder
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Set up static folder
STATIC_FOLDER = '.'
if not os.path.exists(STATIC_FOLDER):
    os.makedirs(STATIC_FOLDER)

def clear_uploads_folder():
    """Clear all files in the uploads folder"""
    for filename in os.listdir(UPLOAD_FOLDER):
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")

# ---------------------------------------------------------------------------
# Functions from cancermaps_v12.0.py not previously in app.py
# ---------------------------------------------------------------------------

def create_total_cancer_chart(location_name, location_data, years):
    """
    Create a matplotlib line chart of total cancer cases per year for a city.
    Returns an <img> HTML string (base64 PNG) or '' on failure.
    Ported from cancermaps_v12.0.py.
    """
    if location_data is None or location_data.empty:
        return ""
    try:
        total_cases = location_data[years].astype(int).values.flatten()
        if len(total_cases) != len(years):
            return ""

        with plt.ioff():
            fig, ax = plt.subplots(figsize=(3.5, 2.2))
            ax.plot(years, total_cases, marker="o", color="#66b3ff")
            ax.set_title(f"Total Cancer Trend in {location_name}", fontsize=9, color="white")
            ax.set_xlabel("Year", fontsize=8, color="white")
            ax.set_ylabel("Number of Cases", fontsize=8, color="white")
            ax.tick_params(colors="white", labelsize=7)
            fig.patch.set_facecolor("#1b263b")
            ax.set_facecolor("#0d1b2a")
            for spine in ax.spines.values():
                spine.set_edgecolor("#415a77")

            buf = BytesIO()
            plt.savefig(buf, format="png", bbox_inches="tight",
                        facecolor=fig.get_facecolor())
            plt.close(fig)
            buf.seek(0)
            image = base64.b64encode(buf.read()).decode("utf-8")
            return f'<img src="data:image/png;base64,{image}" width="320" height="200">'

    except Exception as e:
        print(f"Chart error for {location_name}: {e}")
        return ""


def create_interactive_comparative_chart(df, city_coordinates, years):
    """
    Create a Plotly chart comparing cancer trends across all cities.
    Returns an HTML div string.
    Ported from cancermaps_v12.0.py.
    """
    traces = []
    for city in city_coordinates.keys():
        location_data = df[df['City'] == city]
        if location_data.empty:
            continue
        try:
            total_cases = location_data[years].astype(int).values.flatten()
            if len(total_cases) != len(years):
                continue
            trace = go.Scatter(
                x=years,
                y=total_cases,
                mode='lines+markers',
                name=city,
                hovertemplate=f"<b>{city}</b><br>Year: %{{x}}<br>Cases: %{{y:,}}<extra></extra>"
            )
            traces.append(trace)
        except Exception:
            continue

    layout = go.Layout(
        title={
            'text': 'Interactive Comparative Cancer Trends Across Cities',
            'font': {'size': 20, 'color': 'white'}
        },
        xaxis=dict(title='Year', color='white', gridcolor='#415a77'),
        yaxis=dict(title='Number of Cases', color='white', gridcolor='#415a77'),
        hovermode='closest',
        height=500,
        plot_bgcolor='#1b263b',
        paper_bgcolor='#1b263b',
        font={'color': 'white'},
        legend={'font': {'size': 12, 'color': 'white'}},
        margin=dict(l=60, r=20, t=60, b=60)
    )
    fig = go.Figure(data=traces, layout=layout)
    return pio.to_html(fig, full_html=False,
                       config={'displayModeBar': True, 'scrollZoom': True})


def create_cancer_table(df, location_name, cancer_types, population_data):
    """
    Create an HTML table of cancer types and case counts for a city popup.
    Ported from cancermaps_v12.0.py.
    """
    location_data = df[df['City'] == location_name]
    population = population_data.get(location_name, 'N/A')

    table_html = """
    <table style="width:100%; border-collapse:collapse; color:white; font-size:13px;">
        <tr>
            <th style="border:1px solid #415a77; padding:5px; background-color:#415a77;">Cancer Type</th>
            <th style="border:1px solid #415a77; padding:5px; background-color:#415a77;">Cases</th>
        </tr>
    """
    for cancer in cancer_types:
        try:
            num_cases = int(location_data[cancer].values[0])
        except Exception:
            num_cases = 0
        table_html += (
            f"<tr>"
            f"<td style='border:1px solid #415a77; padding:5px;'>{cancer}</td>"
            f"<td style='border:1px solid #415a77; padding:5px; text-align:center;'>{num_cases}</td>"
            f"</tr>"
        )
    table_html += (
        f"<tr>"
        f"<td style='border:1px solid #415a77; padding:5px; font-weight:bold;'>Population</td>"
        f"<td style='border:1px solid #415a77; padding:5px; text-align:center;'>"
        f"{int(population):,}</td>"
        f"</tr>"
    )
    table_html += "</table>"
    return table_html


def generate_graph_table(df, city_coordinates, years, num_per_row=2):
    """
    Build a grid of per-city matplotlib trend charts.
    Returns an HTML table string.
    Ported from cancermaps_v12.0.py.
    """
    graphs = []
    for city in city_coordinates.keys():
        location_data = df[df['City'] == city]
        chart_html = create_total_cancer_chart(city, location_data, years)
        if chart_html:
            label = (f"<div style='text-align:center;font-size:12px;"
                     f"color:#aaa;margin-bottom:4px;'>{city}</div>")
            graphs.append(label + chart_html)

    if not graphs:
        return "<p style='color:#aaa;'>No trend charts available.</p>"

    table_html = "<table style='width:100%; border-collapse:collapse;'>"
    for i in range(0, len(graphs), num_per_row):
        table_html += "<tr>"
        for graph in graphs[i:i + num_per_row]:
            table_html += (
                f"<td style='border:1px solid #415a77; padding:12px;"
                f"vertical-align:top; background-color:#162c49;'>{graph}</td>"
            )
        table_html += "</tr>"
    table_html += "</table>"
    return table_html


# ---------------------------------------------------------------------------
# Functions from cancermaps_v12.1.py not previously in app.py
# ---------------------------------------------------------------------------

def create_population_table(county_race_data):
    """
    Convert county race DataFrame to a styled HTML table.
    Ported from cancermaps_v12.1.py.
    """
    return county_race_data.to_html(
        index=False, border=0, justify='center', classes='cancer-csv-table'
    )


def create_age_sex_population_table(age_sex_data):
    """
    Convert age/sex DataFrame to a styled HTML table.
    Ported from cancermaps_v12.1.py.
    """
    return age_sex_data.to_html(
        index=False, border=0, justify='center', classes='cancer-csv-table'
    )


def create_population_pie_chart(county_race_data):
    """
    Pie chart of race proportions derived from uploaded county race data.
    Ported from cancermaps_v12.1.py.
    """
    try:
        race_cols = [c for c in county_race_data.columns if c != 'County']
        totals = county_race_data[race_cols].sum()
        labels = totals.index.tolist()
        sizes = totals.values.tolist()
        colors = ['#ff9999','#66b3ff','#99ff99','#ffcc99','#c2c2f0','#ffb3e6','#ffd700',
                  '#aec6cf','#b39ddb','#80cbc4']

        with plt.ioff():
            fig, ax = plt.subplots(figsize=(6, 4))  # FIX: reduced from (12, 8)
            ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90,
                   colors=colors[:len(labels)],
                   wedgeprops={'edgecolor': 'black'},
                   textprops={'fontsize': 10, 'color': 'white'})
            ax.axis('equal')
            fig.patch.set_facecolor('#1b263b')
            plt.tight_layout()

            buf = BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight',
                        facecolor=fig.get_facecolor())
            plt.close(fig)
            buf.seek(0)
            image = base64.b64encode(buf.read()).decode('utf-8')
            return (f'<img src="data:image/png;base64,{image}" '
                    f'style="width:100%; height:auto;">')  # FIX: removed max-width/margin/display
    except Exception as e:
        print(f"Race pie chart error: {e}")
        return ''


def create_hispanic_population_pie_chart(county_race_data):
    """
    Pie chart of Hispanic vs non-Hispanic population derived from uploaded data.
    If a 'Hispanic or Latino' column exists, uses real data; otherwise falls back
    to RI state-level figures from cancermaps_v12.1.py.
    Ported from cancermaps_v12.1.py.
    """
    try:
        hispanic_col = next(
            (c for c in county_race_data.columns
             if 'hispanic' in c.lower() or 'latino' in c.lower()), None
        )
        if hispanic_col:
            hispanic_total = county_race_data[hispanic_col].sum()
            other_total = county_race_data[
                [c for c in county_race_data.columns
                 if c != 'County' and c != hispanic_col]
            ].sum().sum()
            sizes = [hispanic_total, other_total]
        else:
            sizes = [16.6, 83.4]

        labels = ['Hispanic or Latino', 'Non Hispanic or Latino']
        colors = ['#c2c2f0', '#8fbc8f']

        with plt.ioff():
            fig, ax = plt.subplots(figsize=(6, 4))  # FIX: reduced from (12, 8)
            ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90,
                   colors=colors,
                   wedgeprops={'edgecolor': 'black'},
                   textprops={'fontsize': 10, 'color': 'white'})
            ax.axis('equal')
            fig.patch.set_facecolor('#1b263b')
            plt.tight_layout()

            buf = BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight',
                        facecolor=fig.get_facecolor())
            plt.close(fig)
            buf.seek(0)
            image = base64.b64encode(buf.read()).decode('utf-8')
            return (f'<img src="data:image/png;base64,{image}" '
                    f'style="width:100%; height:auto;">')  # FIX: removed max-width/margin/display
    except Exception as e:
        print(f"Hispanic pie chart error: {e}")
        return ''


def create_age_pie_chart(age_sex_data):
    """
    Pie chart of total population by age group.
    Ported from cancermaps_v12.1.py.
    """
    try:
        import numpy as np
        age_labels = age_sex_data.columns[1:]
        total_by_age = age_sex_data[age_labels].sum()

        with plt.ioff():
            fig, ax = plt.subplots(figsize=(6, 4))  # FIX: reduced from (12, 8)
            ax.pie(total_by_age, labels=age_labels, autopct='%1.1f%%', startangle=90,
                   colors=plt.cm.Pastel1(np.linspace(0, 1, len(age_labels))),
                   textprops={'fontsize': 10, 'color': 'white'})
            ax.axis('equal')
            fig.patch.set_facecolor('#1b263b')
            plt.tight_layout()

            buf = BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight',
                        facecolor=fig.get_facecolor())
            plt.close(fig)
            buf.seek(0)
            image = base64.b64encode(buf.read()).decode('utf-8')
            return (f'<img src="data:image/png;base64,{image}" '
                    f'style="width:100%; height:auto;">')  # FIX: removed max-width/margin/display
    except Exception as e:
        print(f"Age pie chart error: {e}")
        return ''


def create_sex_pie_chart(age_sex_data):
    """
    Pie chart of total population split by sex.
    Ported from cancermaps_v12.1.py.
    """
    try:
        age_cols = age_sex_data.columns[1:]
        male_total   = age_sex_data.loc[age_sex_data['Sex'] == 'Male',   age_cols].sum().sum()
        female_total = age_sex_data.loc[age_sex_data['Sex'] == 'Female', age_cols].sum().sum()
        sizes  = [male_total, female_total]
        labels = ['Male', 'Female']
        colors = ['#66b3ff', '#ff9999']

        with plt.ioff():
            fig, ax = plt.subplots(figsize=(6, 4))  # FIX: reduced from (12, 8)
            ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90,
                   colors=colors, textprops={'fontsize': 10, 'color': 'white'})
            ax.set_title('Population by Sex', fontsize=14, color='white')
            ax.axis('equal')
            fig.patch.set_facecolor('#1b263b')
            plt.tight_layout()

            buf = BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight',
                        facecolor=fig.get_facecolor())
            plt.close(fig)
            buf.seek(0)
            image = base64.b64encode(buf.read()).decode('utf-8')
            return (f'<img src="data:image/png;base64,{image}" '
                    f'style="width:100%; height:auto;">')  # FIX: removed max-width/margin/display
    except Exception as e:
        print(f"Sex pie chart error: {e}")
        return ''


# ---------------------------------------------------------------------------
# Page HTML strings
# ---------------------------------------------------------------------------

# Landing page HTML
landing_page_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OncoContour - Cancer Research Data Portal</title>
    <style>
        body {
            font-family: 'Roboto', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #1e1e2f;
            color: #e4e4eb;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            margin-bottom: 30px;
        }
        .brand-name {
            font-size: 2.5rem;
            font-weight: bold;
            margin: 0;
            color: #e4e4eb;
        }
        .tagline {
            font-size: 1.2rem;
            color: #aaa;
            margin-top: 5px;
        }
        .app-title {
            font-size: 3rem;
            font-weight: bold;
            color: #8a9bb5;
            margin: 10px 0 5px 0;
        }
        .app-description {
            font-size: 1rem;
            color: #b0b8c8;
            max-width: 680px;
            margin: 12px auto 0 auto;
            line-height: 1.7;
            text-align: center;
        }
        .nav-buttons {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin: 30px 0;
        }
        .button {
            background-color: #444e69;
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
            background-color: #575f7f;
        }
        .logo-container {
            margin-top: 30px;
            text-align: center;
        }
        .logo {
            width: 160px;
            height: 160px;
            margin-bottom: 15px;
        }
        .iframe-container {
            width: 45%;
            height: 300px;
            border: 2px solid #444e69;
            border-radius: 8px;
            margin: 20px;
            display: inline-block;
            cursor: pointer;
            overflow: hidden;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .iframe-container:hover {
            transform: scale(1.05);
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        }
        iframe {
            width: 100%;
            height: 100%;
            border: none;
            pointer-events: none;
        }
        .section-title {
            margin-top: 40px;
            border-bottom: 2px solid #444e69;
            padding-bottom: 10px;
        }
        .footer {
            margin-top: 60px;
            text-align: center;
            font-size: 0.9rem;
            color: #aaa;
            padding: 20px 0;
            border-top: 1px solid #444e69;
        }
        @media (max-width: 768px) {
            .iframe-container {
                width: 90%;
                height: 200px;
            }
            .logo {
                width: 120px;
                height: 120px;
            }
            .brand-name {
                font-size: 2rem;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="nav-buttons">
            <a href="/" class="button">Home</a>
            <a href="/import" class="button">Import Data</a>
            <a href="/user-guide" class="button">User Guide</a>
            <a href="/about" class="button">About</a>
        </div>
        
        <div class="logo-container">
            <img src="/OncoContour.png" alt="OncoContour Logo" class="logo">
            <p class="app-title">OncoContour</p>
            <p class="tagline">Geographic Visualization of Cancer Statistics</p>
            <p class="app-description">
                OncoContour is a geospatial cancer analytics platform designed to help researchers,
                clinicians, and public health professionals explore and visualize cancer incidence data
                across geographic regions. By combining interactive heatmaps, demographic breakdowns,
                and multi-year trend analysis, OncoContour transforms raw cancer statistics into
                actionable, map-based insights.
            </p>
        </div>

        <h2 class="section-title">Region Specific Cancer Mapping</h2>
        <p>Click on a visualization to view it in full screen:</p>
        
        <div class="iframe-container" onclick="navigateTo('/rhode_island_cancer_map_v12.1.html')">
            <iframe src="rhode_island_cancer_map_v12.1.html" title="Population Distribution"></iframe>
        </div>
        <div class="iframe-container" onclick="navigateTo('/rhode_island_cancer_map_v12.html')">
            <iframe src="rhode_island_cancer_map_v12.html" title="Cancer Incidence Map"></iframe>
        </div>

        <div id="visualization"></div>
        
        <div class="footer">
            <p>© <span id="footer-year"></span> OncoContour - Geospatial Cancer Analytics</p>
            <script>document.getElementById('footer-year').textContent = new Date().getFullYear();</script>
        </div>
    </div>

    <script>
        function navigateTo(path) {
            window.location.href = path;
        }
    </script>
</body>
</html>
"""

# Import page HTML content
import_page_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Import Data - OncoContour</title>
    <style>
        body {
            font-family: 'Roboto', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #1e1e2f;
            color: #e4e4eb;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .nav-buttons {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-bottom: 20px;
        }
        .button {
            background-color: #444e69;
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
            background-color: #575f7f;
        }
        .upload-section {
            background-color: #2a2a3c;
            padding: 20px;
            border-radius: 8px;
            margin-top: 40px;
        }
        .file-group-container {
            display: flex;
            flex-wrap: wrap;
            justify-content: space-between;
            margin-bottom: 20px;
        }
        .file-group {
            padding: 15px;
            background-color: #353549;
            border-radius: 8px;
            width: calc(50% - 40px);
            margin: 10px;
            box-sizing: border-box;
        }
        .example-data {
            padding: 15px;
            background-color: #353549;
            border-radius: 8px;
            width: calc(50% - 40px);
            margin: 10px;
            box-sizing: border-box;
        }
        .status {
            margin-top: 10px;
            padding: 10px;
            border-radius: 4px;
        }
        .success {
            background-color: #28a745;
            color: white;
            display: none;
        }
        .error {
            background-color: #dc3545;
            color: white;
            display: none;
        }
        #visualizeBtn {
            margin: 20px auto;
            width: 200px;
            display: block;
        }
        .csv-content {
            background-color: #2a2a3c;
            color: #e4e4eb;
            font-family: monospace;
            padding: 10px;
            border-radius: 4px;
            white-space: pre;
            overflow-x: auto;
            margin-top: 10px;
            font-size: 14px;
            line-height: 1.4;
        }
        .footer {
            margin-top: 60px;
            text-align: center;
            font-size: 0.9rem;
            color: #aaa;
            padding: 20px 0;
            border-top: 1px solid #444e69;
        }
        @media (max-width: 768px) {
            .file-group, .example-data {
                width: 100%;
                margin: 10px 0;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="nav-buttons">
            <a href="/" class="button">Home</a>
            <a href="/import" class="button">Import Data</a>
            <a href="/user-guide" class="button">User Guide</a>
            <a href="/about" class="button">About</a>
        </div>

        <h1>Data Import</h1>

        <div class="upload-section">
            <h2>Upload Your Data</h2>
            
            <!-- Cancer Data Section -->
            <div class="file-group-container">
                <div class="file-group">
                    <h3>Cancer Statistics Data</h3>
                    <p>Upload CSV with format: "City,State,CancerType1,CancerType2,...,Year1,Year2,..."</p>
                    <p>State must be 2-letter abbreviation (e.g., RI, MA)</p>
                    <input type="file" id="cancerDataFile" accept=".csv" class="button">
                    <button onclick="uploadFile('cancer')" class="button">Upload Cancer Data</button>
                    <div id="cancerStatus" class="status"></div>
                </div>

                <div class="example-data">
                    <h3>Example Cancer Data Format</h3>
                    <p>Your CSV should follow this pattern:</p>
                    <div class="csv-content">City,State,Bladder,Breast,Lung,Prostate,2015,2016,2017,2018,2019,2020,2021
Providence,RI,11,50,40,30,47,45,44,42,41,39,37
Lincoln,RI,32,20,15,10,18,35,16,15,14,13,12
Barrington,RI,33,25,18,12,23,55,21,20,19,18,17</div>
                </div>
            </div>

            <!-- City Coordinates Cancer Data Section -->
            <div class="file-group-container">
                <div class="file-group">
                    <h3>City Coordinates Cancer Data</h3>
                    <p>Upload CSV with format: "City,Population,Latitude,Longitude,CancerType1,...,Year1,..."</p>
                    <p>Use this format when you have coordinates directly instead of State abbreviations.</p>
                    <input type="file" id="cityCoordsCancerDataFile" accept=".csv" class="button">
                    <button onclick="uploadFile('cityCoordsCancer')" class="button">Upload City Coords Cancer Data</button>
                    <div id="cityCoordsCancerStatus" class="status"></div>
                </div>

                <div class="example-data">
                    <h3>Example City Coordinates Cancer Data Format</h3>
                    <p>Your CSV should follow this pattern:</p>
                    <div class="csv-content">City,Population,Latitude,Longitude,Bladder,Breast,Lung,Prostate,2015,2016,2017,2018,2019,2020,2021
Providence,190792,41.8236,-71.4222,11,50,40,30,47,45,44,42,41,39,37
Barrington,17061,41.7409,-71.3084,33,25,18,12,23,55,21,20,19,18,17
Cranston,82635,41.7798,-71.4373,20,45,35,25,40,38,37,36,35,34,33</div>
                </div>
            </div>
            
            <!-- County Race Data Section -->
            <div class="file-group-container">
                <div class="file-group">
                    <h3>County Race/Ethnicity Data</h3>
                    <p>Upload CSV starting with "County" followed by any race or ethnicity you're tracking</p>
                    <input type="file" id="countyRaceDataFile" accept=".csv" class="button">
                    <button onclick="uploadFile('countyRace')" class="button">Upload County Race Data</button>
                    <div id="countyRaceStatus" class="status"></div>
                </div>

                <div class="example-data">
                    <h3>Example County Race Data Format</h3>
                    <p>Your CSV should match this format:</p>
                    <div class="csv-content">County,White,Hispanic or Latino,Black,American Indian,Asian,Pacific Islander,Other,Two or More
Bristol,45355,1943,773,105,1285,1,500,2774
Kent,147106,9665,3220,532,4882,40,3860,10723
Newport,72063,5592,2840,362,1570,64,2533,6211
Providence,402194,160323,53803,5362,28614,380,94730,75658
Washington,116202,4578,1532,1024,2610,51,1992,6428</div>
                </div>
            </div>
            
            <!-- Age/Sex Data Section -->
            <div class="file-group-container">
                <div class="file-group">
                    <h3>Age and Sex Population Data</h3>
                    <p>Upload CSV starting with "Sex," followed by age ranges indicated by numbers</p>
                    <input type="file" id="ageSexDataFile" accept=".csv" class="button">
                    <button onclick="uploadFile('ageSex')" class="button">Upload Age/Sex Data</button>
                    <div id="ageSexStatus" class="status"></div>
                </div>

                <div class="example-data">
                    <h3>Example Age/Sex Data Format</h3>
                    <p>Your CSV should follow this structure:</p>
                    <div class="csv-content">Sex,0-9,10-19,20-29,30-39,40-49,50-59,60-69,70-79,80+
Male,55897,68369,78277,74753,63778,73199,67452,38527,16969
Female,54344,66057,75425,72340,62843,75137,73676,46375,30832</div>
                </div>
            </div>

            <button id="visualizeBtn" onclick="visualizeData()" class="button">
                Generate Visualization
            </button>
        </div>
        <div id="visualization"></div>
        
        <div class="footer">
            <p>© <span id="footer-year"></span> OncoContour - Geospatial Cancer Analytics</p>
            <script>document.getElementById('footer-year').textContent = new Date().getFullYear();</script>
        </div>
    </div>

    <script>
        let uploadedFiles = {
            city: false,
            cancer: false,
            cityCoordsCancer: false,
            countyRace: false,
            ageSex: false
        };

        function navigateTo(path) {
            window.location.href = path;
        }

        function uploadFile(type) {
            const fileInput = document.getElementById(type + 'DataFile');
            const file = fileInput.files[0];
            const statusDiv = document.getElementById(type + 'Status');
            
            if (!file) {
                statusDiv.textContent = 'Please select a file first';
                statusDiv.className = 'status error';
                statusDiv.style.display = 'block';
                return;
            }

            const formData = new FormData();
            formData.append('file', file);
            formData.append('type', type);

            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    statusDiv.textContent = 'File uploaded successfully!';
                    statusDiv.className = 'status success';
                    statusDiv.style.display = 'block';
                    uploadedFiles[type] = true;
                } else {
                    statusDiv.textContent = 'Error: ' + data.message;
                    statusDiv.className = 'status error';
                    statusDiv.style.display = 'block';
                }
            })
            .catch(error => {
                statusDiv.textContent = 'Error uploading file: ' + error;
                statusDiv.className = 'status error';
                statusDiv.style.display = 'block';
            });
        }

        function visualizeData() {
            const hasFiles = Object.values(uploadedFiles).some(value => value === true);
            
            if (!hasFiles) {
                alert('Please upload at least one data file before generating visualizations.');
                return;
            }
            
            fetch('/visualize')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    window.location.href = data.redirect;
                } else {
                    alert('Error: ' + data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error generating visualization');
            });
        }
    </script>
</body>
</html>
"""

# About page HTML content
about_page_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>About - OncoContour</title>
    <style>
        body {
            font-family: 'Roboto', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #1e1e2f;
            color: #e4e4eb;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .nav-buttons {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-bottom: 30px;
        }
        .button {
            background-color: #444e69;
            color: #ffffff;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            transition: background-color 0.3s ease;
            text-decoration: none;
            display: inline-block;
        }
        .button:hover {
            background-color: #575f7f;
        }
        .section {
            background-color: #2a2a3c;
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 30px;
        }
        h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
            border-bottom: 2px solid #444e69;
            padding-bottom: 15px;
        }
        h2 {
            font-size: 1.8rem;
            margin-top: 0;
            margin-bottom: 20px;
            border-bottom: 1px solid #444e69;
            padding-bottom: 10px;
        }
        h3 {
            font-size: 1.3rem;
            margin-top: 0;
            margin-bottom: 10px;
            color: #6b9bd1;
        }
        p {
            line-height: 1.8;
            color: #c4c4d4;
            font-size: 1rem;
        }
        .feature-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        .feature-card {
            background-color: #353549;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #6b9bd1;
        }
        .tech-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            margin-top: 20px;
        }
        .tech-tag {
            background-color: #353549;
            color: #e4e4eb;
            padding: 10px 20px;
            border-radius: 20px;
            font-size: 0.95rem;
            border: 1px solid #444e69;
        }
        .authors-section {
            background-color: #2a2a3c;
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 30px;
            border-left: 4px solid #6b9bd1;
        }
        .author-info {
            margin-bottom: 20px;
        }
        .author-info p {
            margin: 5px 0;
        }
        .contact-info {
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #444e69;
        }
        .lab-link {
            display: inline-block;
            background-color: #353549;
            color: #6b9bd1;
            padding: 10px 20px;
            border-radius: 8px;
            text-decoration: none;
            margin-top: 10px;
            transition: background-color 0.3s ease;
        }
        .lab-link:hover {
            background-color: #444e69;
            color: #e4e4eb;
        }
        .footer {
            margin-top: 60px;
            text-align: center;
            font-size: 0.9rem;
            color: #aaa;
            padding: 20px 0;
            border-top: 1px solid #444e69;
        }
        @media (max-width: 768px) {
            h1 { font-size: 2rem; }
            h2 { font-size: 1.5rem; }
            .feature-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="nav-buttons">
            <a href="/" class="button">Home</a>
            <a href="/import" class="button">Import Data</a>
            <a href="/user-guide" class="button">User Guide</a>
            <a href="/about" class="button">About</a>
        </div>

        <div class="section">
            <h1>About This Application</h1>
            <p style="font-size: 1.1rem; color: #a0a0b0;">
                Empowering public health research through data visualization and analysis
            </p>
        </div>

        <div class="authors-section">
            <h2>Authors</h2>
            <div class="author-info">
                <p>This project was developed by Alper Uzun and Daniel White at The Warren Alpert Medical School of Brown University.</p>
            </div>
            
            <h2>Contact</h2>
            <div class="author-info">
                <p>For questions or support, please contact:</p>
                <p>• Dr. Alper Uzun (<a href="mailto:alper_uzun@brown.edu" style="color: #6b9bd1; text-decoration: none;">alper_uzun@brown.edu</a>)</p>
                <p>• Daniel White (<a href="mailto:daniel_white@brown.edu" style="color: #6b9bd1; text-decoration: none;">daniel_white@brown.edu</a>)</p>
            </div>
            
            <div class="contact-info">
                <p>Visit our lab website:</p>
                <a href="https://sites.brown.edu/gmilab/" target="_blank" class="lab-link">Genomics and Machine Intelligence Lab →</a>
            </div>
        </div>

        <div class="section">
            <h2>Purpose and Objectives</h2>
            <p>
                This application provides comprehensive cancer data visualization and analysis tools designed for
                public health researchers, policymakers, and community organizations. The platform combines
                geographic, demographic, and epidemiological data to reveal patterns and trends in cancer
                incidence across different regions, facilitating evidence-based decision making and research.
            </p>
        </div>

        <div class="section">
            <h2>Key Features and Capabilities</h2>
            <div class="feature-grid">
                <div class="feature-card">
                    <h3>Interactive Geographic Mapping</h3>
                    <p>
                        Visualize population density and cancer incidence rates through dynamic heatmaps with
                        interactive markers providing detailed regional information and comparative analysis.
                    </p>
                </div>
                <div class="feature-card">
                    <h3>Temporal Trend Analysis</h3>
                    <p>
                        Examine multi-year cancer incidence patterns with city-by-city comparisons and interactive
                        charting capabilities for comprehensive temporal analysis.
                    </p>
                </div>
                <div class="feature-card">
                    <h3>Custom Data Integration</h3>
                    <p>
                        Import custom CSV datasets to generate tailored visualizations for any geographic region,
                        enabling specialized research and analysis requirements.
                    </p>
                </div>
                <div class="feature-card">
                    <h3>Demographics Integration</h3>
                    <p>
                        Correlate cancer data with age, sex, and race demographics to identify population-specific
                        patterns and inform targeted public health interventions.
                    </p>
                </div>
            </div>
        </div>

        <div class="footer">
            <p>© <span id="footer-year"></span> OncoContour - Geospatial Cancer Analytics</p>
            <script>document.getElementById('footer-year').textContent = new Date().getFullYear();</script>
        </div>
    </div>
</body>
</html>
"""

# User Guide page HTML content
user_guide_page_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>User Guide - OncoContour</title>
    <style>
        body {
            font-family: 'Roboto', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #1e1e2f;
            color: #e4e4eb;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .nav-buttons {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-bottom: 30px;
        }
        .button {
            background-color: #444e69;
            color: #ffffff;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            transition: background-color 0.3s ease;
            text-decoration: none;
            display: inline-block;
        }
        .button:hover { background-color: #575f7f; }
        .guide-box {
            background-color: #2a2a3c;
            border-radius: 10px;
            padding: 40px;
            margin-top: 20px;
            text-align: center;
        }
        h1 {
            font-size: 2rem;
            margin-bottom: 10px;
            border-bottom: 2px solid #444e69;
            padding-bottom: 15px;
        }
        .version {
            color: #aaa;
            font-size: 1rem;
            margin-bottom: 30px;
        }
        .download-link {
            display: inline-flex;
            align-items: center;
            gap: 10px;
            background-color: #444e69;
            color: #ffffff;
            text-decoration: none;
            padding: 14px 28px;
            border-radius: 8px;
            font-size: 1.05rem;
            font-weight: 600;
            transition: background-color 0.3s ease;
        }
        .download-link:hover { background-color: #575f7f; }
        .footer {
            margin-top: 60px;
            text-align: center;
            font-size: 0.9rem;
            color: #aaa;
            padding: 20px 0;
            border-top: 1px solid #444e69;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="nav-buttons">
            <a href="/" class="button">Home</a>
            <a href="/import" class="button">Import Data</a>
            <a href="/user-guide" class="button">User Guide</a>
            <a href="/about" class="button">About</a>
        </div>

        <h1>User Guide</h1>

        <div class="guide-box">
            <p class="version"><strong>Version:</strong> 1.1</p>
            <p style="color: #c4c4d4; margin-bottom: 30px;">Click below to open the OncoContour User Guide.</p>
            <a href="/OncoContourUserGuide.pdf" target="_blank" class="download-link">
                &#8595; Open User Guide (PDF)
            </a>
        </div>

        <div class="footer">
            <p>© <span id="footer-year"></span> OncoContour - Geospatial Cancer Analytics</p>
            <script>document.getElementById('footer-year').textContent = new Date().getFullYear();</script>
        </div>
    </div>
</body>
</html>
"""

# US state abbreviations for validation
US_STATES = {
    'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
    'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
    'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
    'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
    'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
}

# ---------------------------------------------------------------------------
# Flask routes
# ---------------------------------------------------------------------------

@app.route('/')
def home():
    response = make_response(render_template_string(landing_page_html))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response

@app.route('/import')
def import_page():
    response = make_response(render_template_string(import_page_html))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response

@app.route('/about')
def about_page():
    response = make_response(render_template_string(about_page_html))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response

@app.route('/user-guide')
def user_guide_page():
    response = make_response(render_template_string(user_guide_page_html))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file part'})

    file = request.files['file']
    file_type = request.form.get('type', '')

    if file.filename == '':
        return jsonify({'success': False, 'message': 'No selected file'})

    if file and file.filename.endswith('.csv'):
        filename = f"{file_type}_data.csv"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception as e:
                print(f"Error removing existing file: {e}")

        try:
            temp_path = os.path.join(app.config['UPLOAD_FOLDER'], 'temp.csv')
            file.save(temp_path)
            df = pd.read_csv(temp_path)

            if file_type == 'cancer':
                if len(df.columns) < 3:
                    os.remove(temp_path)
                    return jsonify({
                        'success': False,
                        'message': 'Cancer data must have at least City, State and one data column'
                    })
                if df.columns[0].lower() != 'city' or df.columns[1].lower() != 'state':
                    os.remove(temp_path)
                    return jsonify({
                        'success': False,
                        'message': 'First two columns must be "City" and "State"'
                    })
                if not all(str(state).upper() in US_STATES for state in df.iloc[:, 1]):
                    os.remove(temp_path)
                    return jsonify({
                        'success': False,
                        'message': 'State column must contain valid 2-letter US state abbreviations'
                    })
                for col in df.columns[2:]:
                    col_stripped = str(col).strip()
                    if not (col_stripped.isalpha() or col_stripped.isdigit()):
                        os.remove(temp_path)
                        return jsonify({
                            'success': False,
                            'message': f'Column "{col}" must be either a cancer type (text) or year (number)'
                        })

            elif file_type == 'cityCoordsCancer':
                required_cols = ['City', 'Population', 'Latitude', 'Longitude']
                for i, col in enumerate(required_cols):
                    if i >= len(df.columns) or df.columns[i].strip() != col:
                        os.remove(temp_path)
                        return jsonify({
                            'success': False,
                            'message': f'Column {i+1} must be "{col}". Expected: City,Population,Latitude,Longitude,CancerType1,...,Year1,...'
                        })
                if len(df.columns) < 5:
                    os.remove(temp_path)
                    return jsonify({
                        'success': False,
                        'message': 'Must have City, Population, Latitude, Longitude, and at least one cancer type or year column'
                    })

            elif file_type == 'countyRace':
                if df.columns[0] != 'County':
                    os.remove(temp_path)
                    return jsonify({'success': False, 'message': 'First column must be "County"'})

            elif file_type == 'ageSex':
                if df.columns[0] != 'Sex':
                    os.remove(temp_path)
                    return jsonify({'success': False, 'message': 'First column must be "Sex"'})

            os.rename(temp_path, filepath)
            return jsonify({
                'success': True,
                'message': f'{file_type.capitalize()} data uploaded successfully'
            })

        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return jsonify({'success': False, 'message': f'Error processing file: {str(e)}'})

    return jsonify({'success': False, 'message': 'Invalid file format. Please upload a CSV file.'})


@app.route('/<path:filename>')
def serve_file(filename):
    if filename.endswith('.html'):
        try:
            with open(filename, 'r') as f:
                content = f.read()
                response = make_response(content)
                response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
                return response
        except FileNotFoundError:
            return "File not found", 404
    return send_from_directory(STATIC_FOLDER, filename)


@app.route('/visualize')
def visualize():
    import math

    # ------------------------------------------------------------------
    # Helper: build a canonical cancer-type table for popup use.
    # ------------------------------------------------------------------
    def _popup_cancer_table(df, city, cancer_types, population_data):
        location_data = df[df['City'] == city]
        rows = ''
        for ct in cancer_types:
            try:
                n = int(location_data[ct].values[0])
            except Exception:
                n = 0
            rows += (f"<tr><td style='padding:4px 8px;border:1px solid #ccc;'>{ct}</td>"
                     f"<td style='padding:4px 8px;border:1px solid #ccc;text-align:center;'>{n}</td></tr>")
        pop = population_data.get(city, 'N/A')
        pop_fmt = f'{int(pop):,}' if pop != 'N/A' else 'N/A'
        rows += (f"<tr><td style='padding:4px 8px;border:1px solid #ccc;font-weight:bold;'>Population</td>"
                 f"<td style='padding:4px 8px;border:1px solid #ccc;text-align:center;'>{pop_fmt}</td></tr>")
        return (f"<table style='border-collapse:collapse;font-size:12px;width:100%;'>"
                f"<thead><tr>"
                f"<th style='padding:4px 8px;border:1px solid #999;background:#eee;'>Cancer Type</th>"
                f"<th style='padding:4px 8px;border:1px solid #999;background:#eee;'>Cases</th>"
                f"</tr></thead><tbody>{rows}</tbody></table>")

    # ------------------------------------------------------------------
    # Population-only heatmap
    # ------------------------------------------------------------------
    def _build_population_map(city_coordinates, population_data, out_file):
        lats = [v[0] for v in city_coordinates.values()]
        lngs = [v[1] for v in city_coordinates.values()]
        center = [sum(lats) / len(lats), sum(lngs) / len(lngs)]
        m = folium.Map(location=center, zoom_start=10)

        pops    = [max(population_data.get(c, 1), 1) for c in city_coordinates]
        log_pops = [math.log1p(p) for p in pops]
        max_log  = max(log_pops) if log_pops else 1

        heat_data = []
        for city, coord in city_coordinates.items():
            pop       = max(population_data.get(city, 1), 1)
            intensity = math.log1p(pop) / max_log
            heat_data.append([coord[0], coord[1], intensity])

        HeatMap(heat_data, radius=55, blur=15, max_zoom=13).add_to(m)
        folium.LayerControl().add_to(m)
        m.save(out_file)

    # ------------------------------------------------------------------
    # Cancer incidence heatmap
    # ------------------------------------------------------------------
    def _build_cancer_map(city_coordinates, population_data, df_cancer,
                          cancer_types, years, out_file):
        lats = [v[0] for v in city_coordinates.values()]
        lngs = [v[1] for v in city_coordinates.values()]
        center = [sum(lats) / len(lats), sum(lngs) / len(lngs)]
        m = folium.Map(location=center, zoom_start=10)

        heat_data = []
        for city, coord in city_coordinates.items():
            row = df_cancer[df_cancer['City'] == city]
            if row.empty:
                continue
            total = (row[years].astype(float).values.sum()
                     if years else row[cancer_types].astype(float).values.sum())
            pop   = max(population_data.get(city, 1), 1)
            per_100k = (total / pop) * 100_000
            heat_data.append([coord[0], coord[1], per_100k])

        if heat_data:
            max_val    = max(h[2] for h in heat_data) or 1
            normalised = [[h[0], h[1], h[2] / max_val] for h in heat_data]
            HeatMap(normalised, radius=55, blur=15, max_zoom=13).add_to(m)

        for city, coord in city_coordinates.items():
            row = df_cancer[df_cancer['City'] == city]
            if row.empty:
                continue
            table = _popup_cancer_table(df_cancer, city, cancer_types, population_data)
            chart = create_total_cancer_chart(city, row, years)
            popup_html = (
                f"<div style='max-width:480px;font-family:Arial,sans-serif;'>"
                f"<h4 style='margin:0 0 6px;'>{city}</h4>"
                f"{table}"
                f"<div style='margin-top:8px;'>{chart}</div>"
                f"</div>"
            )
            folium.Marker(
                location=coord,
                popup=folium.Popup(popup_html, max_width=500),
                icon=folium.Icon(color='blue', icon='info-sign')
            ).add_to(m)

        folium.LayerControl().add_to(m)
        m.save(out_file)

    try:
        uploaded_files = [f for f in os.listdir(UPLOAD_FOLDER) if f.endswith('.csv')]
        if not uploaded_files:
            return jsonify({
                'success': False,
                'message': 'No data files found. Please upload at least one file.'
            })

        success = custom_cancer_map.generate_visualization(uploads_folder=UPLOAD_FOLDER)
        if not success:
            return jsonify({
                'success': False,
                'message': 'Error generating visualization. Please check your data files.'
            })

        # ----------------------------------------------------------------
        # Paths
        # ----------------------------------------------------------------
        cancer_path             = os.path.join(UPLOAD_FOLDER, 'cancer_data.csv')
        city_coords_cancer_path = os.path.join(UPLOAD_FOLDER, 'cityCoordsCancer_data.csv')
        county_race_path        = os.path.join(UPLOAD_FOLDER, 'countyRace_data.csv')
        age_sex_path            = os.path.join(UPLOAD_FOLDER, 'ageSex_data.csv')

        cancer_table_html      = ''
        comparative_chart_html = ''
        graph_table_html       = ''
        years                  = []

        county_race_table_html = ''
        race_pie_html          = ''
        hispanic_pie_html      = ''
        age_sex_table_html     = ''
        age_pie_html           = ''
        sex_pie_html           = ''

        generated_maps = []

        # ── City-coordinates cancer CSV ─────────────────────────────────
        if os.path.exists(city_coords_cancer_path):
            df_cc = pd.read_csv(city_coords_cancer_path)
            df_cc.columns = df_cc.columns.str.strip()
            fixed_cols      = ['City', 'Population', 'Latitude', 'Longitude']
            years_cc        = [col for col in df_cc.columns if col.strip().isdigit()]
            cancer_types_cc = [col for col in df_cc.columns
                               if col not in fixed_cols + years_cc]

            display_cols_cc = [c for c in df_cc.columns
                               if c not in ('Population', 'Latitude', 'Longitude')]
            if not cancer_table_html:
                cancer_table_html = df_cc[display_cols_cc].to_html(
                    index=False, border=0, classes='cancer-csv-table')

            city_coords_cc = {
                row['City']: [row['Latitude'], row['Longitude']]
                for _, row in df_cc.iterrows()
            }
            pop_data_cc = {
                row['City']: row['Population']
                for _, row in df_cc.iterrows()
            }

            if years_cc:
                if not comparative_chart_html:
                    comparative_chart_html = create_interactive_comparative_chart(
                        df_cc, city_coords_cc, years_cc)
                if not graph_table_html:
                    graph_table_html = generate_graph_table(
                        df_cc, city_coords_cc, years_cc)
                if not years:
                    years = years_cc

            _build_population_map(city_coords_cc, pop_data_cc,
                                  'population_map_coords.html')
            _build_cancer_map(city_coords_cc, pop_data_cc, df_cc,
                              cancer_types_cc, years_cc,
                              'cancer_map_coords.html')
            generated_maps.append(('population_map_coords.html',
                                   'Population Distribution (City Coordinates Data)'))
            generated_maps.append(('cancer_map_coords.html',
                                   'Cancer Incidence Heatmap (City Coordinates Data)'))

        # ── Standard cancer CSV ─────────────────────────────────────────
        if os.path.exists(cancer_path):
            df = pd.read_csv(cancer_path)
            df.columns = df.columns.str.strip()
            years_std    = [col for col in df.columns if col.strip().isdigit()]
            cancer_types = [col for col in df.columns
                           if col not in ['City', 'State'] + years_std]

            display_cols = [c for c in df.columns
                            if c not in ('Population', 'Latitude', 'Longitude')]
            if not cancer_table_html:
                cancer_table_html = df[display_cols].to_html(
                    index=False, border=0, classes='cancer-csv-table')

            census_path = 'processed_census_data.csv'
            if not os.path.exists(census_path):
                census_path = os.path.join(UPLOAD_FOLDER, 'processed_census_data.csv')

            if os.path.exists(census_path) and years_std:
                census_data = pd.read_csv(census_path)
                merged = pd.merge(
                    df, census_data,
                    left_on=['City', 'State'],
                    right_on=['city', 'state_id'],
                    how='inner'
                )
                city_coords_std = {
                    row['City']: [row['lat'], row['lng']]
                    for _, row in merged.iterrows()
                }
                pop_data_std = {
                    row['City']: row['population']
                    for _, row in merged.iterrows()
                }

                if not comparative_chart_html:
                    comparative_chart_html = create_interactive_comparative_chart(
                        df, city_coords_std, years_std)
                if not graph_table_html:
                    graph_table_html = generate_graph_table(
                        df, city_coords_std, years_std)
                if not years:
                    years = years_std

                _build_population_map(city_coords_std, pop_data_std,
                                      'population_map_census.html')
                _build_cancer_map(city_coords_std, pop_data_std, df,
                                  cancer_types, years_std,
                                  'cancer_map_census.html')
                generated_maps.append(('population_map_census.html',
                                       'Population Distribution (Census Designated Places)'))
                generated_maps.append(('cancer_map_census.html',
                                       'Cancer Incidence Heatmap (Census Designated Places)'))

        # ── Demographic data ────────────────────────────────────────────
        if os.path.exists(county_race_path):
            county_race_data = pd.read_csv(county_race_path)
            county_race_data.columns = county_race_data.columns.str.strip()
            county_race_table_html = create_population_table(county_race_data)
            race_pie_html          = create_population_pie_chart(county_race_data)
            hispanic_pie_html      = create_hispanic_population_pie_chart(county_race_data)

        if os.path.exists(age_sex_path):
            age_sex_data = pd.read_csv(age_sex_path)
            age_sex_data.columns = age_sex_data.columns.str.strip()
            age_sex_table_html = create_age_sex_population_table(age_sex_data)
            age_pie_html       = create_age_pie_chart(age_sex_data)
            sex_pie_html       = create_sex_pie_chart(age_sex_data)

        # ----------------------------------------------------------------
        # Assemble output HTML
        # ----------------------------------------------------------------
        def iframe(src, height='500px'):
            return (f'<div style="height:{height}; border-radius:8px; overflow:hidden; '
                    f'border:2px solid #415a77;">'
                    f'<iframe src="{src}" style="width:100%;height:100%;border:none;"></iframe>'
                    f'</div>')

        section_style = ('margin-bottom:40px; background-color:#1b263b; padding:20px; '
                         'border-radius:8px; border:1px solid #415a77;')
        h2_style  = 'color:white; margin-top:0;'
        col_style = 'flex:1; min-width:300px;'

        body_sections = ''

        # -- Maps: render pairs side-by-side ----------------------------
        if generated_maps:
            for i in range(0, len(generated_maps), 2):
                pair = generated_maps[i:i + 2]
                body_sections += '<div style="display:flex; gap:20px; flex-wrap:wrap; margin-bottom:40px;">'
                for fname, title in pair:
                    if os.path.exists(fname):
                        body_sections += (f'<div style="{col_style}">'
                                          f'<div style="{section_style}">'
                                          f'<h2 style="{h2_style}">{title}</h2>'
                                          f'{iframe("/" + fname)}'
                                          f'</div></div>')
                body_sections += '</div>'

        # -- Cancer data table ------------------------------------------
        if cancer_table_html:
            body_sections += (f'<div style="{section_style}">'
                              f'<h2 style="{h2_style}">Cancer Data Table</h2>'
                              f'{cancer_table_html}'
                              f'</div>')

        # -- Comparative Plotly chart -----------------------------------
        if comparative_chart_html:
            body_sections += (f'<div style="{section_style}">'
                              f'<h2 style="{h2_style}">Interactive Comparative Cancer Trends</h2>'
                              f'{comparative_chart_html}'
                              f'</div>')

        # -- Standalone chart files from import_data --------------------
        chart_files = [
            ('cancer_trends.html',       'Cancer Trends Over Time'),
            ('cancer_distribution.html', 'Cancer Type Distribution'),
        ]
        existing_charts = [(f, t) for f, t in chart_files if os.path.exists(f)]
        for i in range(0, len(existing_charts), 2):
            body_sections += '<div style="display:flex; gap:20px; flex-wrap:wrap; margin-bottom:40px;">'
            for f, t in existing_charts[i:i+2]:
                body_sections += (f'<div style="{col_style}">'
                                  f'<div style="{section_style}">'
                                  f'<h2 style="{h2_style}">{t}</h2>'
                                  f'{iframe("/" + f)}'
                                  f'</div></div>')
            body_sections += '</div>'

        # -- Per-city graph grid ----------------------------------------
        if graph_table_html:
            body_sections += (f'<div style="{section_style}">'
                              f'<h2 style="{h2_style}">Individual Cancer Trends by City</h2>'
                              f'{graph_table_html}'
                              f'</div>')

        # -- County race table ------------------------------------------
        if county_race_table_html:
            body_sections += (f'<div style="{section_style}">'
                              f'<h2 style="{h2_style}">Race Population by County</h2>'
                              f'{county_race_table_html}'
                              f'</div>')

        # -- Race pie charts: side by side ------------------------------
        # FIX: wrapped in flex row instead of stacked vertically
        if race_pie_html or hispanic_pie_html:
            body_sections += (f'<div style="{section_style}">'
                              f'<h2 style="{h2_style}">Race Proportions</h2>'
                              f'<div style="display:flex; gap:20px; flex-wrap:wrap; align-items:flex-start;">'
                              f'<div style="flex:1; min-width:280px;">{race_pie_html}</div>'
                              f'<div style="flex:1; min-width:280px;">{hispanic_pie_html}</div>'
                              f'</div>'
                              f'</div>')

        # -- Age/sex table ----------------------------------------------
        if age_sex_table_html:
            body_sections += (f'<div style="{section_style}">'
                              f'<h2 style="{h2_style}">Population Data by Age and Sex</h2>'
                              f'{age_sex_table_html}'
                              f'</div>')

        # -- Age/sex pie charts: side by side ---------------------------
        # FIX: wrapped in flex row instead of stacked vertically
        if age_pie_html or sex_pie_html:
            body_sections += (f'<div style="{section_style}">'
                              f'<h2 style="{h2_style}">Age and Sex Proportions</h2>'
                              f'<div style="display:flex; gap:20px; flex-wrap:wrap; align-items:flex-start;">'
                              f'<div style="flex:1; min-width:280px;">{age_pie_html}</div>'
                              f'<div style="flex:1; min-width:280px;">{sex_pie_html}</div>'
                              f'</div>'
                              f'</div>')

        output_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cancer Data Visualization Report</title>
    <style>
        body {{
            font-family: 'Roboto', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #0d1b2a;
            color: #ffffff;
        }}
        .nav-buttons {{
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-bottom: 30px;
        }}
        .button {{
            background-color: #415a77;
            color: #ffffff;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            transition: background-color 0.3s ease;
            text-decoration: none;
            display: inline-block;
        }}
        .button:hover {{ background-color: #566c86; }}
        table.cancer-csv-table {{
            width: 100%;
            border-collapse: collapse;
        }}
        table.cancer-csv-table th {{
            background-color: #415a77;
            color: white;
            padding: 8px;
            border: 1px solid #415a77;
            text-align: center;
        }}
        table.cancer-csv-table td {{
            background-color: #1b263b;
            color: white;
            padding: 8px;
            border: 1px solid #415a77;
            text-align: center;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="nav-buttons">
        <a href="/" class="button">Home</a>
        <a href="/import" class="button">Import Data</a>
        <a href="/user-guide" class="button">User Guide</a>
        <a href="/about" class="button">About</a>
    </div>
    <h1 style="color:white; margin-bottom:30px;">Cancer Data Visualization Report</h1>
    {body_sections}
</body>
</html>"""

        with open('custom_cancer_map_v12_4.html', 'w') as fh:
            fh.write(output_html)

        return jsonify({'success': True, 'redirect': '/custom_cancer_map_v12_4.html'})

    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error generating visualization: {str(e)}'})


if __name__ == '__main__':
    app.run(debug=True)