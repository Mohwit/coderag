"""
Pinecone vector store implementation for CodeRAG.

This module provides a Pinecone-based vector store implementation that follows
the VectorStore interface.
"""

from typing import List, Dict, Any, Optional
import logging
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
        logging.info(f"Initializing Pinecone store with index: {index_name}")
        
        # Initialize Pinecone with new API
        self.pc = Pinecone(api_key=api_key)
        self.index_name = index_name
        self.namespace = namespace
        self.dimension = dimension
        self.cloud = cloud        # Store cloud parameter
        self.region = region      # Store region parameter
        self.index = None  # Will be initialized when dimension is known
    
    def _init_index(self, dimension: int):
        """Initialize index with correct dimension."""
        if self.index is None:
            # Create index if it doesn't exist
            if self.index_name not in self.pc.list_indexes().names():
                self.pc.create_index(
                    name=self.index_name,
                    dimension=dimension,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud=self.cloud,
                        region=self.region
                    )
                )
                logging.info(f"Created new Pinecone index: {self.index_name} with dimension {dimension}")
            
            self.index = self.pc.Index(self.index_name)
            self.dimension = dimension
    
    def add_embeddings(self,
                      embeddings: List[List[float]],
                      metadata: List[Dict[str, Any]],
                      batch_size: int = 100) -> None:
        """
        Add embeddings and their metadata to the store.
        
        Args:
            embeddings: List of embedding vectors
            metadata: List of metadata dictionaries
            batch_size: Number of vectors to upsert in each batch
        """
        if not embeddings:
            return
            
        # Initialize index with correct dimension from first embedding
        if self.index is None:
            embedding_dim = len(embeddings[0])
            self._init_index(embedding_dim)
            
        # Verify dimensions match
        if len(embeddings[0]) != self.dimension:
            raise ValueError(
                f"Embedding dimension {len(embeddings[0])} does not match index dimension {self.dimension}"
            )
        
        logging.info(f"Adding {len(embeddings)} embeddings to Pinecone")
        
        # Process in batches
        for i in range(0, len(embeddings), batch_size):
            batch_embeddings = embeddings[i:i + batch_size]
            batch_metadata = metadata[i:i + batch_size]
            
            vectors = [
                (str(j + i), emb, meta)
                for j, (emb, meta) in enumerate(zip(batch_embeddings, batch_metadata))
            ]
            
            try:
                self.index.upsert(
                    vectors=vectors,
                    namespace=self.namespace
                )
                logging.debug(f"Successfully added batch of {len(vectors)} vectors")
            except Exception as e:
                logging.error(f"Error adding batch to Pinecone: {e}")
                raise
    
    def delete(self, ids: List[str]) -> None:
        """
        Delete vectors by their IDs.
        
        Args:
            ids: List of vector IDs to delete
        """
        try:
            self.index.delete(
                ids=ids,
                namespace=self.namespace
            )
            logging.info(f"Successfully deleted {len(ids)} vectors")
        except Exception as e:
            logging.error(f"Error deleting vectors from Pinecone: {e}")
            raise

    def search(self,
               query_embedding: Optional[List[float]],
               top_k: int = 5,
               filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search for similar vectors.
        
        Args:
            query_embedding: Query vector to search with, or None for metadata-only search
            top_k: Number of results to return
            filter: Optional metadata filter
            
        Returns:
            List of dictionaries containing search results with scores and metadata
        """
        if query_embedding is None and filter is None:
            raise ValueError("Either query_embedding or filter must be provided")
        
        try:
            # Initialize index if not done yet
            if self.index is None:
                if query_embedding is not None:
                    self._init_index(len(query_embedding))
                else:
                    # For metadata-only search, use default dimension
                    self._init_index(384)  # Default dimension for most models
            
            if query_embedding is None:
                # Metadata-only search
                results = self.index.query(
                    vector=[0] * self.dimension,  # Use stored dimension
                    top_k=top_k,
                    filter=filter,
                    namespace=self.namespace,
                    include_metadata=True
                )
            else:
                # Vector similarity search
                results = self.index.query(
                    vector=query_embedding,
                    top_k=top_k,
                    filter=filter,
                    namespace=self.namespace,
                    include_metadata=True
                )
            
            # Format results to match VectorStore interface
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
            logging.error(f"Error searching Pinecone: {e}")
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
            logging.error(f"Error getting Pinecone stats: {e}")
            return {
                "error": str(e),
                "total_vectors": 0,
                "dimension": self.dimension or 384,
                "namespaces": {}
            } 