"""
Pinecone vector store implementation for CodeRAG.

This module provides a Pinecone-based vector store implementation that follows
the VectorStore interface.
"""

from typing import List, Dict, Any, Optional
from pinecone import Pinecone, ServerlessSpec
from .base import VectorStore

class PineconeStore(VectorStore):
    """
    Pinecone-based vector store implementation.
    
    This class implements the VectorStore interface using Pinecone as the backend.
    It handles initialization, adding embeddings, and searching for similar vectors.
    
    Attributes:
        index: Pinecone index instance
        namespace: Optional namespace for the vectors
    """
    
    def __init__(self,
                 api_key: str,
                 index_name: str,
                 cloud: str = "aws",
                 region: str = "us-east-1",
                 namespace: Optional[str] = None,
                 dimension: Optional[int] = None):
        """
        Initialize the Pinecone vector store.
        
        Args:
            api_key: Pinecone API key
            index_name: Name of the Pinecone index
            namespace: Optional namespace for vectors
            dimension: Optional dimension override (if None, will be determined from first batch)
        """
        # Initialize Pinecone with new API
        self.pc = Pinecone(api_key=api_key)
        self.index_name = index_name
        self.namespace = namespace
        self.dimension = dimension
        self.cloud = cloud        # Store cloud parameter
        self.region = region      # Store region parameter
        self.index = None  # Will be initialized when dimension is known
    
    def _init_index(self, dimension: int):
        """Initialize the Pinecone index with the given dimension."""
        try:
            # Try to get existing index
            self.index = self.pc.Index(self.index_name)
            self.dimension = dimension
        except Exception:
            # Create new index if it doesn't exist
            self.pc.create_index(
                name=self.index_name,
                dimension=dimension,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud=self.cloud,
                    region=self.region
                )
            )
            self.index = self.pc.Index(self.index_name)
            self.dimension = dimension
    
    def add_embeddings(self, embeddings: List[List[float]], metadata: List[Dict[str, Any]]):
        """
        Add embeddings with metadata to the vector store.
        
        Args:
            embeddings: List of embedding vectors
            metadata: List of metadata dictionaries
        """
        if not embeddings:
            return
        
        # Initialize index if not already done
        if self.index is None:
            self._init_index(len(embeddings[0]))
        
        # Prepare vectors for upsert
        vectors = []
        for i, (embedding, meta) in enumerate(zip(embeddings, metadata)):
            vector_id = meta.get('id', str(i))
            vectors.append((vector_id, embedding, meta))
        
        # Upsert vectors in batches
        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i + batch_size]
            try:
                self.index.upsert(
                    vectors=batch,
                    namespace=self.namespace
                )
            except Exception as e:
                raise
    
    def search(self,
               query_embedding: Optional[List[float]],
               top_k: int = 5,
               filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search for similar vectors.
        
        Args:
            query_embedding: Query vector to search for
            top_k: Number of results to return
            filter: Optional metadata filter
            
        Returns:
            List of dictionaries containing search results with scores and metadata
        """
        try:
            # Initialize index with default dimension if not initialized
            if self.index is None:
                self._init_index(len(query_embedding))
            
            # Perform search
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                namespace=self.namespace,
                filter=filter,
                include_metadata=True
            )
            
            # Format results
            formatted_results = []
            for match in results.matches:
                result = {
                    "id": match.id,
                    "score": match.score,
                    "metadata": match.metadata
                }
                formatted_results.append(result)
            
            return formatted_results
            
        except Exception as e:
            raise

    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store.
        
        Returns:
            Dictionary containing collection statistics
        """
        try:
            # Initialize index with default dimension if not initialized
            if self.index is None:
                self._init_index(384)  # Default dimension
            
            stats = self.index.describe_index_stats()
            return {
                "total_vectors": stats["total_vector_count"],
                "dimension": stats["dimension"],
                "namespaces": stats["namespaces"]
            }
        except Exception as e:
            return {
                "error": str(e),
                "total_vectors": 0,
                "dimension": self.dimension or 384,
                "namespaces": {}
            } 