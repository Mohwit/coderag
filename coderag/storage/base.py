"""
Base vector storage module for CodeRAG.

This module defines the abstract base class for all vector storage implementations,
providing a common interface for adding, searching, and managing code embeddings.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class VectorStore(ABC):
    """
    Abstract base class for vector storage implementations.
    
    This class defines the interface that all vector storage implementations must follow.
    It provides methods for adding embeddings, searching for similar embeddings, and
    managing the vector database.
    
    Implementations should handle the specifics of different vector database backends
    while conforming to this interface.
    """
    
    @abstractmethod
    def __init__(self, **kwargs):
        """
        Initialize the vector store with configuration.
        
        Args:
            **kwargs: Implementation-specific configuration options
        """
        pass
    
    @abstractmethod
    def add_embeddings(self, 
                      embeddings: List[List[float]], 
                      metadata: List[Dict[str, Any]], 
                      ids: Optional[List[str]] = None) -> None:
        """
        Add embeddings to the vector store.
        
        This method stores embedding vectors along with their associated metadata.
        Each embedding represents a code chunk from the repository.
        
        Args:
            embeddings: List of embedding vectors
            metadata: List of metadata dictionaries for each embedding
            ids: Optional list of IDs for the embeddings (auto-generated if not provided)
        
        Raises:
            Exception: If there's an error adding the embeddings to the store
        """
        pass
    
    @abstractmethod
    def search(self, 
               query_embedding: Optional[List[float]], 
               top_k: int = 5, 
               filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search for similar vectors in the store or by ID.
        
        This method finds the closest embeddings to the query embedding based on
        vector similarity (typically cosine similarity). If query_embedding is None
        and filter contains an ID, it will search by ID instead.
        
        Args:
            query_embedding: Query vector to search for, or None for ID-based search
            top_k: Number of results to return
            filter: Optional metadata filter to narrow down search
            
        Returns:
            List of dictionaries containing search results with scores and metadata
            
        Raises:
            Exception: If there's an error searching the vector store
        """
        pass
    
    @abstractmethod
    def delete(self, ids: List[str]) -> None:
        """
        Delete embeddings from the store.
        
        This method removes embeddings with the specified IDs from the vector store.
        
        Args:
            ids: List of IDs to delete
            
        Raises:
            Exception: If there's an error deleting the embeddings
        """
        pass
    
    @abstractmethod
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store collection.
        
        Returns:
            Dictionary containing collection statistics (count, dimensions, etc.)
            
        Raises:
            Exception: If there's an error retrieving the statistics
        """
        pass 