"""
Embedder module for generating vector embeddings from code snippets.

This module provides the CodeEmbedder class that converts code snippets into
vector embeddings using SentenceTransformers.
"""

from typing import List, Union
from sentence_transformers import SentenceTransformer
from ..config import DEFAULT_EMBEDDING_MODEL, DEFAULT_EMBEDDING_BATCH_SIZE

class CodeEmbedder:
    """
    Generates vector embeddings for code snippets.
    
    This class wraps SentenceTransformer to provide code-specific embedding functionality.
    It handles batching and normalization of embeddings for optimal performance.
    
    Attributes:
        model: The underlying SentenceTransformer model
        verbose: Whether to print detailed progress information
    """
    
    def __init__(self, model_name: str = DEFAULT_EMBEDDING_MODEL, verbose: bool = False):
        """
        Initialize the code embedder.
        
        Args:
            model_name: Name of the pre-trained model to use for embeddings.
                       Defaults to a general-purpose code-friendly model.
            verbose: Whether to print detailed progress information
        """
        self.verbose = verbose
        self._log(f"Initializing embedder with model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self._log("Model loaded successfully")
    
    def _log(self, message: str) -> None:
        """Print message if verbose mode is enabled."""
        if self.verbose:
            print(f"[CodeRAG Embedder] {message}")
    
    def embed(self, texts: Union[str, List[str]], batch_size: int = DEFAULT_EMBEDDING_BATCH_SIZE) -> List[List[float]]:
        """
        Generate embeddings for text(s).
        
        This method handles both single texts and lists of texts. The resulting embeddings
        are L2-normalized, making them suitable for cosine similarity comparison.
        
        Args:
            texts: Single text string or list of texts to embed
            batch_size: Number of texts to process in each batch
            
        Returns:
            List of embedding vectors (list of lists of floats)
        """
        if isinstance(texts, str):
            texts = [texts]
            self._log("Converting single text to list")
            
        self._log(f"Generating embeddings for {len(texts)} texts with batch size {batch_size}")
            
        # Generate embeddings in batches
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=len(texts) > 100,  # Only show progress for larger batches
            normalize_embeddings=True  # L2 normalize embeddings
        )
        
        self._log("Embeddings generated successfully")
        return embeddings.tolist()  # Convert numpy array to list
    
    def embed_query(self, text: str) -> List[float]:
        """
        Generate embedding for a single query text.
        
        This method is specifically for query embedding, returning a single vector
        in the format expected by vector stores for similarity search.
        
        Args:
            text: Query text to embed
            
        Returns:
            Single embedding vector (list of floats)
        """
        self._log("Generating embedding for query")
        
        # Generate embedding for single text
        embedding = self.model.encode(
            text,
            normalize_embeddings=True  # L2 normalize embeddings
        )
        
        self._log("Query embedding generated successfully")
        return embedding.tolist()  # Convert numpy array to list 