# census_processor.py
import csv

def process_census_data(input_csv_path, output_csv_path):
    """
    Processes the uscities.csv file to extract only the necessary columns:
    city, state_id, county_name, lat, lng, population.
    
    Args:
        input_csv_path (str): Path to the original uscities.csv file.
        output_csv_path (str): Path where the processed data will be saved.
    """
    required_columns = ['city', 'state_id', 'county_name', 'lat', 'lng', 'population']
    
    with open(input_csv_path, mode='r', encoding='utf-8') as infile, \
         open(output_csv_path, mode='w', encoding='utf-8', newline='') as outfile:
        
        reader = csv.DictReader(infile)
        writer = csv.DictWriter(outfile, fieldnames=required_columns)
        
        writer.writeheader()
        
        for row in reader:
            # Extract only the required columns
            processed_row = {col: row[col] for col in required_columns}
            writer.writerow(processed_row)

# Example usage:
if __name__ == "__main__":
    process_census_data('uscities.csv', 'processed_census_data.csv')