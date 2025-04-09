import json
from datetime import datetime
from typing import Dict, Any, Optional, List

from .constants import IMPORTANT_METADATA_KEYS
from .logger import Logger

logger = Logger("metadata")

def extract_metadata(notebook: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract important metadata from a Jupyter notebook.
    
    Args:
        notebook: Parsed notebook object
        
    Returns:
        Dictionary of important metadata
    """
    metadata = {}
    
    # Extract notebook-level metadata
    if 'metadata' in notebook:
        nb_metadata = notebook['metadata']
        
        # Handle important fields
        for key in IMPORTANT_METADATA_KEYS:
            if key in nb_metadata:
                metadata[key] = nb_metadata[key]
        
        # Special handling for kernelspec
        if 'kernelspec' in nb_metadata:
            metadata['kernel_name'] = nb_metadata['kernelspec'].get('name', 'unknown')
            metadata['kernel_display_name'] = nb_metadata['kernelspec'].get('display_name', 'Unknown')
        
        # Special handling for language_info
        if 'language_info' in nb_metadata:
            metadata['language'] = nb_metadata['language_info'].get('name', 'unknown')
            metadata['language_version'] = nb_metadata['language_info'].get('version', 'unknown')
    
    # Add cell counts
    cell_counts = {}
    if 'cells' in notebook:
        all_cells = notebook['cells']
        cell_counts['total'] = len(all_cells)
        
        # Count by cell type
        cell_types = {}
        for cell in all_cells:
            cell_type = cell.get('cell_type', 'unknown')
            cell_types[cell_type] = cell_types.get(cell_type, 0) + 1
        
        cell_counts['by_type'] = cell_types
        
        # Count code cells with outputs
        code_cells_with_output = 0
        for cell in all_cells:
            if cell.get('cell_type') == 'code' and 'outputs' in cell and cell['outputs']:
                code_cells_with_output += 1
        
        cell_counts['code_cells_with_output'] = code_cells_with_output
    
    metadata['cell_counts'] = cell_counts
    
    # Add timestamp for extraction
    metadata['extraction_date'] = datetime.now().isoformat()
    
    return metadata

def format_metadata_as_markdown(metadata: Dict[str, Any]) -> str:
    """
    Format metadata as Markdown.
    
    Args:
        metadata: Dictionary of metadata
        
    Returns:
        Formatted markdown string
    """
    md_lines = ["## Notebook Metadata", ""]
    
    # Basic metadata
    if 'title' in metadata:
        md_lines.append(f"**Title:** {metadata['title']}")
    
    if 'authors' in metadata:
        authors = metadata['authors']
        if isinstance(authors, list):
            author_str = ", ".join(str(a) for a in authors)
        else:
            author_str = str(authors)
        md_lines.append(f"**Authors:** {author_str}")
    
    # Language and kernel
    lang_parts = []
    if 'language' in metadata:
        lang_parts.append(f"{metadata['language']}")
        if 'language_version' in metadata:
            lang_parts.append(f"v{metadata['language_version']}")
    
    if lang_parts:
        md_lines.append(f"**Language:** {' '.join(lang_parts)}")
    
    if 'kernel_display_name' in metadata:
        md_lines.append(f"**Kernel:** {metadata['kernel_display_name']}")
    
    # Dates
    if 'creation_date' in metadata:
        md_lines.append(f"**Created:** {metadata['creation_date']}")
    
    if 'last_modified' in metadata:
        md_lines.append(f"**Last Modified:** {metadata['last_modified']}")
    
    # Cell statistics
    if 'cell_counts' in metadata:
        counts = metadata['cell_counts']
        md_lines.append("")
        md_lines.append("### Cell Statistics")
        md_lines.append(f"**Total Cells:** {counts.get('total', 0)}")
        
        if 'by_type' in counts:
            md_lines.append("")
            md_lines.append("**Cell Types:**")
            for cell_type, count in counts['by_type'].items():
                md_lines.append(f"- {cell_type}: {count}")
        
        if 'code_cells_with_output' in counts:
            md_lines.append(f"**Code Cells with Output:** {counts['code_cells_with_output']}")
    
    # Tags
    if 'tags' in metadata and metadata['tags']:
        md_lines.append("")
        md_lines.append("### Tags")
        if isinstance(metadata['tags'], list):
            for tag in metadata['tags']:
                md_lines.append(f"- {tag}")
        else:
            md_lines.append(str(metadata['tags']))
    
    # Add extraction date
    if 'extraction_date' in metadata:
        md_lines.append("")
        md_lines.append(f"*Extracted on: {metadata['extraction_date']}*")
    
    return "\n".join(md_lines)

def format_metadata_as_json(metadata: Dict[str, Any]) -> str:
    """
    Format metadata as JSON.
    
    Args:
        metadata: Dictionary of metadata
        
    Returns:
        Formatted JSON string
    """
    try:
        return json.dumps(metadata, indent=2)
    except Exception as e:
        logger.error(f"Error formatting metadata as JSON: {str(e)}")
        return "{}"

def get_cell_metadata(cell: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract important metadata from a cell.
    
    Args:
        cell: Parsed cell object
        
    Returns:
        Dictionary of important cell metadata
    """
    cell_metadata = {}
    
    if 'metadata' in cell:
        # Extract tags
        if 'tags' in cell['metadata']:
            cell_metadata['tags'] = cell['metadata']['tags']
        
        # Extract collapsed/hidden state
        if 'collapsed' in cell['metadata']:
            cell_metadata['collapsed'] = cell['metadata']['collapsed']
        
        if 'hidden' in cell['metadata']:
            cell_metadata['hidden'] = cell['metadata']['hidden']
    
    # For code cells, get execution count
    if cell.get('cell_type') == 'code' and 'execution_count' in cell:
        cell_metadata['execution_count'] = cell['execution_count']
    
    return cell_metadata
