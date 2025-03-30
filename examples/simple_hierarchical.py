#!/usr/bin/env python3
"""
A simple example demonstrating hierarchical chunking in CodeRAG.
"""

import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from coderag import Repository, ChromaDBStore

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
    
    if metadata["type"] == "class":
        if "children" in metadata:
            methods = [m.split(":")[-1] for m in metadata["children"]]
            print("Methods:", ", ".join(methods))
    else:  # method
        if "parent" in metadata:
            parent_class = metadata["parent"].split(":")[-2]
            print(f"In class: {parent_class}")
    
    print("\nCode Preview:")
    print("```")
    print(preview_code(result["text"]))
    print("```")

def main():
    # Initialize vector store
    vector_store = ChromaDBStore(
        collection_name="simple_hierarchical_example",
        persist_directory=".chroma"
    )
    
    # Create and initialize repository
    repo = Repository(
        repo_path=os.path.dirname(os.path.dirname(__file__)),  # Use CodeRAG's own repo
        vector_store=vector_store,
    )
    
    # Index only the indexer directory for this example
    repo.index(target_directories=["coderag/indexer"])
    
    print("Example 1: Search for a class")
    print("-" * 50)
    results = repo.search(
        "class for handling repository indexing",
        top_k=2
    )
    for result in results:
        display_result(result)
    
    print("\nExample 2: Search for a method")
    print("-" * 50)
    results = repo.search(
        "method to extract code chunks from file",
        top_k=2
    )
    for result in results:
        display_result(result)

if __name__ == "__main__":
    main() 