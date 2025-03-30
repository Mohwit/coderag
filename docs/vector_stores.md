# Vector Stores in CodeRAG

CodeRAG supports multiple vector store backends for storing and searching code embeddings. Currently supported options are:

## ChromaDB

ChromaDB is the default vector store, offering local storage and fast similarity search.

```python
from coderag import Repository
from coderag.storage.chromadb import ChromaDBStore

# Initialize ChromaDB store
vector_store = ChromaDBStore(
    collection_name="my_collection",
    persist_directory=".chroma"  # Local directory for storage
)

# Use with Repository
repo = Repository(
    repo_path="./my_repo",
    vector_store=vector_store
)
```

## Pinecone

Pinecone offers a cloud-based vector store with high scalability and performance.

```python
from coderag import Repository
from coderag.storage.pinecone import PineconeStore

# Initialize Pinecone store
vector_store = PineconeStore(
    api_key="your-api-key",          # From Pinecone dashboard
    environment="your-environment",   # From Pinecone dashboard
    index_name="coderag-index",      # Name for your index
    namespace="optional-namespace"    # Optional namespace for organization
)

# Use with Repository
repo = Repository(
    repo_path="./my_repo",
    vector_store=vector_store
)
```

### Pinecone Features

1. **Cloud Storage**: Embeddings are stored in Pinecone's cloud infrastructure
2. **Namespaces**: Organize vectors into separate namespaces
3. **Scalability**: Handle large codebases efficiently
4. **High Performance**: Fast similarity search at scale

### Using Namespaces

Pinecone supports namespaces for organizing vectors:

```python
# Create stores for different parts of your codebase
main_store = PineconeStore(
    api_key="your-api-key",
    environment="your-environment",
    index_name="coderag-index",
    namespace="main"
)

test_store = PineconeStore(
    api_key="your-api-key",
    environment="your-environment",
    index_name="coderag-index",
    namespace="tests"
)

# Index main code and tests separately
main_repo = Repository(repo_path="./src", vector_store=main_store)
test_repo = Repository(repo_path="./tests", vector_store=test_store)
```

## Common Features

Both vector stores support:

1. **Similarity Search**: Find similar code chunks using vector embeddings
2. **Metadata Filtering**: Filter results based on metadata (language, file type, etc.)
3. **Batch Processing**: Efficient handling of large numbers of embeddings
4. **Statistics**: Get information about stored vectors

## Choosing a Vector Store

- Use **ChromaDB** when:

  - You want a simple, local setup
  - Your codebase is small to medium sized
  - You don't need cloud storage

- Use **Pinecone** when:
  - You need cloud-based storage
  - Your codebase is large
  - You want to organize vectors into namespaces
  - You need high scalability

## Examples

See the example scripts in the examples directory:

- [basic_usage.py](../examples/basic_usage.py): Basic usage with ChromaDB
- [pinecone_example.py](../examples/pinecone_example.py): Using Pinecone as vector store
