# CodeRAG

A plug-and-play Python package for code repository indexing and semantic search, enabling RAG (Retrieval-Augmented Generation) applications for codebases.

## Features

- **Smart Code Parsing**: Analyzes code using tree-sitter, preserving semantic structure
- **Language Support**: Handles Python, JavaScript, TypeScript, and Java
- **Flexible Storage**: Choose between various vector databases (currently supports ChromaDB)
- **Intelligent Chunking**: Creates meaningful code chunks based on classes, functions, and logical blocks
- **Summarization Option**: Generate AI summaries of code chunks for more effective embedding
- **Easy Integration**: Simple API to add CodeRAG to any application

## Installation

```bash
pip install coderag
```

## Quick Start

```python
from coderag import Repository, ChromaDBStore

# Initialize vector store
vector_store = ChromaDBStore(
    collection_name="my_repo",
    persist_directory="./vector_db"
)

# Initialize repository handler
repo = Repository(
    repo_path="path/to/your/repo",
    vector_store=vector_store,
    use_code_summaries=True  # Optional: use AI summaries for better embeddings
)

# Index the repository
repo.index()

# Search for code
results = repo.search("function to handle HTTP requests", top_k=5)

# Display results
for result in results:
    print(f"Score: {result['score']}")
    print(f"File: {result['metadata']['file_path']}")
    if 'summary' in result['metadata']:
        print(f"Summary: {result['metadata']['summary']}")
    print(f"Code:\n{result['metadata']['content']}")
    print("-" * 50)
```

## How It Works

CodeRAG breaks down the code repository into semantically meaningful chunks using tree-sitter parsing. It understands code structure (functions, classes, imports) and organizes them accordingly.

1. **Parsing**: Repository files are parsed using language-specific parsers
2. **Chunking**: Code is divided into logical chunks (functions, classes, imports, etc.)
3. **Embedding**: Chunks are embedded using SentenceTransformers
4. **Storage**: Embeddings are stored in a vector database
5. **Retrieval**: Similar code is retrieved based on semantic similarity

## Advanced Usage

### Using Code Summaries

For better semantic matching, you can enable code summarization:

```python
repo = Repository(
    repo_path="path/to/your/repo",
    vector_store=vector_store,
    use_code_summaries=True  # Enable AI summarization
)
```

### Custom Embeddings

You can provide your own embedding model:

```python
from coderag import CodeEmbedder, Repository

custom_embedder = CodeEmbedder(model_name="your-preferred-model")

repo = Repository(
    repo_path="path/to/your/repo",
    vector_store=vector_store,
    embedder=custom_embedder
)
```

### Filtering Results

You can filter search results based on metadata:

```python
# Search only for Python functions
results = repo.search(
    query="handle authentication",
    filter={"language": "python", "type": "function"}
)
```

## Contributing

Contributions are welcome! To contribute:

1. Fork the repository
2. Create a feature branch
3. Add your changes
4. Submit a pull request

For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the Apache 2.0 License - see the LICENSE file for details.
