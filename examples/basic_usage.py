import sys
import os
from dotenv import load_dotenv

load_dotenv()

# Add the project root to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from coderag import Repository, ChromaDBStore

def main():
    # Initialize the vector store
    vector_store = ChromaDBStore(
        collection_name="example_repo",
        persist_directory="./vector_store"
    )
    
    # Initialize the repository handler
    repo = Repository(
        repo_path="./coderag",  # Path to the repository you want to index
        vector_store=vector_store,
        use_code_summaries=True,  # Enable code summarization
        model="claude-3-5-sonnet-20240620",
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        use_hyde=True,
        use_reranking=True,
        verbose=True
    )
    
    # Index the repository
    print("Indexing repository...")
    stats = repo.index()
    print(f"Indexed {stats['total_chunks']} chunks from {stats['indexed_files']} files")
    
    # Search for code
    query = "function to handle HTTP requests"
    print(f"\nSearching for: {query}")
    results = repo.search(query=query, top_k=3)
    
    # Display results
    for i, result in enumerate(results, 1):
        print(f"\nResult {i} (Score: {result['score']:.4f})")
        print(f"File: {result['metadata']['file_path']}")
        print(f"Type: {result['metadata']['type']}")
        if 'name' in result['metadata']:
            print(f"Name: {result['metadata']['name']}")
        
        if 'summary' in result['metadata']:
            print(f"Summary: {result['metadata']['summary']}")
        
        # Print first few lines of code
        code_lines = result['metadata']['content'].split('\n')
        preview = '\n'.join(code_lines[:10])
        print(f"\nCode preview:\n{preview}")
        if len(code_lines) > 10:
            print("... [more code] ...")

if __name__ == "__main__":
    main()
