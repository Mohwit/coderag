"""
Embedder module for generating vector embeddings from code snippets.

This module provides the CodeEmbedder class that converts code snippets into
vector embeddings using SentenceTransformers.
"""

from typing import List, Union
from sentence_transformers import SentenceTransformer
import logging
from ..config import DEFAULT_EMBEDDING_MODEL, DEFAULT_EMBEDDING_BATCH_SIZE

class CodeEmbedder:
    """
    Generates vector embeddings for code snippets.
    
    This class wraps SentenceTransformer to provide code-specific embedding functionality.
    It handles batching and normalization of embeddings for optimal performance.
    
    Attributes:
        model: The underlying SentenceTransformer model
    """
    
    def __init__(self, model_name: str = DEFAULT_EMBEDDING_MODEL):
        """
        Initialize the code embedder.
        
        Args:
            model_name: Name of the pre-trained model to use for embeddings.
                       Defaults to a general-purpose code-friendly model.
        """
        logging.info(f"Initializing CodeEmbedder with model: {model_name}")
        self.model = SentenceTransformer(model_name)
    
    def embed(self, texts: Union[str, List[str]], batch_size: int = DEFAULT_EMBEDDING_BATCH_SIZE) -> List[List[float]]:
        """
        Generate embeddings for text(s).
        
        This method handles both single texts and lists of texts. The resulting embeddings
        are L2-normalized, making them suitable for cosine similarity comparison.
        
        Args:
            texts: Single text string or list of text strings to embed
            batch_size: Number of texts to process in each batch
            
        Returns:
            List of embedding vectors (list of floats)
        """
        if isinstance(texts, str):
            texts = [texts]
            
        logging.debug(f"Generating embeddings for {len(texts)} texts (batch size: {batch_size})")
            
        # Generate embeddings in batches
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=len(texts) > 100,  # Only show progress for larger batches
            normalize_embeddings=True  # L2 normalize embeddings
        )
        
        return embeddings.tolist()  # Convert numpy array to list 