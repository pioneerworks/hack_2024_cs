from dotenv import load_dotenv
from simple_salesforce import Salesforce
import pandas as pd
import re
from bs4 import BeautifulSoup
import os
import shutil
import glob
from pathlib import Path

# Get the project root (hack_2024_cs)
current_file = Path(__file__).resolve()
project_root = current_file.parents[2]  # Go up 3 levels from the current file

# Verify we're in the correct directory
if project_root.name != "hack_2024_cs":
    raise RuntimeError("Could not find hack_2024_cs project root")

# Load environment variables from project root
load_dotenv(project_root / ".env")

# Set working directory to script directory if needed
script_dir = current_file.parent
os.chdir(script_dir)

def move_to_obselete():
    """Move existing CSV files from results to obselete folder"""
    results_dir = os.path.join(script_dir, 'results')
    obselete_dir = os.path.join(results_dir, 'obselete')
    
    # Create obselete directory if it doesn't exist
    os.makedirs(obselete_dir, exist_ok=True)
    
    # Move existing CSV files to obselete
    for csv_file in glob.glob(os.path.join(results_dir, '*.csv')):
        if 'obselete' not in csv_file:
            try:
                shutil.move(csv_file, os.path.join(obselete_dir, os.path.basename(csv_file)))
                print(f"Moved {os.path.basename(csv_file)} to obselete folder")
            except Exception as e:
                print(f"Could not move {csv_file}: {str(e)}")

def get_latest_csv():
    """Get the most recent CSV file from the results directory"""
    results_dir = os.path.join(script_dir, 'results')
    csv_files = glob.glob(os.path.join(results_dir, '*.csv'))
    # Filter out files in obselete directory
    csv_files = [f for f in csv_files if 'obselete' not in f]
    
    if not csv_files:
        raise FileNotFoundError("No CSV files found in results directory")
    
    # Get the most recent file
    latest_file = max(csv_files, key=os.path.getctime)
    return latest_file

def strip_html(text):
    if pd.isna(text):
        return ""
    
    # First pass: Use BeautifulSoup to get text content
    soup = BeautifulSoup(text, 'html.parser')
    
    # Remove all images
    for img in soup.find_all('img'):
        img.decompose()
    
    # Replace list items with bullet points
    for li in soup.find_all('li'):
        li.insert_before('• ')
        li.unwrap()
    
    # Replace horizontal rules with dashes
    for hr in soup.find_all('hr'):
        hr.replace_with('\n---\n')
    
    # Add spacing around headers
    for header in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        header.insert_before('\n\n')
        header.insert_after('\n')
        header.unwrap()
    
    # Add newlines around paragraphs
    for p in soup.find_all('p'):
        p.insert_before('\n')
        p.insert_after('\n')
        p.unwrap()
    
    # Unwrap remaining tags but keep their content
    for tag in soup.find_all():
        tag.unwrap()
    
    # Get text content
    text = soup.get_text()
    
    # Clean up any remaining HTML and special characters
    text = re.sub(r'<[^>]+>', '', text)  # Remove any remaining HTML tags
    text = re.sub(r'&[a-zA-Z0-9#]+;', ' ', text)  # Remove HTML entities
    text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with single space
    text = re.sub(r'\n\s*\n', '\n\n', text)  # Clean up multiple newlines
    text = re.sub(r'•\s+', '• ', text)  # Clean up bullet points
    
    # Final cleanup of whitespace
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(line for line in lines if line)
    
    return text.strip()

def download_knowledge_data():
    print("Connecting to Salesforce...")
    sf_args = dict(
        username=os.environ['SALESFORCE_USERNAME'],
        consumer_key=os.environ['SALESFORCE_CONSUMER_KEY'],
        privatekey=os.environ['SALESFORCE_PRIVATE_KEY'],
        client_id=os.environ['SALESFORCE_CLIENT_ID'],
    )
    if os.environ['SALESFORCE_ENV'] != "production":
        sf_args["domain"] = "test"
    sf = Salesforce(**sf_args)

    print("Getting metadata...")
    account_metadata = sf.Knowledge__kav.describe()

    compound_field_names_set = set()
    for field in account_metadata['fields']:
        compound_field_name = field.get('compoundFieldName')
        if compound_field_name:
            compound_field_names_set.add(compound_field_name)
    compound_field_names_set.discard('Name')
    
    field_names = [field['name'] for field in account_metadata['fields'] 
                  if field['name'] not in compound_field_names_set]

    print("Downloading knowledge articles...")
    # query = f"SELECT {', '.join(field_names)} FROM Knowledge__kav"
    query = f"SELECT Id, ArticleNumber, Title, Article_Body__c, Knowledge_Article_URL__c FROM Knowledge__kav"
    results_dir = os.path.join(script_dir, 'results')
    sf.bulk2.Knowledge__kav.download(
        query, path=results_dir, max_records=10000000
    )
    print("Download complete!")

def process_knowledge_data():
    try:
        print("\nProcessing downloaded data...")
        # Read most recent CSV
        latest_csv = get_latest_csv()
        print(f"Reading file: {latest_csv}")
        df = pd.read_csv(latest_csv)
        
        # Clean the HTML content in Article_Body__c
        print("Cleaning HTML content...")
        df['Article_Body__c'] = df['Article_Body__c'].apply(strip_html)
        
        # Save results with all columns
        output_path = os.path.join(script_dir, 'results', 'processed_knowledge_data.csv')
        df.to_csv(output_path, index=False)
        print(f"Cleaned data saved to {output_path}")
        
        # Show sample
        print("\nFirst cleaned article sample:")
        print("-" * 50)
        print(f"Title: {df['Title'].iloc[0]}")
        print("-" * 50)
        print(df['Article_Body__c'].iloc[0])
        
    except Exception as e:
        print(f"Error during processing: {str(e)}")

def main():
    try:
        move_to_obselete()
        download_knowledge_data()
        process_knowledge_data()
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()