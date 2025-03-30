# HYDE and Reranking in CodeRAG

## Overview

CodeRAG supports two advanced retrieval techniques to improve search results:

1. **HYDE (HYpothetical Document Embeddings)**: Generates a hypothetical code summary that would answer the query, then uses that for embedding-based search.
2. **Reranking**: Uses a specialized ColBERT model to rerank initial search results based on semantic relevance.

## How It Works

### HYDE

1. When a search query is received, CodeRAG first generates a hypothetical code summary using Claude.
2. This summary describes what an ideal code snippet answering the query would look like.
3. The summary is embedded and used for vector similarity search instead of the original query.
4. This approach often leads to more precise results by bridging the query-document semantic gap.

### Reranking

1. After initial vector similarity search, results are passed through a ColBERT reranker.
2. The reranker compares the query against each result using fine-grained token-level interactions.
3. Results are reordered based on semantic relevance scores.
4. Final scores are normalized to maintain consistency with the rest of the system.

## Usage

Enable these features when initializing the Repository:

```python
from coderag import Repository, ChromaDBStore

repo = Repository(
    repo_path="./my_repo",
    vector_store=vector_store,
    use_hyde=True,        # Enable HYDE
    use_reranking=True    # Enable reranking
)
```

You can also toggle these features on/off after initialization:

```python
# Disable HYDE for a specific search
repo.use_hyde = False

# Enable reranking for a specific search
repo.use_reranking = True
```

## Example Results

Here's how the same query might return different results with these features:

1. Basic Search:

```python
results = repo.search("find methods that process abstract syntax trees", top_k=3)
# Returns results based on direct query embedding
```

2. With HYDE:

```python
repo.use_hyde = True
results = repo.search("find methods that process abstract syntax trees", top_k=3)
# Returns results based on hypothetical code summary embedding
```

3. With HYDE and Reranking:

```python
repo.use_hyde = True
repo.use_reranking = True
results = repo.search("find methods that process abstract syntax trees", top_k=3)
# Returns reranked results based on hypothetical code summary
```

## Benefits

1. **HYDE Benefits**:

   - Better handling of natural language queries
   - Improved semantic matching
   - More relevant results for implementation-focused queries

2. **Reranking Benefits**:
   - More accurate result ordering
   - Better handling of code-specific context
   - Improved relevance for complex queries

## Limitations

1. **HYDE**:

   - Requires API access to Claude
   - Slightly slower due to summary generation
   - May not improve results for already well-structured queries

2. **Reranking**:
   - Additional computational overhead
   - May reorder results in unexpected ways for very similar matches

## Examples

See the example scripts in the examples directory:

- [hyde_reranking_example.py](../examples/hyde_reranking_example.py): Demonstrates HYDE and reranking features
