import pandas as pd
import numpy as np
from typing import List
from sentence_transformers import SentenceTransformer
import torch
from tqdm import tqdm
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from llm.lib.data_preparation import get_project_root

class EmbeddingGenerator:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2', batch_size: int = 32):
        """
        Initialize the embedding generator.
        
        Args:
            model_name (str): Name of the Sentence Transformers model to use
            batch_size (int): Number of texts to process at once
        """
        self.batch_size = batch_size
        self.model = SentenceTransformer(model_name)
        self.project_root = get_project_root()
        
        # Use GPU if available
        if torch.cuda.is_available():
            self.model = self.model.to('cuda')
            print("Using GPU for embeddings")
        else:
            print("Using CPU for embeddings")

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings using Sentence Transformers.
        
        Args:
            texts (List[str]): List of texts to generate embeddings for
            
        Returns:
            List[List[float]]: List of embeddings
        """
        embeddings = []
        
        for i in tqdm(range(0, len(texts), self.batch_size), desc="Generating embeddings"):
            batch = texts[i:i + self.batch_size]
            try:
                with torch.no_grad():
                    batch_embeddings = self.model.encode(batch)
                    embeddings.extend(batch_embeddings.tolist())
            except Exception as e:
                print(f"Error generating embeddings for batch {i}: {e}")
                embeddings.extend([None] * len(batch))
        
        return embeddings

    def process_documents(self, input_path: str, output_path: str):
        """
        Process documents from CSV and save embeddings.
        
        Args:
            input_path (str): Path to input CSV file
            output_path (str): Path to save embeddings
        """
        # Load prepared documents
        print(f"Loading documents from {input_path}")
        df = pd.read_csv(input_path)
        
        # Generate embeddings for all texts
        embeddings = self.generate_embeddings(df['text'].tolist())
        
        # Add embeddings to dataframe
        df['embedding'] = embeddings
        
        # Save embeddings and metadata
        self.save_embeddings(df, output_path)
        print(f"Saved embeddings to {output_path}")

    def save_embeddings(self, df: pd.DataFrame, output_path: str):
        """
        Save embeddings and metadata to files.
        
        Args:
            df (pd.DataFrame): DataFrame with embeddings
            output_path (str): Base path for saving files
        """
        # Save embeddings as numpy array
        embeddings = np.array(df['embedding'].tolist())
        np.save(f"{output_path}_embeddings.npy", embeddings)
        
        # Save metadata without embeddings
        metadata = df.drop('embedding', axis=1)
        metadata.to_csv(f"{output_path}_metadata.csv", index=False)
        
        # Print some statistics
        print(f"Generated {len(embeddings)} embeddings")
        print(f"Embedding dimension: {embeddings.shape[1]}")

def main():
    """
    Main function to run the embedding generation process.
    """
    # Initialize embedding generator
    generator = EmbeddingGenerator(
        model_name='all-MiniLM-L6-v2',  # You can change this to other models
        batch_size=32
    )
    
    # Process documents using relative paths
    generator.process_documents(
        input_path=f"{generator.project_root}/llm/data/prepared_docs.csv",
        output_path=f"{generator.project_root}/llm/data/embeddings"
    )

if __name__ == "__main__":
    main()