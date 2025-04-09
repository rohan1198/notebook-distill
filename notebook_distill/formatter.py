import re
import base64
from typing import Dict, Any, Optional, Tuple, List

from .constants import (
    CELL_TYPE_CODE, CELL_TYPE_MARKDOWN, CELL_TYPE_RAW,
    OUTPUT_TEXT_PLAIN, OUTPUT_TEXT_HTML, OUTPUT_TEXT_LATEX, OUTPUT_TEXT_MARKDOWN,
    OUTPUT_IMAGE_PNG, OUTPUT_IMAGE_JPEG, OUTPUT_IMAGE_SVG, OUTPUT_APPLICATION_JSON,
    IMAGE_CONTENT_NOTE, WIDGET_CONTENT_NOTE,
    LATEX_INLINE_MARKER, LATEX_BLOCK_START_MARKER, LATEX_BLOCK_END_MARKER,
    CODE_BLOCK_START_MARKER, CODE_BLOCK_END_MARKER
)
from .html_converter import convert_html_to_markdown
from .metadata import get_cell_metadata
from .logger import Logger

logger = Logger("formatter")

def format_markdown_cell(source: str) -> str:
    """
    Format a markdown cell for LLM consumption.
    
    Args:
        source: Markdown cell content
        
    Returns:
        Formatted markdown
    """
    # Ensure LaTeX equations are properly formatted
    # Preserve block equations
    formatted = re.sub(
        r'\$\$(.*?)\$\$',
        lambda m: f"{LATEX_BLOCK_START_MARKER}\n{m.group(1).strip()}\n{LATEX_BLOCK_END_MARKER}",
        source,
        flags=re.DOTALL
    )
    
    # Preserve inline equations
    formatted = re.sub(
        r'\$([^\$]+?)\$',
        lambda m: f"{LATEX_INLINE_MARKER}{m.group(1).strip()}{LATEX_INLINE_MARKER}",
        formatted
    )
    
    # Ensure proper spacing after headers
    formatted = re.sub(r'(#+)(\s*)(.*?)(\n|$)', r'\1 \3\4', formatted)
    
    return formatted.strip() + "\n\n"

def format_code_cell(source: str, cell_metadata: Dict[str, Any] = None) -> str:
    """
    Format a code cell for LLM consumption.
    
    Args:
        source: Code cell content
        cell_metadata: Optional cell metadata
        
    Returns:
        Formatted code block
    """
    # Add execution count if available
    prefix = ""
    if cell_metadata and 'execution_count' in cell_metadata:
        count = cell_metadata['execution_count']
        if count is not None:
            prefix = f"[{count}] "
    
    # Add code tags
    formatted = f"{CODE_BLOCK_START_MARKER}python\n{source.strip()}\n{CODE_BLOCK_END_MARKER}\n\n"
    
    # Add metadata prefix if needed
    if prefix:
        formatted = f"{prefix}{formatted}"
    
    return formatted

def format_raw_cell(source: str) -> str:
    """
    Format a raw cell for LLM consumption.
    
    Args:
        source: Raw cell content
        
    Returns:
        Formatted raw text
    """
    return f"{CODE_BLOCK_START_MARKER}\n{source.strip()}\n{CODE_BLOCK_END_MARKER}\n\n"

def format_output(output: Dict[str, Any], max_output_length: Optional[int] = None) -> Optional[str]:
    """
    Format a cell output for LLM consumption.
    
    Args:
        output: Cell output object
        max_output_length: Maximum output length
        
    Returns:
        Formatted output or None if output cannot be formatted
    """
    output_type = output.get('output_type')
    
    if output_type == 'stream':
        if 'text' in output:
            text = output['text']
            if isinstance(text, list):
                text = ''.join(text)
            if max_output_length and len(text) > max_output_length:
                text = text[:max_output_length] + "... [truncated]"
            return f"**Output:**\n{CODE_BLOCK_START_MARKER}\n{text.strip()}\n{CODE_BLOCK_END_MARKER}\n\n"
    
    elif output_type in ['execute_result', 'display_data']:
        if 'data' in output:
            data = output['data']
            
            # Handle text/plain (most common)
            if OUTPUT_TEXT_PLAIN in data:
                text = data[OUTPUT_TEXT_PLAIN]
                if isinstance(text, list):
                    text = ''.join(text)
                if max_output_length and len(text) > max_output_length:
                    text = text[:max_output_length] + "... [truncated]"
                return f"**Result:**\n{CODE_BLOCK_START_MARKER}\n{text.strip()}\n{CODE_BLOCK_END_MARKER}\n\n"
            
            # Handle text/html
            elif OUTPUT_TEXT_HTML in data:
                html = data[OUTPUT_TEXT_HTML]
                if isinstance(html, list):
                    html = ''.join(html)
                markdown, complex_html = convert_html_to_markdown(html)
                if max_output_length and len(markdown) > max_output_length:
                    markdown = markdown[:max_output_length] + "... [truncated]"
                return f"**HTML Output:**\n{markdown}\n\n"
            
            # Handle text/latex
            elif OUTPUT_TEXT_LATEX in data:
                latex = data[OUTPUT_TEXT_LATEX]
                if isinstance(latex, list):
                    latex = ''.join(latex)
                if max_output_length and len(latex) > max_output_length:
                    latex = latex[:max_output_length] + "... [truncated]"
                return f"**LaTeX:**\n{LATEX_BLOCK_START_MARKER}\n{latex.strip()}\n{LATEX_BLOCK_END_MARKER}\n\n"
            
            # Handle text/markdown
            elif OUTPUT_TEXT_MARKDOWN in data:
                markdown = data[OUTPUT_TEXT_MARKDOWN]
                if isinstance(markdown, list):
                    markdown = ''.join(markdown)
                if max_output_length and len(markdown) > max_output_length:
                    markdown = markdown[:max_output_length] + "... [truncated]"
                return f"**Markdown Output:**\n{markdown}\n\n"
            
            # Handle images
            elif any(k in data for k in [OUTPUT_IMAGE_PNG, OUTPUT_IMAGE_JPEG, OUTPUT_IMAGE_SVG]):
                return f"**Image Output:** *{IMAGE_CONTENT_NOTE}*\n\n"
            
            # Handle JSON
            elif OUTPUT_APPLICATION_JSON in data:
                import json
                json_data = data[OUTPUT_APPLICATION_JSON]
                try:
                    if isinstance(json_data, str):
                        formatted_json = json.dumps(json.loads(json_data), indent=2)
                    else:
                        formatted_json = json.dumps(json_data, indent=2)
                    if max_output_length and len(formatted_json) > max_output_length:
                        formatted_json = formatted_json[:max_output_length] + "... [truncated]"
                    return f"**JSON Result:**\n{CODE_BLOCK_START_MARKER}json\n{formatted_json}\n{CODE_BLOCK_END_MARKER}\n\n"
                except Exception as e:
                    logger.error(f"Error formatting JSON: {str(e)}")
                    return f"**JSON Result:** [Error formatting JSON]\n\n"
    
    elif output_type == 'error':
        ename = output.get('ename', 'Error')
        evalue = output.get('evalue', '')
        error_message = f"{ename}: {evalue}"
        if max_output_length and len(error_message) > max_output_length:
            error_message = error_message[:max_output_length] + "... [truncated]"
        return f"**Error:**\n{CODE_BLOCK_START_MARKER}\n{error_message.strip()}\n{CODE_BLOCK_END_MARKER}\n\n"
    
    # If we get here, we don't know how to handle this output type
    return f"**Unhandled Output Type:** {output_type}\n\n"

def format_cell(
    cell: Dict[str, Any], 
    include_code: bool = True,
    include_outputs: bool = True,
    max_output_length: Optional[int] = None
) -> str:
    """
    Format a Jupyter notebook cell for LLM consumption.
    
    Args:
        cell: Notebook cell object
        include_code: Whether to include code cells
        include_outputs: Whether to include outputs
        max_output_length: Maximum output length
        
    Returns:
        Formatted cell content
    """
    cell_type = cell.get('cell_type', '')
    source = cell.get('source', '')
    
    # Convert source to string if it's a list
    if isinstance(source, list):
        source = ''.join(source)
    
    # Get cell metadata for additional context
    cell_metadata = get_cell_metadata(cell)
    
    # Format based on cell type
    if cell_type == CELL_TYPE_MARKDOWN:
        return format_markdown_cell(source)
    
    elif cell_type == CELL_TYPE_CODE and include_code:
        result = []
        
        # Add code if requested
        if include_code:
            result.append(format_code_cell(source, cell_metadata))
        
        # Add outputs if requested
        if include_outputs and 'outputs' in cell and cell['outputs']:
            for output in cell['outputs']:
                formatted_output = format_output(output, max_output_length)
                if formatted_output:
                    result.append(formatted_output)
        
        return ''.join(result)
    
    elif cell_type == CELL_TYPE_RAW:
        return format_raw_cell(source)
    
    return ""

def format_notebook_metadata(metadata: Dict[str, Any]) -> str:
    """
    Format notebook metadata as markdown.
    
    Args:
        metadata: Notebook metadata
        
    Returns:
        Formatted metadata
    """
    from .metadata import format_metadata_as_markdown
    return format_metadata_as_markdown(metadata)
