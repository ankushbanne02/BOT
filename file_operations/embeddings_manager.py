import os
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Tuple
from tqdm import tqdm

class EmbeddingsManager:
    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.index = None
        self.paths = []
        self.index_file = "path_index.faiss"
        self.paths_file = "path_list.json"
        self.batch_size = 10000  # Process 10k paths at a time

    def create_embeddings(self, directory_tree: Dict) -> None:
        """Create embeddings for all paths in the directory tree"""
        print("🔄 Creating embeddings for directory structure...")
        
        # Extract all paths from the directory tree
        self.paths = []
        for drive, tree in directory_tree.items():
            for path, content in tree.items():
                # Add the drive path
                full_path = os.path.join(drive, path)
                self.paths.append(full_path)
                
                # Add all subdirectories
                for dir_name in content["dirs"]:
                    dir_path = os.path.join(full_path, dir_name)
                    self.paths.append(dir_path)
                
                # Add all files
                for file_name in content["files"]:
                    file_path = os.path.join(full_path, file_name)
                    self.paths.append(file_path)

        print(f"✅ Found {len(self.paths)} paths. Generating embeddings...")
        
        # Process paths in batches
        all_embeddings = []
        for i in tqdm(range(0, len(self.paths), self.batch_size), desc="Generating embeddings"):
            batch_paths = self.paths[i:i + self.batch_size]
            batch_embeddings = self.model.encode(batch_paths)
            all_embeddings.append(batch_embeddings)
        
        # Combine all embeddings
        path_embeddings = np.vstack(all_embeddings)
        
        # Create and save FAISS index
        dimension = path_embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(path_embeddings.astype('float32'))
        
        # Save index and paths
        faiss.write_index(self.index, self.index_file)
        with open(self.paths_file, 'w', encoding='utf-8') as f:
            json.dump(self.paths, f, indent=2)
        
        print("✅ Embeddings saved successfully!")

    def load_embeddings(self) -> bool:
        """Load existing embeddings from disk"""
        try:
            if os.path.exists(self.index_file) and os.path.exists(self.paths_file):
                self.index = faiss.read_index(self.index_file)
                with open(self.paths_file, 'r', encoding='utf-8') as f:
                    self.paths = json.load(f)
                print("✅ Loaded existing embeddings")
                return True
            return False
        except Exception as e:
            print(f"Error loading embeddings: {e}")
            return False

    def search_paths(self, query: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """Search for paths similar to the query"""
        if self.index is None:
            if not self.load_embeddings():
                print("⚠️ No embeddings found. Please create embeddings first.")
                return []

        # Generate embedding for the query
        query_embedding = self.model.encode([query]).astype('float32')
        
        # Search the index
        distances, indices = self.index.search(query_embedding, top_k)
        
        # Return results with paths and distances
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx < len(self.paths):  # Ensure valid index
                results.append((self.paths[idx], float(distance)))
        
        return results

    def update_embeddings(self, new_paths: List[str]) -> None:
        """Update embeddings with new paths"""
        if self.index is None:
            if not self.load_embeddings():
                print("⚠️ No existing embeddings found. Creating new ones...")
                return

        # Generate embeddings for new paths in batches
        new_embeddings = []
        for i in tqdm(range(0, len(new_paths), self.batch_size), desc="Generating new embeddings"):
            batch_paths = new_paths[i:i + self.batch_size]
            batch_embeddings = self.model.encode(batch_paths)
            new_embeddings.append(batch_embeddings)
        
        # Combine new embeddings
        new_embeddings = np.vstack(new_embeddings)
        
        # Add new embeddings to the index
        self.index.add(new_embeddings.astype('float32'))
        
        # Update paths list
        self.paths.extend(new_paths)
        
        # Save updated index and paths
        faiss.write_index(self.index, self.index_file)
        with open(self.paths_file, 'w', encoding='utf-8') as f:
            json.dump(self.paths, f, indent=2)
        
        print("✅ Updated embeddings with new paths")