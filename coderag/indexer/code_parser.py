import os
from typing import List, Dict, Any, Generator, Tuple, Optional
from pathlib import Path
import mimetypes
from tree_sitter import Language, Parser
import logging

# Import language modules
import tree_sitter_python
import tree_sitter_javascript
import tree_sitter_typescript as tstypescript
import tree_sitter_java

# Define language-specific node types
LANGUAGE_NODE_TYPES = {
    'python': {
        'class': 'class_definition',
        'function': 'function_definition',
        'import': ['import_statement', 'import_from_statement'],
        'control_flow': [
            "if_statement",
            "for_statement",
            "while_statement",
            "try_statement",
            "with_statement"
        ],
        'assignment': [
            "assignment",
            "expression_statement",
            "augmented_assignment"
        ]
    },
    'javascript': {
        'class': 'class_declaration',
        'function': ['function_declaration', 'method_definition', 'arrow_function'],
        'import': ['import_statement', 'import_specifier'],
        'control_flow': [
            "if_statement",
            "for_statement",
            "while_statement",
            "try_statement",
            "with_statement"
        ],
        'assignment': [
            "assignment_expression",
            "variable_declaration",
            "expression_statement"
        ]
    },
    'typescript': {
        'class': 'class_declaration',
        'function': ['function_declaration', 'method_definition', 'arrow_function'],
        'import': ['import_statement', 'import_specifier'],
        'control_flow': [
            "if_statement",
            "for_statement",
            "while_statement",
            "try_statement",
            "with_statement"
        ],
        'assignment': [
            "assignment_expression",
            "variable_declaration",
            "expression_statement"
        ]
    },
    'java': {
        'class': 'class_declaration',
        'function': 'method_declaration',
        'import': ['import_declaration'],
        'control_flow': [
            "if_statement",
            "for_statement",
            "while_statement",
            "try_statement"
        ],
        'assignment': [
            "assignment_expression",
            "variable_declaration",
            "expression_statement"
        ]
    }
}

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Output to console
        logging.FileHandler('coderag.log')  # Output to file
    ]
)

class CodeParser:
    """Parser for extracting and processing code from repositories using tree-sitter."""
    
    # Supported languages and their file extensions
    LANGUAGE_CONFIGS = {
        'python': {
            'extensions': ['.py'],
            'module': tree_sitter_python
        },
        'javascript': {
            'extensions': ['.js', '.jsx'],
            'module': tree_sitter_javascript
        },
        'typescript': {
            'extensions': ['.ts', '.tsx'],
            'module': tstypescript
        },
        'java': {
            'extensions': ['.java'],
            'module': tree_sitter_java
        }
    }
    
    def __init__(self, 
                 repo_path: str,
                 exclude_dirs: List[str] = None,
                 exclude_extensions: List[str] = None):
        """
        Initialize the code parser.
        
        Args:
            repo_path: Path to the repository
            exclude_dirs: List of directory names to exclude
            exclude_extensions: List of file extensions to exclude
        """
        self.repo_path = Path(repo_path)
        self.exclude_dirs = set(exclude_dirs or ['.git', 'node_modules', '__pycache__', '.venv'])
        self.exclude_extensions = set(exclude_extensions or ['.pyc', '.pyo', '.pyd', '.so'])
        
        # Initialize tree-sitter parsers
        self.parsers = {}
        self.init_parsers()
    
    def init_parsers(self):
        """Initialize tree-sitter parsers for supported languages."""
        try:
            for lang, config in self.LANGUAGE_CONFIGS.items():
                try:
                    if lang == 'typescript':
                        # TypeScript often has a different structure
                        try:
                            lang_obj = Language(tstypescript.language_typescript())
                        except AttributeError:
                            # Some versions use this format instead
                            lang_obj = Language(tstypescript.get_language("typescript"))
                    else:
                        lang_obj = Language(config['module'].language())
                    
                    parser = Parser()
                    parser.language = lang_obj
                    self.parsers[lang] = parser
                except Exception as e:
                    logging.error(f"Failed to initialize {lang} parser: {e}")
                    
        except Exception as e:
            logging.error(f"Error initializing tree-sitter parsers: {str(e)}")
            raise
    
    def get_language_from_extension(self, file_path: Path) -> Optional[str]:
        """Get the programming language based on file extension."""
        extension = file_path.suffix.lower()
        for lang, config in self.LANGUAGE_CONFIGS.items():
            if extension in config['extensions']:
                return lang
        return None
    
    def is_text_file(self, file_path: str) -> bool:
        """Check if a file is a text file using mimetypes."""
        mime, _ = mimetypes.guess_type(file_path)
        if mime is None:
            # If mime type can't be determined, check if it's one of our supported extensions
            extension = Path(file_path).suffix.lower()
            for extensions in self.LANGUAGE_CONFIGS.values():
                if extension in extensions['extensions']:
                    return True
            return False
        
        return mime.startswith('text/') or mime in [
            'application/json',
            'application/javascript',
            'application/x-python',
            'application/typescript'
        ]
    
    def walk_repository(self) -> Generator[Path, None, None]:
        """Walk through repository and yield valid files."""
        total_files = 0
        processed_files = 0
        skipped_files = 0
        
        logging.info(f"Starting repository scan at: {self.repo_path}")
        
        for root, dirs, files in os.walk(self.repo_path):
            # Remove excluded directories
            excluded_dirs = [d for d in dirs if d in self.exclude_dirs]
            if excluded_dirs:
                logging.debug(f"Skipping excluded directories: {', '.join(excluded_dirs)}")
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]
            
            for file in files:
                total_files += 1
                file_path = Path(root) / file
                
                if file_path.suffix in self.exclude_extensions:
                    logging.debug(f"Skipping excluded file: {file_path}")
                    skipped_files += 1
                    continue
                
                if not self.is_text_file(str(file_path)):
                    logging.debug(f"Skipping non-text file: {file_path}")
                    skipped_files += 1
                    continue
                
                language = self.get_language_from_extension(file_path)
                if not language:
                    logging.debug(f"Skipping unsupported language file: {file_path}")
                    skipped_files += 1
                    continue
                
                logging.info(f"Processing file: {file_path} (Language: {language})")
                processed_files += 1
                yield file_path
        
        logging.info(f"Repository scan completed:")
        logging.info(f"Total files found: {total_files}")
        logging.info(f"Files processed: {processed_files}")
        logging.info(f"Files skipped: {skipped_files}")
    
    def get_node_text(self, node, code_bytes: bytes) -> str:
        """Get the text content of a node."""
        return code_bytes[node.start_byte:node.end_byte].decode('utf8')
    
    def get_docstring(self, node, code_bytes: bytes) -> str:
        """Extract docstring from a node if present."""
        if not node or not node.children:
            return ""
            
        for child in node.children:
            if child.type == "expression_statement":
                string_node = child.children[0] if child.children else None
                if string_node and string_node.type == "string":
                    return self.get_node_text(string_node, code_bytes)
        return ""
    
    def extract_code_chunk(self, content: str, language: str) -> List[Tuple[str, Dict[str, Any]]]:
        """Extract code chunks using tree-sitter parsing."""
        chunks = []
        parser = self.parsers.get(language)
        if not parser:
            logging.warning(f"No parser found for language: {language}")
            return []
        
        try:
            logging.info("=" * 80)
            logging.info(f"Extracting chunks for {language} content")
            logging.info("=" * 80)
            
            code_bytes = content.encode('utf8')
            tree = parser.parse(code_bytes)
            root_node = tree.root_node
            
            # Process imports
            import_nodes = []
            import_types = LANGUAGE_NODE_TYPES[language]['import']
            
            for child in root_node.children:
                if isinstance(import_types, list):
                    if child.type in import_types:
                        import_nodes.append(child)
                elif child.type == import_types:
                    import_nodes.append(child)
            
            if import_nodes:
                import_texts = [self.get_node_text(node, code_bytes) for node in import_nodes]
                combined_imports = '\n'.join(import_texts)
                chunks.append((
                    combined_imports,
                    {
                        'type': 'import',
                        'content': combined_imports,
                        'start_line': str(import_nodes[0].start_point[0] + 1),
                        'end_line': str(import_nodes[-1].end_point[0] + 1)
                    }
                ))
                logging.info("\nImport Chunk:")
                logging.info("-" * 40)
                logging.info(f"Lines: {chunks[-1][1]['start_line']}-{chunks[-1][1]['end_line']}")
                logging.info("Content:")
                logging.info(combined_imports)
                logging.info("-" * 40)
            
            # Process classes and functions
            for child in root_node.children:
                # Process classes
                if child.type == LANGUAGE_NODE_TYPES[language]['class']:
                    name_node = child.child_by_field_name("name")
                    if name_node:
                        class_text = self.get_node_text(child, code_bytes)
                        class_name = self.get_node_text(name_node, code_bytes)
                        body_node = child.child_by_field_name("body")
                        docstring = self.get_docstring(body_node, code_bytes) if body_node else ""
                        
                        chunks.append((
                            class_text,
                            {
                                'type': 'class',
                                'name': class_name,
                                'content': class_text,
                                'start_line': str(child.start_point[0] + 1),
                                'end_line': str(child.end_point[0] + 1),
                                'docstring': docstring
                            }
                        ))
                        logging.info(f"\nClass Chunk: {class_name}")
                        logging.info("-" * 40)
                        logging.info(f"Lines: {chunks[-1][1]['start_line']}-{chunks[-1][1]['end_line']}")
                        logging.info("Content:")
                        logging.info(class_text)
                        logging.info("-" * 40)
                
                # Process functions
                elif isinstance(LANGUAGE_NODE_TYPES[language]['function'], list):
                    if child.type in LANGUAGE_NODE_TYPES[language]['function']:
                        self._process_function_node(child, code_bytes, chunks, language)
                elif child.type == LANGUAGE_NODE_TYPES[language]['function']:
                    self._process_function_node(child, code_bytes, chunks, language)
            
            # Log summary
            logging.info("\nChunking Summary:")
            logging.info(f"Total chunks created: {len(chunks)}")
            logging.info("=" * 80 + "\n")
            
            return sorted(chunks, key=lambda x: int(x[1]['start_line']))
            
        except Exception as e:
            logging.error(f"Error during code chunking: {str(e)}", exc_info=True)
            return []
    
    def _process_function_node(self, node, code_bytes: bytes, chunks: list, language: str):
        """Process a function node and add it to chunks."""
        name_node = node.child_by_field_name("name")
        if name_node:
            func_text = self.get_node_text(node, code_bytes)
            func_name = self.get_node_text(name_node, code_bytes)
            body_node = node.child_by_field_name("body")
            docstring = self.get_docstring(body_node, code_bytes) if body_node else ""
            
            # Get parameters
            params = []
            parameters_node = node.child_by_field_name("parameters")
            if parameters_node:
                for param in parameters_node.children:
                    if language == 'python' and param.type == "identifier":
                        params.append(self.get_node_text(param, code_bytes))
                    elif language == 'java' and param.type == "formal_parameter":
                        param_name = param.child_by_field_name("name")
                        if param_name:
                            params.append(self.get_node_text(param_name, code_bytes))
                    elif language in ['javascript', 'typescript']:
                        if param.type in ["identifier", "formal_parameter"]:
                            params.append(self.get_node_text(param, code_bytes))
            
            chunks.append((
                func_text,
                {
                    'type': 'function',
                    'name': func_name,
                    'content': func_text,
                    'start_line': str(node.start_point[0] + 1),
                    'end_line': str(node.end_point[0] + 1),
                    'docstring': docstring,
                    'parameters': ','.join(params)
                }
            ))
            
            logging.info(f"\nFunction Chunk: {func_name}")
            logging.info("-" * 40)
            logging.info(f"Lines: {chunks[-1][1]['start_line']}-{chunks[-1][1]['end_line']}")
            logging.info(f"Parameters: {', '.join(params)}")
            logging.info("Content:")
            logging.info(func_text)
            logging.info("-" * 40)
    
    def parse_file(self, file_path: Path) -> List[Tuple[str, Dict[str, Any]]]:
        """Parse a single file and return chunks with metadata."""
        try:
            logging.info(f"Starting to parse file: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            relative_path = file_path.relative_to(self.repo_path)
            language = self.get_language_from_extension(file_path)
            
            if not language:
                logging.warning(f"Unsupported language for file: {file_path}")
                return []
            
            logging.info(f"File size: {len(content)} bytes")
            chunks = self.extract_code_chunk(content, language)
            
            # Add file metadata and log results
            processed_chunks = []
            for chunk_content, metadata in chunks:
                processed_chunks.append((
                    chunk_content,
                    {
                        'file_path': str(relative_path),
                        'language': language,
                        'type': metadata.get('type', ''),
                        'name': metadata.get('name', ''),
                        'start_line': metadata.get('start_line', ''),
                        'end_line': metadata.get('end_line', ''),
                        'docstring': metadata.get('docstring', ''),
                        'parameters': metadata.get('parameters', ''),
                        'content': chunk_content
                    }
                ))
            
            logging.info(f"Successfully parsed {len(processed_chunks)} chunks from {file_path}")
            return processed_chunks
            
        except Exception as e:
            logging.error(f"Error parsing file {file_path}: {str(e)}", exc_info=True)
            return [] 