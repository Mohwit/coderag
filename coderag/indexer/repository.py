"""
Repository indexing module for CodeRAG.

This module provides the main Repository class for parsing, indexing, and searching
code repositories. It coordinates the interaction between the parser, embedder, and
vector store components.
"""

from typing import Optional, List, Dict, Any
from pathlib import Path
import logging

from .code_parser import CodeParser
from .embedder import CodeEmbedder
from ..storage.base import VectorStore
from ..utils.generate_summary import generate_code_summary
from ..config import DEFAULT_EXCLUDE_DIRS, DEFAULT_EXCLUDE_EXTENSIONS, DEFAULT_BATCH_SIZE, setup_logging

class Repository:
    """
    Main class for handling repository indexing and searching.
    
    This class coordinates the processing of a code repository, breaking it down into
    meaningful chunks, generating embeddings, and storing them in a vector database.
    It also provides functionality for searching the indexed code.
    
    Attributes:
        repo_path: Path to the repository
        vector_store: Vector store instance for storing embeddings
        embedder: Embedder instance for generating vectors
        parser: Parser instance for processing code files
        use_code_summaries: Whether to use code summaries for embeddings
    """
    
    def __init__(self,
                 repo_path: str,
                 vector_store: VectorStore,
                 embedder: Optional[CodeEmbedder] = None,
                 exclude_dirs: Optional[List[str]] = None,
                 exclude_extensions: Optional[List[str]] = None,
                 use_code_summaries: bool = False,
                 log_level: int = logging.INFO,
                 log_file: Optional[str] = None):
        """
        Initialize the repository handler.
        
        Args:
            repo_path: Path to the repository
            vector_store: Vector store instance for storing embeddings
            embedder: Optional custom embedder instance
            exclude_dirs: List of directory names to exclude
            exclude_extensions: List of file extensions to exclude
            use_code_summaries: Whether to use code summaries for embeddings instead of raw code
            log_level: Logging level
            log_file: Optional path to a log file
        """
        # Set up logging
        setup_logging(level=log_level, log_file=log_file)
        
        self.repo_path = Path(repo_path)
        self.vector_store = vector_store
        self.embedder = embedder or CodeEmbedder()
        self.use_code_summaries = use_code_summaries
        
        # Use default exclude lists if not provided
        self.parser = CodeParser(
            repo_path=repo_path,
            exclude_dirs=exclude_dirs or DEFAULT_EXCLUDE_DIRS,
            exclude_extensions=exclude_extensions or DEFAULT_EXCLUDE_EXTENSIONS
        )
        
        logging.info(f"Initialized repository handler for: {self.repo_path}")
        logging.info(f"Summary mode: {'enabled' if self.use_code_summaries else 'disabled'}")
    
    def index(self, batch_size: int = DEFAULT_BATCH_SIZE) -> Dict[str, Any]:
        """
        Index the entire repository.
        
        This method processes all files in the repository, chunks them into meaningful
        segments, generates embeddings, and stores them in the vector database.
        
        Args:
            batch_size: Number of chunks to process at once
            
        Returns:
            Dictionary containing indexing statistics
        """
        logging.info(f"Starting indexing of repository: {self.repo_path}")
        logging.info(f"Using {'code summaries' if self.use_code_summaries else 'raw code'} for embeddings")
        logging.info(f"Batch size: {batch_size}")
        
        # Collect all files
        files = list(self.parser.walk_repository())
        total_files = len(files)
        logging.info(f"Found {total_files} files to process")
        
        # Process files in batches
        chunks = []
        metadata = []
        total_chunks = 0
        indexed_files = 0
        skipped_files = 0
        processing_errors = 0
        
        # Process each file
        for i, file_path in enumerate(files, 1):
            try:
                logging.info(f"Processing file {i}/{total_files}: {file_path}")
                file_chunks = self.parser.parse_file(file_path)
                
                if not file_chunks:
                    logging.warning(f"No valid chunks found in file: {file_path}")
                    skipped_files += 1
                    continue
                
                indexed_files += 1
                
                # Process chunks from the file
                for chunk_text, chunk_metadata in file_chunks:
                    # Generate summary if enabled
                    if self.use_code_summaries:
                        try:
                            summary = generate_code_summary(chunk_text)
                            chunks.append(summary)
                            # Store both summary and original code in metadata
                            chunk_metadata['summary'] = summary
                            chunk_metadata['content'] = chunk_text
                        except Exception as e:
                            logging.error(f"Error generating summary for chunk: {e}")
                            # Fall back to using raw code if summary generation fails
                            chunks.append(chunk_text)
                            chunk_metadata['content'] = chunk_text
                    else:
                        chunks.append(chunk_text)
                        chunk_metadata['content'] = chunk_text
                    
                    metadata.append(chunk_metadata)
                    total_chunks += 1
                    
                    # Process batch if size reached
                    if len(chunks) >= batch_size:
                        logging.info(f"Processing batch of {len(chunks)} chunks")
                        self._process_batch(chunks, metadata)
                        chunks = []
                        metadata = []
                        
            except Exception as e:
                logging.error(f"Error processing file {file_path}: {e}")
                processing_errors += 1
                skipped_files += 1
        
        # Process remaining chunks
        if chunks:
            logging.info(f"Processing final batch of {len(chunks)} chunks")
            self._process_batch(chunks, metadata)
        
        # Generate statistics
        stats = {
            "total_files": total_files,
            "indexed_files": indexed_files,
            "skipped_files": skipped_files,
            "processing_errors": processing_errors,
            "total_chunks": total_chunks,
            "vector_store_stats": self.vector_store.get_collection_stats()
        }
        
        logging.info(f"Indexing completed:")
        logging.info(f"Total files processed: {total_files}")
        logging.info(f"Successfully indexed files: {indexed_files}")
        logging.info(f"Skipped files: {skipped_files}")
        logging.info(f"Total chunks created: {total_chunks}")
        
        return stats
    
    def _process_batch(self, chunks: List[str], metadata: List[Dict[str, Any]]) -> None:
        """
        Process a batch of chunks.
        
        This helper method generates embeddings for a batch of chunks and adds them
        to the vector store.
        
        Args:
            chunks: List of code chunks or summaries
            metadata: List of metadata dictionaries
        """
        try:
            # Generate embeddings
            embeddings = self.embedder.embed(chunks)
            
            # Store in vector database
            self.vector_store.add_embeddings(
                embeddings=embeddings,
                metadata=metadata
            )
        except Exception as e:
            logging.error(f"Error processing batch: {e}")
            raise
    
    def search(self,
               query: str,
               top_k: int = 5,
               filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search for similar code in the indexed repository.
        
        This method generates an embedding for the query and searches for similar
        vectors in the vector store. Results are enhanced with hierarchical relationships
        for improved context.
        
        Args:
            query: Search query
            top_k: Number of results to return
            filter: Optional metadata filter (e.g., {"language": "python"})
            
        Returns:
            List of dictionaries containing search results with scores and metadata
        """
        try:
            logging.info(f"Searching for: {query}")
            logging.info(f"Filter: {filter}")
            logging.info(f"Top K: {top_k}")
            
            # Generate query embedding using the dedicated query embedding method
            query_embedding = self.embedder.embed_query(query)
            
            # Search vector store
            results = self.vector_store.search(
                query_embedding=query_embedding,
                top_k=top_k,
                filter=filter
            )
            
            # Enhance results with hierarchical relationships
            enhanced_results = self._enhance_hierarchical_results(results)
            
            logging.info(f"Found {len(enhanced_results)} results")
            return enhanced_results
            
        except Exception as e:
            logging.error(f"Error during search: {e}")
            raise

    def _enhance_hierarchical_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enhance search results with hierarchical relationships.
        
        This method:
        1. Identifies method results that have parent classes
        2. Adds context about the parent class to the method result
        3. Ensures that relevant parts of class are included even if only methods match
        
        Args:
            results: Original search results
            
        Returns:
            Enhanced results with hierarchical relationships
        """
        enhanced_results = []
        seen_ids = set()
        
        # First pass: collect all class IDs that might be parents
        parent_classes = {}
        for result in results:
            result_id = result['id']
            if result_id in seen_ids:
                continue
            
            metadata = result['metadata']
            
            # If this is a method with a parent class
            if metadata.get('type') == 'method' and 'parent' in metadata:
                parent_id = metadata['parent']
                class_name = metadata.get('class')
                
                # Save this ID to fetch full class details later
                if parent_id not in parent_classes:
                    parent_classes[parent_id] = {
                        'methods': [],
                        'class_name': class_name
                    }
                
                # Add this method to the parent's methods list
                parent_classes[parent_id]['methods'].append(result)
            
            # Add result to enhanced list
            enhanced_results.append(result)
            seen_ids.add(result_id)
        
        # Second pass: for each method that has a parent, check if the parent is already in results
        for parent_id, parent_info in parent_classes.items():
            # If parent not yet in results, fetch it from vector store
            if not any(r['id'] == parent_id for r in enhanced_results):
                try:
                    # Try to fetch the parent class details
                    parent_results = self.vector_store.search(
                        query_embedding=None,  # Not needed for ID search
                        filter={"id": parent_id},
                        top_k=1
                    )
                    
                    if parent_results:
                        # Add class metadata
                        parent_result = parent_results[0]
                        parent_result['score'] = 0.5  # Lower artificial score
                        parent_result['included_as_context'] = True
                        
                        # Add to enhanced results
                        enhanced_results.append(parent_result)
                        logging.info(f"Added parent class {parent_info['class_name']} as context")
                except Exception as e:
                    logging.warning(f"Error fetching parent class: {e}")
        
        # Sort by score (highest first)
        enhanced_results.sort(key=lambda x: x['score'], reverse=True)
        
        return enhanced_results 