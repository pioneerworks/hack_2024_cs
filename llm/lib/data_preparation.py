import pandas as pd
import re
from typing import List, Dict
import numpy as np
import os
from dotenv import load_dotenv


def get_project_root():
    """Get the project root directory from PYTHONPATH"""
    load_dotenv()
    python_path = os.getenv('PYTHONPATH')
    if not python_path:
        raise ValueError("PYTHONPATH not set in .env file")
    return python_path

class DataPreparator:
    def __init__(self, chunk_size: int = 1000):
        """
        Initialize the DataPreparator with configurable chunk size.
        Args:
            chunk_size (int): Maximum number of characters per chunk
        """
        self.chunk_size = chunk_size
        self.project_root = get_project_root()

    def load_data(self, file_path: str) -> pd.DataFrame:
        """
        Load data from CSV file.
        Args:
            file_path (str): Path to the CSV file
        Returns:
            pd.DataFrame: Loaded and basic-cleaned dataframe
        """
        df = pd.read_csv(file_path)
        # Remove any rows where essential columns are null
        df = df.dropna(subset=['Title', 'Article_Body__c'])
        return df

    def clean_text(self, text: str) -> str:
        """
        Clean text by removing special characters and extra whitespace.
        Args:
            text (str): Input text to clean
        Returns:
            str: Cleaned text
        """
        if pd.isna(text):
            return ""
        # Remove special characters but keep periods and basic punctuation
        text = re.sub(r'[^\w\s.,!?-]', ' ', str(text))
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove extra periods
        text = re.sub(r'\.+', '.', text)
        return text.strip()

    def create_chunks(self, text: str) -> List[str]:
        """
        Split text into chunks of approximately equal size.
        Args:
            text (str): Text to split into chunks
        Returns:
            List[str]: List of text chunks
        """
        chunks = []
        current_chunk = ""
        # Split by sentences to maintain context
        sentences = re.split(r'(?<=[.!?])\s+', text)
        for sentence in sentences:
            if len(current_chunk) + len(sentence) < self.chunk_size:
                current_chunk += " " + sentence if current_chunk else sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
        if current_chunk:
            chunks.append(current_chunk.strip())
        return chunks

    def prepare_data(self, file_path: str) -> List[Dict]:
        """
        Main method to prepare data for embedding.
        Args:
            file_path (str): Path to the CSV file
        Returns:
            List[Dict]: List of prepared documents with metadata
        """
        # Load data
        df = self.load_data(file_path)
        prepared_docs = []
        for _, row in df.iterrows():
            # Combine title and body
            full_text = f"{row['Title']}\n\n{row['Article_Body__c']}"
            cleaned_text = self.clean_text(full_text)
            # Create chunks
            chunks = self.create_chunks(cleaned_text)
            # Create document for each chunk
            for i, chunk in enumerate(chunks):
                doc = {
                    'id': f"{row['Id']}_{i}",
                    'article_id': row['Id'],
                    'article_number': row['ArticleNumber'],
                    'title': row['Title'],
                    'url': row['Knowledge_Article_URL__c'],
                    'chunk_index': i,
                    'total_chunks': len(chunks),
                    'text': chunk
                }
                prepared_docs.append(doc)
        return prepared_docs

def main():
    """
    Main function to run the data preparation process.
    """
    preparator = DataPreparator(chunk_size=1000)
    prepared_docs = preparator.prepare_data(f"{preparator.project_root}/data_sources/salesforce_kb_download/results/processed_knowledge_data.csv")
    print(f"Total documents prepared: {len(prepared_docs)}")
    print(f"Average chunk length: {np.mean([len(doc['text']) for doc in prepared_docs]):.2f} characters")
    output_df = pd.DataFrame(prepared_docs)
    output_df.to_csv(f'{preparator.project_root}/llm/data/prepared_docs.csv', index=False)

if __name__ == "__main__":
    main()
