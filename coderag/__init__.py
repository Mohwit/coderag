"""
CodeRAG: Code repository indexing and semantic search.

This package enables semantic search over code repositories by:
1. Parsing and chunking code into meaningful segments
2. Generating embeddings for code chunks
3. Storing embeddings in a vector database
4. Providing search capabilities for finding similar code

Main components:
- Repository: Main class for indexing and searching code
- VectorStore: Abstract base class for vector storage
- ChromaDBStore: ChromaDB implementation of VectorStore
- CodeEmbedder: Generates embeddings for code chunks
"""

from .indexer.repository import Repository
from .indexer.embedder import CodeEmbedder
from .indexer.code_parser import CodeParser
from .storage.base import VectorStore
from .storage.chromadb import ChromaDBStore
from .storage.pinecone import PineconeStore
from .utils.generate_summary import generate_code_summary
from .config import LANGUAGE_CONFIGS

__version__ = "0.1.0"

__all__ = [
    "Repository",
    "CodeEmbedder",
    "CodeParser",
    "VectorStore",
    "ChromaDBStore",
    "PineconeStore",
    "generate_code_summary",
    "LANGUAGE_CONFIGS",
]
