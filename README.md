# CodeRAG

A plug-and-play Python package for code repository indexing and semantic search, enabling RAG (Retrieval-Augmented Generation) applications for codebases.

## Features

- **Smart Code Parsing**: Analyzes code using tree-sitter, preserving semantic structure
- **Language Support**: Handles Python, JavaScript, TypeScript, and Java
- **Flexible Storage**: Choose between various vector databases (currently supports ChromaDB)
- **Hierarchical Chunking**: Preserves class-method relationships for improved context and search results
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
    # Display hierarchical information if available
    if result['metadata']['type'] == 'method' and 'parent' in result['metadata']:
        print(f"Method in class: {result['metadata']['parent'].split(':')[-2]}")
    elif result['metadata']['type'] == 'class' and 'children' in result['metadata']:
        print(f"Class with methods: {len(result['metadata']['children'])}")
    if 'summary' in result['metadata']:
        print(f"Summary: {result['metadata']['summary']}")
    print(f"Code:\n{result['metadata']['content']}")
    print("-" * 50)
```

## How It Works

CodeRAG breaks down the code repository into semantically meaningful chunks using tree-sitter parsing. It understands code structure (functions, classes, imports) and organizes them accordingly.

1. **Parsing**: Repository files are parsed using language-specific parsers
2. **Hierarchical Chunking**: Classes and methods are preserved in a hierarchical structure
3. **Chunking**: Code is divided into logical chunks (functions, classes, imports, etc.)
4. **Embedding**: Chunks are embedded using SentenceTransformers
5. **Storage**: Embeddings are stored in a vector database
6. **Retrieval**: Similar code is retrieved based on semantic similarity, preserving hierarchical context

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

### Understanding Hierarchical Results

Search results include hierarchical metadata:

```python
# Search for methods within a specific class
results = repo.search("database connection method")

for result in results:
    metadata = result['metadata']

    # For methods, get the parent class
    if metadata['type'] == 'method' and 'parent' in metadata:
        parent_id = metadata['parent']
        print(f"Method '{metadata['name']}' belongs to class: {parent_id.split(':')[-2]}")

    # For classes, see what methods are included
    if metadata['type'] == 'class' and 'children' in metadata:
        method_names = [m.split(':')[-1] for m in metadata['children']]
        print(f"Class '{metadata['name']}' contains methods: {', '.join(method_names)}")
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
