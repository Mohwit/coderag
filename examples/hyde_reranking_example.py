"""
HYDE and Reranking Example

This script demonstrates how to use CodeRAG with Hypothetical Document Embeddings (HYDE)
and reranking to improve search results.
"""

import os
import logging
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
from coderag import Repository, ChromaDBStore

# Configure logging
logging.basicConfig(level=logging.INFO)

def preview_code(code, max_lines=8):
    """Show a preview of code with first few and last few lines."""
    lines = code.strip().split('\n')
    if len(lines) <= max_lines:
        return code
    
    first = lines[:4]
    last = lines[-2:]
    return '\n'.join(first + ['...'] + last)

def display_result(result):
    """Display a search result with hierarchical information."""
    metadata = result["metadata"]
    score = result["score"]
    
    print(f"\nScore: {score:.2f}")
    print(f"Type: {metadata['type']}")
    print(f"Name: {metadata['name']}")
    print(f"File: {metadata['file_path']}:{metadata['start_line']}-{metadata['end_line']}")
    
    if metadata["type"] == "class":
        if "children" in metadata:
            methods = [m.split(":")[-1] for m in metadata["children"]]
            print("Methods:", ", ".join(methods))
    else:  # method
        if "parent" in metadata:
            parent_class = metadata["parent"].split(":")[-2]
            print(f"In class: {parent_class}")
    
    if 'summary' in metadata:
        print("\nSummary:", metadata['summary'])
    
    print("\nCode Preview:")
    print("```")
    print(preview_code(metadata['content']))
    print("```")

def main():
    # Initialize components
    vector_store = ChromaDBStore(
        collection_name="hyde_reranking_example",
        persist_directory="./vector_store"
    )
    
    # Initialize repository with HYDE and reranking enabled
    repo = Repository(
        repo_path="./coderag",
        vector_store=vector_store,
        use_code_summaries=True,
        use_hyde=True,        # Enable HYDE
        use_reranking=True    # Enable reranking
    )
    
    # Index the repository
    print("Indexing repository...")
    stats = repo.index()
    print(f"Indexed {stats['total_chunks']} chunks from {stats['indexed_files']} files")
    
    # Example 1: Basic search without HYDE/reranking
    print("\n=== Example 1: Basic Search ===")
    print("-" * 50)
    repo.use_hyde = False
    repo.use_reranking = False
    results = repo.search(
        "find methods that process abstract syntax trees",
        top_k=3
    )
    print("Basic Search Results:")
    for result in results:
        display_result(result)
    
    # Example 2: Search with HYDE
    print("\n=== Example 2: Search with HYDE ===")
    print("-" * 50)
    repo.use_hyde = True
    repo.use_reranking = False
    results = repo.search(
        "find methods that process abstract syntax trees",
        top_k=3
    )
    print("HYDE Search Results:")
    for result in results:
        display_result(result)
    
    # Example 3: Search with HYDE and reranking
    print("\n=== Example 3: Search with HYDE and Reranking ===")
    print("-" * 50)
    repo.use_hyde = True
    repo.use_reranking = True
    results = repo.search(
        "find methods that process abstract syntax trees",
        top_k=3
    )
    print("HYDE + Reranking Results:")
    for result in results:
        display_result(result)

if __name__ == "__main__":
    main() 