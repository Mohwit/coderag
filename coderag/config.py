"""
Configuration module for CodeRAG.

This module contains default settings and configuration options for the CodeRAG package.
"""

import logging
import os
from pathlib import Path

# Default logging configuration
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'

# Repository parsing defaults
DEFAULT_EXCLUDE_DIRS = ['.git', 'node_modules', '__pycache__', '.venv', 'venv', 'env']
DEFAULT_EXCLUDE_EXTENSIONS = ['.pyc', '.pyo', '.pyd', '.so', '.dll', '.exe', '.bin']

# Language configurations
LANGUAGE_CONFIGS = {
    'python': {
        'extensions': ['.py'],
    },
    'javascript': {
        'extensions': ['.js', '.jsx'],
    },
    'typescript': {
        'extensions': ['.ts', '.tsx'],
    },
    'java': {
        'extensions': ['.java'],
    }
}

# Language-specific node types for tree-sitter parsing
LANGUAGE_NODE_TYPES = {
    'python': {
        'class': 'class_definition',
        'function': 'function_definition',
        'import': ['import_statement', 'import_from_statement'],
        'control_flow': [
            "if_statement", "for_statement", "while_statement", 
            "try_statement", "with_statement"
        ],
        'assignment': [
            "assignment", "expression_statement", "augmented_assignment"
        ]
    },
    'javascript': {
        'class': 'class_declaration',
        'function': ['function_declaration', 'method_definition', 'arrow_function'],
        'import': ['import_statement', 'import_specifier'],
        'control_flow': [
            "if_statement", "for_statement", "while_statement", 
            "try_statement", "with_statement"
        ],
        'assignment': [
            "assignment_expression", "variable_declaration", "expression_statement"
        ]
    },
    'typescript': {
        'class': 'class_declaration',
        'function': ['function_declaration', 'method_definition', 'arrow_function'],
        'import': ['import_statement', 'import_specifier'],
        'control_flow': [
            "if_statement", "for_statement", "while_statement", 
            "try_statement", "with_statement"
        ],
        'assignment': [
            "assignment_expression", "variable_declaration", "expression_statement"
        ]
    },
    'java': {
        'class': 'class_declaration',
        'function': 'method_declaration',
        'import': ['import_declaration'],
        'control_flow': [
            "if_statement", "for_statement", "while_statement", "try_statement"
        ],
        'assignment': [
            "assignment_expression", "variable_declaration", "expression_statement"
        ]
    }
}

# Embedding defaults
DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_EMBEDDING_BATCH_SIZE = 32

# Storage defaults
DEFAULT_COLLECTION_NAME = "code_embeddings"
DEFAULT_VECTOR_STORE_DIR = os.path.join(str(Path.home()), ".coderag", "vector_store")
DEFAULT_BATCH_SIZE = 100

# Initialize logging
def setup_logging(level=DEFAULT_LOG_LEVEL, log_file=None):
    """Set up logging configuration."""
    handlers = [logging.StreamHandler()]
    
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=level,
        format=DEFAULT_LOG_FORMAT,
        handlers=handlers
    ) 