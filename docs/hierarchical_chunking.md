# Hierarchical Chunking in CodeRAG

## Overview

Hierarchical chunking is a core feature in CodeRAG that enhances code understanding by preserving the relationship between code components, such as classes and their methods. This approach offers several benefits:

1. **Improved code context**: Methods are stored with reference to their parent class, maintaining important relationships.
2. **Enhanced search results**: When a method matches a search query, the parent class context is included to provide a more complete picture.
3. **Better organization**: Code is chunked in a way that reflects its natural structure.

## How It Works

CodeRAG processes code with hierarchical structure in mind:

1. For each class, it creates two types of chunks:

   - A "parent" chunk containing:
     - Class definition and docstring
     - Method signatures (without implementations)
     - Metadata about child methods
   - "Child" chunks for each method containing:
     - Method implementation
     - Reference to parent class
     - Method-specific metadata

2. Each chunk stores metadata about its relationships:

   ```python
   # Class chunk metadata example
   {
       'id': 'class_uuid',
       'type': 'class',
       'name': 'Repository',
       'level': 1,
       'children': [
           'method_uuid1:parse_file',
           'method_uuid2:search',
           'method_uuid3:index'
       ]
   }

   # Method chunk metadata example
   {
       'id': 'method_uuid1',
       'type': 'met
<!-- @import "[TOC]" {cmd="toc" depthFrom=1 depthTo=6 orderedList=false} -->
hod',
       'name': 'parse_file',
       'level': 2,
       'parent': 'class_uuid:Repository'
   }
   ```

3. During search:
   - When a method matches, its parent class context is automatically included
   - Results maintain hierarchy information for better understanding
   - Parent classes are included with a lower score when their methods match

## Example: Class Processing

Here's how a Python class gets processed into hierarchical chunks:

```python
class Repository:
    """Handles repository indexing and searching."""

    def __init__(self, path):
        self.path = path

    def index(self):
        """Index the repository."""
        pass

    def search(self, query):
        """Search the indexed code."""
        pass
```

Gets chunked into:

1. Class Overview Chunk:

```python
class Repository:
    """Handles repository indexing and searching."""

    def __init__(self, path): ...
    def index(self): ...
    def search(self, query): ...
```

2. Method Chunks:

```python
# Method chunk 1
def __init__(self, path):
    self.path = path

# Method chunk 2
def index(self):
    """Index the repository."""
    pass

# Method chunk 3
def search(self, query):
    """Search the indexed code."""
    pass
```

## Search Results Example

When searching for "index repository", you might get results like:

```python
# Result 1 (Score: 0.85)
Type: method
Name: index
File: repository.py:45-60
Part of Class: Repository
Class Method Structure:
└── Repository
    └── index

# Result 2 (Score: 0.50, included as context)
Type: class
Name: Repository
File: repository.py:10-100
Class Structure:
└── Methods:
    ├── __init__
    ├── index
    └── search
```

## Usage

Simply initialize the Repository object and hierarchical chunking will be used automatically:

```python
from coderag import Repository, ChromaDBStore

# Initialize components
vector_store = ChromaDBStore(collection_name="my_collection")

# Create repository
repository = Repository(
    repo_path="/path/to/your/repo",
    vector_store=vector_store
)

# Index the repository
repository.index()

# Search with hierarchical results
results = repository.search("method to process files")

# Access hierarchical information
for result in results:
    metadata = result["metadata"]

    if metadata["type"] == "class":
        print(f"Class: {metadata['name']}")
        if "children" in metadata:
            print("Methods:", ", ".join(m.split(":")[-1] for m in metadata["children"]))
    else:
        print(f"Method: {metadata['name']}")
        if "parent" in metadata:
            print(f"In class: {metadata['parent'].split(':')[-2]}")
```

## Examples

See the example scripts in the examples directory:

- [simple_hierarchical.py](../examples/simple_hierarchical.py): A minimal example showing basic usage
- [hierarchical_chunking_example.py](../examples/hierarchical_chunking_example.py): A comprehensive example with detailed output

## Limitations

- Currently, hierarchical chunking is focused on class-method relationships
- Support varies by language (best for Python, JavaScript, TypeScript, and Java)
- Very large classes might be split across multiple chunks, affecting hierarchy

## Future Improvements

Future versions may include:

- Support for more languages
- Deeper hierarchy levels (nested classes, namespaces, etc.)
- Improved handling of large classes
