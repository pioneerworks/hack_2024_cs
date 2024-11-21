import faiss
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from llm.lib.data_preparation import get_project_root

class VectorStore:
    def __init__(self):
        """
        Initialize the vector store using FAISS.
        """
        self.index = None
        self.metadata = None
        self.dimension = None
        self.project_root = get_project_root()

    def create_index(self, embeddings: np.ndarray, metadata_df: pd.DataFrame):
        """
        Create a FAISS index from embeddings.
        
        Args:
            embeddings (np.ndarray): Matrix of embeddings
            metadata_df (pd.DataFrame): DataFrame containing metadata
        """
        self.dimension = embeddings.shape[1]
        
        # Create FAISS index
        self.index = faiss.IndexFlatL2(self.dimension)
        
        # Add vectors to the index
        self.index = faiss.IndexIDMap(self.index)
        
        # Convert IDs to integers for FAISS
        ids = np.arange(len(embeddings))
        
        # Add vectors to the index
        self.index.add_with_ids(embeddings.astype('float32'), ids)
        
        # Store metadata
        self.metadata = metadata_df
        
        print(f"Created index with {len(embeddings)} vectors of dimension {self.dimension}")

    def save(self, base_path: str):
        """
        Save the FAISS index and metadata to disk.
        
        Args:
            base_path (str): Base path for saving files
        """
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(base_path), exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, f"{base_path}_index.faiss")
        
        # Save metadata
        self.metadata.to_csv(f"{base_path}_metadata.csv", index=False)
        
        print(f"Saved index and metadata to {base_path}")

    def load(self, base_path: str):
        """
        Load the FAISS index and metadata from disk.
        
        Args:
            base_path (str): Base path for loading files
        """
        # Load FAISS index
        self.index = faiss.read_index(f"{base_path}_index.faiss")
        
        # Load metadata
        self.metadata = pd.read_csv(f"{base_path}_metadata.csv")
        
        # Set dimension
        self.dimension = self.index.d
        
        print(f"Loaded index with {self.index.ntotal} vectors of dimension {self.dimension}")

    def search(self, query_vector: np.ndarray, k: int = 5) -> Tuple[np.ndarray, np.ndarray]:
        """
        Search for similar vectors in the index.
        
        Args:
            query_vector (np.ndarray): Query vector
            k (int): Number of results to return
            
        Returns:
            Tuple[np.ndarray, np.ndarray]: Distances and indices of nearest neighbors
        """
        if self.index is None:
            raise ValueError("Index not initialized. Please create or load an index first.")
        
        # Reshape query vector if necessary
        if len(query_vector.shape) == 1:
            query_vector = query_vector.reshape(1, -1)
        
        # Search the index
        distances, indices = self.index.search(query_vector.astype('float32'), k)
        
        return distances, indices

    def get_metadata(self, indices: np.ndarray) -> List[Dict]:
        """
        Get metadata for given indices.
        
        Args:
            indices (np.ndarray): Array of indices
            
        Returns:
            List[Dict]: List of metadata dictionaries
        """
        return [self.metadata.iloc[idx].to_dict() for idx in indices[0]]

def main():
    """
    Main function to create and save the vector store.
    """
    # Initialize vector store
    vector_store = VectorStore()
    
    # Load embeddings and metadata
    embeddings = np.load(f"{vector_store.project_root}/llm/data/embeddings_embeddings.npy")
    metadata_df = pd.read_csv(f"{vector_store.project_root}/llm/data/embeddings_metadata.csv")
    
    # Create index
    vector_store.create_index(embeddings, metadata_df)
    
    # Save to disk
    vector_store.save(f"{vector_store.project_root}/llm/data/vector_store")
    
    # Test search functionality
    print("\nTesting search functionality...")
    test_vector = embeddings[0]  # Use first vector as test query
    distances, indices = vector_store.search(test_vector, k=3)
    
    print("\nTop 3 similar documents:")
    results = vector_store.get_metadata(indices)
    for i, result in enumerate(results):
        print(f"\nResult {i+1} (distance: {distances[0][i]:.4f}):")
        print(f"Title: {result['title']}")
        print(f"Text: {result['text'][:100]}...")

if __name__ == "__main__":
    main()