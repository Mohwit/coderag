import os
from typing import List, Dict, Any, Generator, Tuple, Optional, Iterator
from pathlib import Path
import mimetypes
from tree_sitter import Language, Parser
import uuid

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
        'method': 'function_definition',  # In Python methods are function definitions within classes
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
        'method': 'method_definition',
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
        'method': 'method_definition',
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
        'method': 'method_declaration',
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
                 exclude_extensions: List[str] = None,
                 language_config: Dict[str, Any] = None,
                 verbose: bool = False):
        """
        Initialize the code parser with repository path and optional configurations.
        
        Args:
            repo_path: Path to the repository
            exclude_dirs: List of directory names to exclude
            exclude_extensions: List of file extensions to exclude
            language_config: Optional custom language configuration
            verbose: Whether to print detailed progress information
        """
        self.repo_path = Path(repo_path)
        self.exclude_dirs = exclude_dirs or []
        self.exclude_extensions = exclude_extensions or []
        self.language_config = language_config or {}
        self.verbose = verbose
        
        # Initialize language parsers
        self.parsers = {}
        self.init_parsers()
    
    def init_parsers(self):
        """Initialize tree-sitter parsers for supported languages."""
        try:
            self._log("Initializing language parsers...")
            for lang, config in self.LANGUAGE_CONFIGS.items():
                try:
                    self._log(f"Setting up parser for {lang}")
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
                    self._log(f"Successfully initialized {lang} parser")
                except Exception as e:
                    self._log(f"Failed to initialize {lang} parser: {str(e)}")
                    continue
                    
        except Exception as e:
            self._log(f"Error during parser initialization: {str(e)}")
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
    
    def walk_repository(self) -> Iterator[Path]:
        """Walk through the repository and yield valid code files."""
        total_files = 0
        processed_files = 0
        skipped_files = 0
        
        self._log(f"Walking repository at {self.repo_path}")
        self._log(f"Excluding directories: {', '.join(self.exclude_dirs)}")
        self._log(f"Excluding extensions: {', '.join(self.exclude_extensions)}")
        
        for root, dirs, files in os.walk(self.repo_path):
            # Remove excluded directories
            excluded_dirs = [d for d in dirs if d in self.exclude_dirs]
            if excluded_dirs:
                self._log(f"Skipping excluded directories in {root}: {', '.join(excluded_dirs)}")
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]
            
            for file in files:
                total_files += 1
                file_path = Path(root) / file
                
                if file_path.suffix in self.exclude_extensions:
                    skipped_files += 1
                    self._log(f"Skipping excluded file: {file_path}")
                    continue
                
                if not self.is_text_file(str(file_path)):
                    skipped_files += 1
                    self._log(f"Skipping non-text file: {file_path}")
                    continue
                
                language = self.get_language_from_extension(file_path)
                if not language:
                    skipped_files += 1
                    self._log(f"Skipping unsupported language file: {file_path}")
                    continue
                
                processed_files += 1
                self._log(f"Processing file ({processed_files}/{total_files - skipped_files}): {file_path}")
                yield file_path
    
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
    
    def _create_class_overview(self, class_node, code_bytes: bytes, language: str) -> str:
        """
        Create a summary version of a class without method implementations.
        
        Args:
            class_node: The class node from tree-sitter
            code_bytes: The code as bytes
            language: The programming language
            
        Returns:
            A string with the class signature, docstring, and method signatures
        """
        name_node = class_node.child_by_field_name("name")
        class_name = self.get_node_text(name_node, code_bytes) if name_node else "UnnamedClass"
        
        body_node = class_node.child_by_field_name("body")
        docstring = self.get_docstring(body_node, code_bytes) if body_node else ""
        
        # Get class header (everything before the body)
        header_end = body_node.start_byte if body_node else class_node.end_byte
        class_header = code_bytes[class_node.start_byte:header_end].decode('utf8')
        
        # Get method signatures
        method_signatures = []
        if body_node:
            for child in body_node.children:
                method_type = LANGUAGE_NODE_TYPES[language].get('method')
                if isinstance(method_type, list):
                    is_method = child.type in method_type
                else:
                    is_method = child.type == method_type
                
                if is_method:
                    method_name_node = child.child_by_field_name("name")
                    if method_name_node:
                        method_name = self.get_node_text(method_name_node, code_bytes)
                        
                        # Get parameters
                        params = []
                        parameters_node = child.child_by_field_name("parameters")
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
                        
                        # Get method signature
                        method_signature = f"def {method_name}({', '.join(params)})" if language == 'python' else f"{method_name}({', '.join(params)})"
                        method_signatures.append(method_signature)
        
        # Combine everything
        overview = class_header
        if docstring:
            overview += f"\n    {docstring}"
        
        overview += "\n\n    # Method signatures (implementations omitted):"
        for signature in method_signatures:
            overview += f"\n    # - {signature}"
        
        overview += "\n"
        
        return overview
    
    def _create_method_with_class_context(self, class_name: str, method_node, code_bytes: bytes) -> str:
        """
        Create a method chunk with minimal class context.
        
        Args:
            class_name: The name of the containing class
            method_node: The method node from tree-sitter
            code_bytes: The code as bytes
            
        Returns:
            A string with the method and minimal class context
        """
        method_text = self.get_node_text(method_node, code_bytes)
        
        # Add class context
        context = f"# In class: {class_name}\n{method_text}"
        return context
    
    def _process_class_hierarchical(self, class_node, code_bytes: bytes, language: str, file_path: str) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Process a class node using hierarchical chunking.
        
        Args:
            class_node: The class node from tree-sitter
            code_bytes: The code as bytes
            language: The programming language
            file_path: Path to the source file
            
        Returns:
            List of tuples containing (chunk_text, metadata)
        """
        name_node = class_node.child_by_field_name("name")
        if not name_node:
            return []
        
        class_name = self.get_node_text(name_node, code_bytes)
        class_id = str(uuid.uuid4())
        
        # Get docstring if available
        docstring = self.get_docstring(class_node, code_bytes)
        
        # Create class metadata
        class_metadata = {
            'id': class_id,
            'file_path': file_path,
            'language': language,
            'type': 'class',
            'name': class_name,
            'start_line': class_node.start_point[0] + 1,
            'end_line': class_node.end_point[0] + 1,
            'start_col': class_node.start_point[1],
            'end_col': class_node.end_point[1],
            'docstring': docstring or '',
            'level': 1,  # Class level in hierarchy
            'children': []  # Will be populated with method IDs
        }
        
        # Create class overview (without method implementations)
        class_overview = self._create_class_overview(class_node, code_bytes, language)
        
        # Process methods
        method_ids = []
        chunks = [(class_overview, class_metadata)]
        
        # Find all method nodes
        body_node = class_node.child_by_field_name("body")
        if body_node:
            for child in body_node.children:
                method_type = LANGUAGE_NODE_TYPES[language].get('method')
                if isinstance(method_type, list):
                    is_method = child.type in method_type
                else:
                    is_method = child.type == method_type
                
                if is_method:
                    method_id = str(uuid.uuid4())
                    method_name_node = child.child_by_field_name("name")
                    if method_name_node:
                        method_name = self.get_node_text(method_name_node, code_bytes)
                        method_text = self.get_node_text(child, code_bytes)
                        
                        # Get method docstring
                        method_docstring = self.get_docstring(child, code_bytes)
                        
                        # Create method metadata
                        method_metadata = {
                            'id': method_id,
                            'file_path': file_path,
                            'language': language,
                            'type': 'method',
                            'name': method_name,
                            'class': class_name,  # Add class name for context
                            'parent': class_id,  # Link to parent class
                            'start_line': child.start_point[0] + 1,
                            'end_line': child.end_point[0] + 1,
                            'start_col': child.start_point[1],
                            'end_col': child.end_point[1],
                            'docstring': method_docstring or '',
                            'level': 2  # Method level in hierarchy
                        }
                        
                        # Add class context to method text
                        method_with_context = f"# In class: {class_name}\n{method_text}"
                        
                        chunks.append((method_with_context, method_metadata))
                        method_ids.append(method_id)
        
        # Update the class chunk with children IDs
        class_metadata['children'] = method_ids
        
        return chunks
    
    def extract_code_chunk(self, file_path: str, code_bytes: bytes, language: str) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Extract meaningful code chunks from a file.
        
        This method parses the file and extracts individual classes, functions, and methods
        as separate chunks with metadata.
        
        Args:
            file_path: Path to the file
            code_bytes: Raw file bytes
            language: Language type (python, javascript, etc.)
            
        Returns:
            List of tuples containing (code_text, metadata)
        """
        try:
            self._log(f"Extracting code chunks from {file_path}")
            parser = self.parsers[language]
            tree = parser.parse(code_bytes)
            root_node = tree.root_node
            
            chunks = []
            
            # Get all classes first
            class_nodes = self._get_class_nodes(root_node, language)
            processed_class_ranges = []
            
            # Process classes with hierarchical chunking
            for class_node in class_nodes:
                self._log("Processing class chunks")
                try:
                    class_chunks = self._process_class_hierarchical(
                        class_node, code_bytes, language, file_path)
                    chunks.extend(class_chunks)
                    processed_class_ranges.append((
                        class_chunks[0][1]['start_line'],  # First chunk is class
                        class_chunks[0][1]['end_line']
                    ))
                except Exception as e:
                    self._log(f"Error processing class: {str(e)}")
                    continue
            
            # Process standalone functions (not within any class)
            for child in root_node.children:
                # Skip if this is a class (already processed)
                if self._is_class_node(child, language):
                    continue
                    
                # Process function if it's a standalone function
                if self._is_function_node(child, language):
                    try:
                        # Check if this function is within any of the processed class ranges
                        start_line = child.start_point[0] + 1
                        end_line = child.end_point[0] + 1
                        
                        is_within_class = any(
                            start_line >= class_start and end_line <= class_end
                            for class_start, class_end in processed_class_ranges
                        )
                        
                        if not is_within_class:
                            func_text = self.get_node_text(child, code_bytes)
                            
                            # Extract function name
                            func_name = None
                            name_node = None
                            
                            if language == 'python':
                                for c in child.children:
                                    if c.type == 'identifier':
                                        name_node = c
                                        func_name = self.get_node_text(c, code_bytes)
                                        break
                            elif language in ['javascript', 'typescript']:
                                for c in child.children:
                                    if c.type == 'identifier':
                                        name_node = c
                                        func_name = self.get_node_text(c, code_bytes)
                                        break
                                    # For anonymous functions, try to find assignment
                                    elif c.type == 'formal_parameters' and child.parent and child.parent.type == 'variable_declarator':
                                        for sibling in child.parent.children:
                                            if sibling.type == 'identifier':
                                                name_node = sibling
                                                func_name = self.get_node_text(sibling, code_bytes)
                                                break
                            elif language == 'java':
                                for c in child.children:
                                    if c.type == 'identifier':
                                        name_node = c
                                        func_name = self.get_node_text(c, code_bytes)
                                        break
                            
                            # Get function body if available
                            body = None
                            for c in child.children:
                                if c.type in ['block', 'function_body']:
                                    body = self.get_node_text(c, code_bytes)
                                    break
                            
                            # Get function parameters
                            parameters = self._extract_function_parameters(child, code_bytes, language)
                            
                            # Get docstring if available
                            docstring = self.get_docstring(child, code_bytes)
                            
                            # Create metadata
                            chunk_id = str(uuid.uuid4())
                            metadata = {
                                'id': chunk_id,
                                'file_path': file_path,
                                'language': language,
                                'type': 'function',
                                'name': func_name or 'anonymous_function',
                                'start_line': child.start_point[0] + 1,
                                'end_line': child.end_point[0] + 1,
                                'start_col': child.start_point[1],
                                'end_col': child.end_point[1],
                                'parameters': parameters,
                                'docstring': docstring or '',
                                'level': 1  # Top-level function
                            }
                            
                            chunks.append((func_text, metadata))
                    except Exception as e:
                        self._log(f"Error processing function: {str(e)}")
                        continue
            
            # Sort chunks by their position in the file
            chunks.sort(key=lambda x: x[1]['start_line'])
            self._log(f"Extracted total of {len(chunks)} chunks")
            return chunks
            
        except Exception as e:
            self._log(f"Error extracting chunks: {str(e)}")
            return []
    
    def _get_class_nodes(self, root_node, language):
        """Get all class nodes from the tree-sitter parse tree."""
        class_nodes = []
        for child in root_node.children:
            if child.type == LANGUAGE_NODE_TYPES[language]['class']:
                class_nodes.append(child)
        return class_nodes
    
    def _is_class_node(self, node, language):
        """Check if a node is a class node."""
        return node.type == LANGUAGE_NODE_TYPES[language]['class']
    
    def _is_function_node(self, node, language):
        """Check if a node is a function node."""
        return node.type in LANGUAGE_NODE_TYPES[language]['function']
    
    def _extract_function_parameters(self, node, code_bytes: bytes, language: str):
        """Extract function parameters from a node."""
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
        return ','.join(params)
    
    def parse_file(self, file_path: Path) -> List[Tuple[str, Dict[str, Any]]]:
        """Parse a single file and return chunks with metadata."""
        try:
            self._log(f"Parsing file: {file_path}")
            
            # Read file content
            with open(file_path, 'rb') as f:
                code_bytes = f.read()
                
            # Get language and parser
            language = self.get_language_from_extension(file_path)
            if not language or language not in self.parsers:
                self._log(f"No parser available for {file_path}")
                return []
                
            parser = self.parsers[language]
            self._log(f"Using {language} parser")
            
            # Parse code and extract chunks
            tree = parser.parse(code_bytes)
            self._log("Code parsed successfully, extracting chunks...")
            chunks = self.extract_code_chunk(str(file_path), code_bytes, language)
            self._log(f"Extracted {len(chunks)} code chunks")
            
            return chunks
            
        except Exception as e:
            self._log(f"Error parsing file {file_path}: {str(e)}")
            return []
    
    def _log(self, message: str) -> None:
        """Print message if verbose mode is enabled."""
        if self.verbose:
            print(f"[CodeRAG Parser] {message}") 