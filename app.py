from flask import Flask, request, jsonify, render_template_string, send_from_directory, make_response
import folium
from folium.plugins import HeatMap
import matplotlib.pyplot as plt
import pandas as pd
import plotly.graph_objs as go
import plotly.io as pio
import base64
from io import BytesIO
import os
import re
import cancermaps_v12_4 as custom_cancer_map

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

# Import page HTML content
import_page_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Import Data</title>
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
            <button class="button" onclick="navigateTo('/')">Home</button>
            <button class="button" onclick="navigateTo('/import')">Import</button>
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
    </div>

    <script>
        let uploadedFiles = {
            city: false,
            cancer: false,
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
            // Check if at least one file is uploaded
            const hasFiles = Object.values(uploadedFiles).some(value => value === true);
            
            if (!hasFiles) {
                alert('Please upload at least one data file before generating visualizations.');
                return;
            }
            
            fetch('/visualize')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Redirect to the visualization page
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
            <button class="button" onclick="navigateTo('/')">Home</button>
            <button class="button" onclick="navigateTo('/import')">Import Data</button>
        </div>
        
        <div class="logo-container">
            <img src="/OncoContour.png" alt="OncoContour Logo" class="logo">
            <p class="tagline">Geographic Visualization of Cancer Statistics</p>
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
            <p>© 2025 OncoContour - Geospatial Cancer Analytics</p>
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

# US state abbreviations for validation
US_STATES = {
    'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 
    'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 
    'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 
    'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 
    'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
}

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
        
        # Remove existing file if it exists
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception as e:
                print(f"Error removing existing file: {e}")
        
        try:
            # Save the file temporarily to read it
            temp_path = os.path.join(app.config['UPLOAD_FOLDER'], 'temp.csv')
            file.save(temp_path)
            
            # Read the CSV file
            df = pd.read_csv(temp_path)
            
            # Specific validation for cancer data
            if file_type == 'cancer':
                # Check required columns
                if len(df.columns) < 3:
                    os.remove(temp_path)
                    return jsonify({
                        'success': False,
                        'message': 'Cancer data must have at least City, State and one data column'
                    })
                
                # Check first two columns are City and State
                if df.columns[0].lower() != 'city' or df.columns[1].lower() != 'state':
                    os.remove(temp_path)
                    return jsonify({
                        'success': False,
                        'message': 'First two columns must be "City" and "State"'
                    })
                
                # Validate state abbreviations
                if not all(str(state).upper() in US_STATES for state in df.iloc[:, 1]):
                    os.remove(temp_path)
                    return jsonify({
                        'success': False,
                        'message': 'State column must contain valid 2-letter US state abbreviations'
                    })
                
                # Validate remaining columns are either cancer types or years
                for col in df.columns[2:]:
                    if not (str(col).isalpha() or str(col).isdigit()):
                        os.remove(temp_path)
                        return jsonify({
                            'success': False,
                            'message': f'Column "{col}" must be either a cancer type (text) or year (number)'
                        })
            
            # For other file types, keep existing validation
            elif file_type == 'countyRace':
                if df.columns[0] != 'County':
                    os.remove(temp_path)
                    return jsonify({
                        'success': False,
                        'message': 'First column must be "County"'
                    })
            elif file_type == 'ageSex':
                if df.columns[0] != 'Sex':
                    os.remove(temp_path)
                    return jsonify({
                        'success': False,
                        'message': 'First column must be "Sex"'
                    })
            
            # If validation passed, move the temp file to final location
            os.rename(temp_path, filepath)
            
            return jsonify({
                'success': True,
                'message': f'{file_type.capitalize()} data uploaded successfully'
            })
            
        except Exception as e:
            # Clean up temp file if it exists
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return jsonify({
                'success': False,
                'message': f'Error processing file: {str(e)}'
            })
    
    return jsonify({
        'success': False,
        'message': 'Invalid file format. Please upload a CSV file.'
    })

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
    try:
        # Check if at least one file exists in the upload folder
        uploaded_files = [f for f in os.listdir(UPLOAD_FOLDER) if f.endswith('.csv')]
        
        if not uploaded_files:
            return jsonify({
                'success': False,
                'message': 'No data files found. Please upload at least one file before generating visualizations.'
            })
        
        # Call the custom cancer map generator
        success = custom_cancer_map.generate_visualization(uploads_folder=UPLOAD_FOLDER)
        
        if success:
            # Return the path to the visualization as JSON
            return jsonify({
                'success': True,
                'redirect': '/custom_cancer_map_v12_4.html'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Error generating visualization. Please check that you have uploaded the necessary data files.'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error generating visualization: {str(e)}'
        })

if __name__ == '__main__':
    app.run(debug=True)
