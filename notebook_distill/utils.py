"""Utility functions for Jupyter notebook extraction."""

import os
import re
import tiktoken
from typing import Dict, Any, Optional, List, Union

from .logger import Logger

logger = Logger("utils")

# Cache the tokenizers to avoid re-initialization
_TOKENIZERS = {}

def estimate_tokens(text: str, model: str = "gpt-4") -> int:
    """
    Estimate the number of tokens in the given text using tiktoken.
    
    Args:
        text: The text to estimate tokens for
        model: The model to estimate tokens for (default: gpt-4)
        
    Returns:
        Estimated token count
    """
    global _TOKENIZERS
    
    if model not in _TOKENIZERS:
        try:
            _TOKENIZERS[model] = tiktoken.encoding_for_model(model)
        except KeyError:
            # Fallback to cl100k_base encoding which is used by gpt-4, gpt-3.5-turbo
            _TOKENIZERS[model] = tiktoken.get_encoding("cl100k_base")
    
    encoding = _TOKENIZERS[model]
    tokens = encoding.encode(text)
    return len(tokens)

def get_notebook_title(notebook_path: str, notebook_data: Optional[Dict[str, Any]] = None) -> str:
    """
    Extract a human-readable title from a notebook path or metadata.
    
    Args:
        notebook_path: Path to the notebook file
        notebook_data: Optional notebook data object
        
    Returns:
        Human-readable title
    """
    # First try to get title from metadata
    if notebook_data and 'metadata' in notebook_data:
        metadata = notebook_data['metadata']
        if 'title' in metadata:
            return metadata['title']
    
    # Fall back to filename
    filename = os.path.basename(notebook_path)
    name_without_ext = os.path.splitext(filename)[0]
    
    # Convert CamelCase or snake_case to spaces
    title = re.sub(r'_', ' ', name_without_ext)
    title = re.sub(r'([a-z])([A-Z])', r'\1 \2', title)
    
    # Capitalize first letter of each word
    return title.title()

def detect_output_format(output_path: str) -> str:
    """
    Detect the desired output format based on file extension.
    
    Args:
        output_path: Path to output file
        
    Returns:
        Output format (markdown, json, text)
    """
    from .constants import FORMAT_MARKDOWN, FORMAT_JSON, FORMAT_TEXT
    
    if not output_path:
        return FORMAT_MARKDOWN
    
    ext = os.path.splitext(output_path)[1].lower()
    
    if ext in ['.md', '.markdown']:
        return FORMAT_MARKDOWN
    elif ext in ['.json']:
        return FORMAT_JSON
    elif ext in ['.txt']:
        return FORMAT_TEXT
    
    # Default to markdown
    return FORMAT_MARKDOWN

def format_for_output_type(content: str, metadata: Dict[str, Any], format_type: str) -> str:
    """
    Format content for the specified output type.
    
    Args:
        content: Extracted content
        metadata: Notebook metadata
        format_type: Output format (markdown, json, text)
        
    Returns:
        Formatted content
    """
    from .constants import FORMAT_MARKDOWN, FORMAT_JSON, FORMAT_TEXT
    from .metadata import format_metadata_as_markdown, format_metadata_as_json
    
    if format_type == FORMAT_JSON:
        import json
        return json.dumps({
            'metadata': metadata,
            'content': content
        }, indent=2)
    
    elif format_type == FORMAT_TEXT:
        # Convert markdown to plain text
        plain_text = content
        
        # Remove code block markers
        plain_text = re.sub(r'```[^\n]*\n', '', plain_text)
        plain_text = re.sub(r'```', '', plain_text)
        
        # Convert headers
        plain_text = re.sub(r'^(#+)\s+(.+)$', lambda m: m.group(2).upper(), plain_text, flags=re.MULTILINE)
        
        # Convert bold and italic
        plain_text = re.sub(r'\*\*(.+?)\*\*', r'\1', plain_text)
        plain_text = re.sub(r'\*(.+?)\*', r'\1', plain_text)
        
        # Add metadata as text
        metadata_text = []
        for key, value in metadata.items():
            if isinstance(value, dict):
                metadata_text.append(f"{key.upper()}:")
                for k, v in value.items():
                    metadata_text.append(f"  {k}: {v}")
            else:
                metadata_text.append(f"{key}: {value}")
        
        if metadata_text:
            metadata_str = "NOTEBOOK METADATA:\n" + "\n".join(metadata_text)
            return f"{metadata_str}\n\n{plain_text}"
        
        return plain_text
    
    # Default to markdown
    metadata_md = format_metadata_as_markdown(metadata)
    
    # Fix: Use a variable for the separator instead of an f-string with nested escapes
    separator = "---\n\n" if metadata_md else ""
    return f"{metadata_md}\n\n{separator}{content}"

def save_to_file(content: str, output_path: str) -> None:
    """
    Save content to file.
    
    Args:
        content: Content to save
        output_path: Path to output file
    """
    try:
        directory = os.path.dirname(output_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
            
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        logger.info(f"Successfully saved output to {output_path}")
    except Exception as e:
        logger.error(f"Error saving to file {output_path}: {str(e)}")
        raise
