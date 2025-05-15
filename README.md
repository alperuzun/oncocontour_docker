What This Tool Does

This web application helps researchers and health professionals visualize cancer statistics on interactive maps. Just upload your data files and the system will automatically:

Match your city/state data with map coordinates
Create color-coded heatmaps showing cancer rates
Generate population distribution maps
Produce demographic charts (if you upload that data)
Getting Started

What You'll Need

A computer with Python 3.7 or newer
The data files you want to visualize
Basic knowledge of CSV files
Setup Instructions

Download the software files
Get all the Python files (.py) from the project and save them in a new folder.
Get the city database
Download "uscities.csv" from simplemaps.com/data/us-cities
Save it in the same folder as the Python files.
Prepare the system
Open Command Prompt (Windows) or Terminal (Mac) and type:
pip install flask pandas folium plotly
python census_processor.py
Start the program
Type this command to launch the application:
python app.py
How To Use It

Open the website
After starting the program, open your web browser and go to:
http://localhost:5000
Prepare your data files
Your cancer data must be a CSV file with this exact format:
City,State,CancerType1,CancerType2,Year1,Year2,...
Providence,RI,11,50,40,30,47,45
State must use official 2-letter codes (RI, MA, CA, etc.)
Upload your files
Click "Import" at the top
Click "Choose File" under "Cancer Statistics Data"
Select your prepared CSV file
Click "Upload Cancer Data"
Create visualizations
Click the "Generate Visualization" button
Wait a moment while the system creates your maps
View your results
The system will show:
A population map (darker areas = more people)
A cancer incidence map (hotter colors = higher rates)
Additional charts if you uploaded demographic data
Troubleshooting Help

If something isn't working:

Check your CSV file format
First two columns must be "City,State" (exactly like that)
All states must use valid 2-letter codes
No blank rows at the top
Common error messages
"Processed census data not found":
Make sure you ran python census_processor.py and see the "setup" section above
"Invalid file format":
Check your CSV follows the exact required format
Blank or missing maps
The cities in your data must exist in the census database
Try larger cities first to test (they're more likely to be in the system)
Tips for Best Results

Start with a small test file (5-10 cities) to make sure everything works
The system automatically skips cities it can't find (no error messages)
For best maps, include at least 20-30 cities in your data
Chrome or Firefox work best for viewing the visualizations