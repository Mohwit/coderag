"""
Repository indexing module for CodeRAG.

This module provides the main Repository class for parsing, indexing, and searching
code repositories. It coordinates the interaction between the parser, embedder, and
vector store components.
"""

from typing import Optional, List, Dict, Any
from pathlib import Path
import anthropic
from rerankers import Reranker

from .code_parser import CodeParser
from .embedder import CodeEmbedder
from ..storage.base import VectorStore
from ..utils.generate_summary import generate_code_summary
from ..config import DEFAULT_EXCLUDE_DIRS, DEFAULT_EXCLUDE_EXTENSIONS, DEFAULT_BATCH_SIZE, DEFAULT_MODEL, API_KEY

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
        use_hyde: Whether to use hypothetical document embeddings
        use_reranking: Whether to rerank search results
        verbose: Whether to print detailed progress information
    """
    
    def __init__(self,
                 repo_path: str,
                 vector_store: VectorStore,
                 embedder: Optional[CodeEmbedder] = None,
                 exclude_dirs: Optional[List[str]] = None,
                 exclude_extensions: Optional[List[str]] = None,
                 use_code_summaries: bool = False,
                 use_hyde: bool = False,
                 use_reranking: bool = False,
                 model: str = DEFAULT_MODEL,
                 api_key: str = API_KEY,
                 verbose: bool = False):
        """
        Initialize the repository handler.
        
        Args:
            repo_path: Path to the repository
            vector_store: Vector store instance for storing embeddings
            embedder: Optional custom embedder instance
            exclude_dirs: List of directory names to exclude
            exclude_extensions: List of file extensions to exclude
            use_code_summaries: Whether to use code summaries for embeddings instead of raw code
            use_hyde: Whether to use hypothetical document embeddings
            use_reranking: Whether to rerank search results
            verbose: Whether to print detailed progress information
        """
        self.repo_path = Path(repo_path)
        self.vector_store = vector_store
        self.embedder = embedder or CodeEmbedder(verbose=verbose)
        self.use_code_summaries = use_code_summaries
        self.use_hyde = use_hyde
        self.use_reranking = use_reranking
        self.model = model
        self.api_key = api_key
        self.verbose = verbose      
        # Use default exclude lists if not provided
        self.parser = CodeParser(
            repo_path=repo_path,
            exclude_dirs=exclude_dirs or DEFAULT_EXCLUDE_DIRS,
            exclude_extensions=exclude_extensions or DEFAULT_EXCLUDE_EXTENSIONS,
            verbose=verbose
        )
    
    def _log(self, message: str) -> None:
        """Print message if verbose mode is enabled."""
        if self.verbose:
            print(f"[CodeRAG] {message}")
    
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
        # Collect all files
        self._log("Starting repository indexing...")
        files = list(self.parser.walk_repository())
        total_files = len(files)
        self._log(f"Found {total_files} files to process")
        
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
                self._log(f"Processing file {i}/{total_files}: {file_path}")
                file_chunks = self.parser.parse_file(file_path)
                
                if not file_chunks:
                    skipped_files += 1
                    self._log(f"Skipped empty file: {file_path}")
                    continue
                
                indexed_files += 1
                
                # Process chunks from the file
                for chunk_text, chunk_metadata in file_chunks:
                    # Generate summary if enabled
                    if self.use_code_summaries:
                        try:
                            summary = generate_code_summary(chunk_text, self.model, self.api_key)
                            chunks.append(summary)
                            # Store both summary and original code in metadata
                            chunk_metadata['summary'] = summary
                            chunk_metadata['content'] = chunk_text
                        except Exception as e:
                            self._log(f"Failed to generate summary, using raw code: {str(e)}")
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
                        self._log(f"Processing batch of {len(chunks)} chunks")
                        self._process_batch(chunks, metadata)
                        chunks = []
                        metadata = []
                        
            except Exception as e:
                self._log(f"Error processing file {file_path}: {str(e)}")
                processing_errors += 1
                skipped_files += 1
        
        # Process remaining chunks
        if chunks:
            self._log(f"Processing final batch of {len(chunks)} chunks")
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
        
        self._log("Indexing completed successfully")
        self._log(f"Indexed {indexed_files} files, {total_chunks} chunks, {skipped_files} skipped, {processing_errors} errors")
        
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
            self._log(f"Generating embeddings for {len(chunks)} chunks")
            embeddings = self.embedder.embed(chunks)
            
            # Store in vector database
            self._log("Storing embeddings in vector store")
            self.vector_store.add_embeddings(
                embeddings=embeddings,
                metadata=metadata
            )
            self._log("Successfully stored batch in vector store")
        except Exception as e:
            self._log(f"Error processing batch: {str(e)}")
            raise
    
    def generate_hypothetical_answer(self, query: str) -> str:
        """
        Generate a hypothetical code summary that would answer the query.
        This mimics the format of our stored code summaries.
        
        Args:
            query (str): Search query
            
        Returns:
            str: Hypothetical code summary
        """
        hyde_prompt = f"""Given this question about code: "{query}"
        Write a brief technical summary that would answer this question, as if describing a relevant code snippet.
        Focus on implementation details and keep it concise (2-3 sentences)."""
        
        client = anthropic.Anthropic()
        response = client.messages.create(
            model=self.model,
            api_key=self.api_key,
            temperature=0,
            max_tokens=4096,
            messages=[{"role": "user", "content": hyde_prompt}]
        )
        
        return response.content[0].text

    def rerank_documents(self, query: str, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Rerank search results based on relevance to the query.
        
        Args:
            query (str): Search query
            results: List of search results
            
        Returns:
            List[Dict[str, Any]]: Reranked search results
        """
        # Extract text content from results
        docs = [result["metadata"]["content"] for result in results]
        
        try:
            # Initialize reranker with additional kwargs
            ranker = Reranker("answerdotai/answerai-colbert-small-v1", model_type='colbert', verbose=0)
            
            # Get reranked indices
            reranked_indices = list(ranker.rank(query=query, docs=docs))
            
            # Reorder results based on new ranking
            reranked_results = [results[i] for i in reranked_indices]
            
            # Update scores based on new ranking
            for i, result in enumerate(reranked_results):
                result["score"] = 1.0 - (i / len(reranked_results))
                
            return reranked_results
            
        except Exception as e:
            return results

    def search(self,
               query: str,
               top_k: int = 5,
               filter: Optional[Dict[str, Any]] = None,
            ) -> List[Dict[str, Any]]:
        """
        Search for code chunks using the query.
        
        Args:
            query: Search query string
            top_k: Number of results to return
            filter: Optional metadata filter
            
        Returns:
            List of dictionaries containing search results with metadata
        """
        self._log(f"Searching for: {query}")
        
        if self.use_hyde:
            self._log("Generating hypothetical answer for search...")
            hypothetical_answer = self.generate_hypothetical_answer(query)
            self._log("Using hypothetical answer to enhance search")
            search_query = hypothetical_answer
        else:
            search_query = query
            
        # Generate embedding for search query
        self._log("Generating embedding for search query")
        query_embedding = self.embedder.embed([search_query])[0]
        
        # Search vector store
        self._log(f"Searching vector store with top_k={top_k}")
        results = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            filter=filter
        )
        
        if self.use_reranking and len(results) > 1:
            self._log("Reranking search results")
            results = self.rerank_documents(query, results)
            
        self._log(f"Found {len(results)} results")
        return results

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
                except Exception as e:
                    pass
        
        # Sort by score (highest first)
        enhanced_results.sort(key=lambda x: x['score'], reverse=True)
        
        return enhanced_results 