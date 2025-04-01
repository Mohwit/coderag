#!/usr/bin/env python3
"""
Hierarchical Chunking Example

This script demonstrates how to use CodeRAG with hierarchical chunking to index a repository
and search for code with preserved class-method relationships.
"""

import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from coderag import Repository, ChromaDBStore

# def preview_code(code, max_lines=8):
#     """Show a preview of code with first few and last few lines."""
#     lines = code.strip().split('\n')
#     if len(lines) <= max_lines:
#         return code
    
#     first = lines[:4]
#     last = lines[-2:]
#     return '\n'.join(first + ['...'] + last)

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
    
    if result.get('included_as_context'):
        print("\nNote: Included as context for a matching method")
    
    if 'summary' in metadata:
        print("\nSummary:", metadata['summary'])
    
    print("\nCode Preview:")
    print("```")
    print((metadata['content']))
    print("```")

def main():     
    # Initialize the vector store
    vector_store = ChromaDBStore(
        collection_name="example_repo",
        persist_directory="./vector_store",
        verbose=True
    )
    
    # Initialize the repository handler
    repo = Repository(
        repo_path="./coderag",  # Path to the repository you want to index
        vector_store=vector_store,
        use_code_summaries=False,  # Enable code summarization
        verbose=True
    )
    
    # Index the repository
    print("Indexing repository with hierarchical chunking...")
    stats = repo.index()
    print(f"Indexed {stats['total_chunks']} chunks from {stats['indexed_files']} files")
    
    # Example 1: Search for a class
    # print("\n=== Example 1: Searching for a Class ===")
    # print("-" * 50)
    # results = repo.search(
    #     "function to handle HTTP requests",
    #     top_k=3
    # )
    # for result in results:
    #     display_result(result)
    
    # Example 2: Search for a specific method
    # print("\n=== Example 2: Searching for a Method ===")
    # print("-" * 50)
    # results = repo.search(
    #     "method to extract code chunks from file",
    #     top_k=3
    # )
    # for result in results:
    #     display_result(result)
    
    # # Example 3: Search with language filter
    print("\n=== Example 3: Searching with Language Filter ===")
    print("-" * 50)
    results = repo.search(
        "parse Python code",
        top_k=3,
        filter={"language": "python"}
    )
    for result in results:
        display_result(result)

if __name__ == "__main__":
    main() 