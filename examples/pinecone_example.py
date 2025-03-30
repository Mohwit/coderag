"""
Pinecone Vector Store Example

This script demonstrates how to use CodeRAG with Pinecone as the vector store.
"""

import os
import logging
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from coderag import Repository, PineconeStore

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
            # Get class name from metadata if available, otherwise try to extract from parent ID
            class_name = metadata.get('class')
            if not class_name and ':' in metadata['parent']:
                try:
                    # Try to get class name from parent ID, fallback to full ID if fails
                    class_name = metadata['parent'].split(":")[-1]
                except:
                    class_name = metadata['parent']
            print(f"In class: {class_name}")
    
    if 'summary' in metadata:
        print("\nSummary:", metadata['summary'])
    
    print("\nCode Preview:")
    print("```")
    print(preview_code(metadata['content']))
    print("```")

def main():
    # Initialize Pinecone vector store
    vector_store = PineconeStore(
        api_key=os.getenv("PINECONE_API_KEY"),
        index_name="coderag-example",
        namespace="test",
        dimension=384,
        cloud="aws",
        region="us-east-1"
    )
    
    # Initialize repository with Pinecone
    repo = Repository(
        repo_path="./coderag",
        vector_store=vector_store,
        use_code_summaries=False,
        use_hyde=True,
        use_reranking=False
    )
    
    # Index the repository
    print("Indexing repository...")
    # stats = repo.index()
    # print(f"Indexed {stats['total_chunks']} chunks from {stats['indexed_files']} files")
    
    # Example 1: Basic search
    print("\n=== Example 1: Basic Search ===")
    print("-" * 50)
    results = repo.search(
        "find methods that process abstract syntax trees",
        top_k=3
    )
    for result in results:
        display_result(result)
    
    # Example 2: Search with language filter
    print("\n=== Example 2: Search with Language Filter ===")
    print("-" * 50)
    results = repo.search(
        "find Python class definitions",
        top_k=3,
        filter={"language": "python"}
    )
    for result in results:
        display_result(result)
    

if __name__ == "__main__":
    main() 