<img src="https://github.com/alperuzun/cancermaps/blob/main/OncoContour.png" alt="Page 1 Image" height= 150 align = "center" >



# OncoContour

We present OncoContour: a geographic cancer data visualization platform. OncoContour analyzes and maps cancer incidence data across regions to reveal spatial patterns and demographic correlations. This provides researchers and public health professionals with actionable insights to inform policy decisions and targeted interventions. The platform offers interactive heatmaps, demographic breakdowns, temporal trend visualizations, and comparative analyses.

## Table of Contents

- [Installation](#installation)
  - [Application Download](#application-download)
  - [Setup](#setup)
- [Getting Started](#getting-started)
  - [Running the Application](#running-the-application)
  - [Data Formats](#data-formats)
- [Navigation](#navigation)
  - [Uploading Data](#uploading-data)
  - [Generating Visualizations](#generating-visualizations)
  - [Exploring Results](#exploring-results)
- [Authors](#authors)
- [Contact](#contact)

## Installation

### Application Download

To install OncoContour, clone the repository:
1. Click the green "Code" button 
2. From the dropdown menu, click "Download ZIP"
3. Go to your Downloads folder, find the file named cancermaps-main.zip 
(if it appears as a folder instead of a ZIP, move to Setup)
4. Double-click it to unzip the files.
5. A new folder named cancermaps-main will appear — this is the main project folder.

git clone https://github.com/alperuzun/cancermaps.git

### Setup

1. Ensure you have Python 3.8+ installed (verify by typing python --version and 
pressing enter in Terminal)
2. Navigate to the project directory using Terminal, type "cd ", then drag and
drop the cancermaps-main folder into the Terminal window and press enter
3. Install required dependencies: type "pip install -r requirements.txt" into 
Terminal, then press enter
4. Start the application: type "python3 app.py" into Terminal, then press enter
5. You should see something similar to "* Running on http://127.0.0.1:5000"
6. Copy the "http://127.0.0.1:5000" portion and paste it into the search bar
of any web browser (Safari, Google Chrome, etc.)
7. Now you are all set! The application should appear.

## Getting Started

### Data Formats

Follow the instructions for uploading files in the 'Import' section.
Feel free to reference mock data that is included in the repository to 
understand proper formatting.

## Navigation

### Uploading Data

1. Click "Import Data" from the home screen
2. Select file type (Cancer, Demographics, or Age/Sex)
3. Choose your CSV file and click "Upload"
4. Click "Generate Visualization" when ready

### Generating Visualizations

OncoContour automatically generates:

Geographic heatmaps
Demographic breakdowns
Temporal trend analyses
Comparative visualizations

### Exploring Results

Interactive features include:

Hover for detailed statistics
Click to filter data
Navigation between views
Data/image downloads

## Authors

This project was developed by Alper Uzun and Daniel White at The Warren Alpert 
Medical School of Brown University.

## Contact

For questions or support, please contact:
- Dr. Alper Uzun (alper_uzun@brown.edu)
- Daniel White (daniel_white@brown.edu)

Visit our lab website: https://sites.brown.edu/gmilab/