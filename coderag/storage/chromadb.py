"""
ChromaDB vector store implementation for CodeRAG.

This module provides a ChromaDB-based implementation of the VectorStore interface,
allowing code embeddings to be stored and queried using ChromaDB.
"""

import chromadb
from typing import List, Dict, Any, Optional
import uuid
from pathlib import Path
import os

from .base import VectorStore
from ..config import DEFAULT_COLLECTION_NAME, DEFAULT_VECTOR_STORE_DIR

class ChromaDBStore(VectorStore):
    """
    ChromaDB implementation of the vector store.
    
    This class provides a ChromaDB-based implementation for storing and retrieving
    code embeddings. It supports persistent storage and filtering based on metadata.
    
    Attributes:
        client: The ChromaDB client
        collection: The ChromaDB collection for storing embeddings
    """
    
    def __init__(self, 
                 collection_name: str = DEFAULT_COLLECTION_NAME,
                 persist_directory: Optional[str] = DEFAULT_VECTOR_STORE_DIR,
                 **kwargs):
        """
        Initialize ChromaDB store.
        
        Args:
            collection_name: Name of the collection to use
            persist_directory: Directory to persist the database.
                              If None, an in-memory database is used.
            **kwargs: Additional arguments passed to ChromaDB client
        """
        # Create the persistence directory if it doesn't exist
        if persist_directory:
            os.makedirs(persist_directory, exist_ok=True)
            self.client = chromadb.PersistentClient(path=persist_directory)
        else:
            self.client = chromadb.Client()
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}  # Using cosine similarity
        )
    
    def add_embeddings(self,
                      embeddings: List[List[float]],
                      metadata: List[Dict[str, Any]],
                      ids: Optional[List[str]] = None) -> None:
        """
        Add embeddings to ChromaDB.
        
        Args:
            embeddings: List of embedding vectors
            metadata: List of metadata dictionaries
            ids: Optional list of IDs for the embeddings
            
        Raises:
            Exception: If there's an error adding embeddings to ChromaDB
        """
        if ids is None:
            # Generate UUIDs if no IDs provided
            ids = [str(uuid.uuid4()) for _ in range(len(embeddings))]
        
        # Extract code/summary content and sanitize metadata
        documents = []
        sanitized_metadata = []
        
        for meta in metadata:
            # Get the content (either code or summary)
            if 'summary' in meta:
                # If summary exists, use it as the document
                documents.append(meta['summary'])
            else:
                # Otherwise use the raw code
                documents.append(meta['content'])
            
            # Sanitize metadata to ensure ChromaDB compatibility
            sanitized = {
                'file_path': str(meta.get('file_path', '')),
                'language': str(meta.get('language', '')),
                'type': str(meta.get('type', '')),
                'name': str(meta.get('name', '')),
                'start_line': str(meta.get('start_line', '')),
                'end_line': str(meta.get('end_line', '')),
                'docstring': str(meta.get('docstring', '')),
                'parameters': str(meta.get('parameters', '')),
                'content': str(meta.get('content', '')),  # Original code
            }
            
            # Add summary if it exists
            if 'summary' in meta:
                sanitized['summary'] = str(meta['summary'])
            
            sanitized_metadata.append(sanitized)
        
        # Add embeddings in batches to avoid memory issues
        batch_size = 100
        for i in range(0, len(embeddings), batch_size):
            batch_end = min(i + batch_size, len(embeddings))
            try:
                self.collection.add(
                    embeddings=embeddings[i:batch_end],
                    documents=documents[i:batch_end],
                    metadatas=sanitized_metadata[i:batch_end],
                    ids=ids[i:batch_end]
                )
            except Exception as e:
                raise
    
    def search(self,
               query_embedding: Optional[List[float]],
               top_k: int = 5,
               filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search for similar vectors in ChromaDB or by ID.
        
        Args:
            query_embedding: Query vector to search for, or None for ID-based search
            top_k: Number of results to return
            filter: Optional metadata filter (e.g., {"language": "python"})
            
        Returns:
            List of dictionaries containing search results with scores and metadata
            
        Raises:
            Exception: If there's an error searching ChromaDB
        """
        try:
            # Determine if this is a search by ID
            search_by_id = query_embedding is None and filter is not None and 'id' in filter
            
            if search_by_id:
                # Search by ID
                # Convert filter format to ChromaDB where clause
                where_filter = {"id": filter['id']}
                
                # Use get instead of query for exact ID match
                try:
                    # Note: get() takes a list of IDs
                    items = self.collection.get(
                        ids=[filter['id']],
                        include=['metadatas', 'documents']
                    )
                    
                    if not items['ids']:
                        return []  # ID not found
                    
                    # Format the result similar to query() results
                    formatted_results = []
                    for idx, (id_, metadata, document) in enumerate(zip(
                        items['ids'],
                        items['metadatas'],
                        items['documents']
                    )):
                        # Include both code and summary in results if available
                        result_metadata = {
                            'file_path': metadata['file_path'],
                            'language': metadata['language'],
                            'type': metadata['type'],
                            'name': metadata['name'],
                            'start_line': metadata['start_line'],
                            'end_line': metadata['end_line'],
                            'docstring': metadata['docstring'],
                            'parameters': metadata['parameters'],
                            'content': metadata['content'],  # Original code
                        }
                        
                        # Add summary if it exists
                        if 'summary' in metadata:
                            result_metadata['summary'] = metadata['summary']
                        
                        # Add hierarchical metadata if it exists
                        if 'level' in metadata:
                            result_metadata['level'] = metadata['level']
                        if 'parent' in metadata:
                            result_metadata['parent'] = metadata['parent']
                        if 'children' in metadata:
                            result_metadata['children'] = metadata['children']
                        
                        formatted_results.append({
                            'id': id_,
                            'score': 1.0,  # Perfect match for ID search
                            'metadata': result_metadata
                        })
                    
                    return formatted_results
                    
                except Exception as e:
                    return []
            else:
                # Regular vector similarity search
                if query_embedding is None:
                    raise ValueError("Query embedding cannot be None for similarity search")
                    
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k,
                    where=filter,
                    include=['metadatas', 'distances', 'documents']
                )
                
                formatted_results = []
                for idx, (id_, distance, metadata, document) in enumerate(zip(
                    results['ids'][0],
                    results['distances'][0],
                    results['metadatas'][0],
                    results['documents'][0]
                )):
                    # Include both code and summary in results if available
                    result_metadata = {
                        'file_path': metadata['file_path'],
                        'language': metadata['language'],
                        'type': metadata['type'],
                        'name': metadata['name'],
                        'start_line': metadata['start_line'],
                        'end_line': metadata['end_line'],
                        'docstring': metadata['docstring'],
                        'parameters': metadata['parameters'],
                        'content': metadata['content'],  # Original code
                    }
                    
                    # Add summary if it exists
                    if 'summary' in metadata:
                        result_metadata['summary'] = metadata['summary']
                    
                    # Add hierarchical metadata if it exists
                    if 'level' in metadata:
                        result_metadata['level'] = metadata['level']
                    if 'parent' in metadata:
                        result_metadata['parent'] = metadata['parent']
                    if 'children' in metadata:
                        result_metadata['children'] = metadata['children']
                    
                    formatted_results.append({
                        'id': id_,
                        'score': 1 - distance,  # Convert distance to similarity score
                        'metadata': result_metadata
                    })
                
                return formatted_results
                
        except Exception as e:
            raise
    
    def delete(self, ids: List[str]) -> None:
        """
        Delete embeddings from ChromaDB.
        
        Args:
            ids: List of IDs to delete
            
        Raises:
            Exception: If there's an error deleting embeddings
        """
        try:
            self.collection.delete(ids=ids)
        except Exception as e:
            raise
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the ChromaDB collection.
        
        Returns:
            Dictionary containing collection statistics
            
        Raises:
            Exception: If there's an error retrieving statistics
        """
        try:
            # Get count of items in collection
            count = self.collection.count()
            
            # Get a sample embedding to determine dimensions
            sample = self.collection.peek(limit=1)
            
            # Fix the ambiguous truth value error
            dimensions = 0
            if sample['embeddings'] is not None and len(sample['embeddings']) > 0:
                dimensions = len(sample['embeddings'][0])
            
            return {
                "count": count,
                "dimensions": dimensions,
                "name": self.collection.name,
                "metadata": self.collection.metadata
            }
        except Exception as e:
            raise 