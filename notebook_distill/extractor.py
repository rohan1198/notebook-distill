import nbformat
import nbclient
import os
from typing import Dict, List, Optional, Union, Any

from .formatter import format_cell, format_notebook_metadata
from .chunker import smart_chunk_notebook
from .utils import estimate_tokens, get_notebook_title, format_for_output_type, detect_output_format
from .metadata import extract_metadata
from .logger import Logger

logger = Logger("extractor")

def extract_notebook(
    notebook_path: str,
    include_code: bool = True,
    include_outputs: bool = True,
    max_output_length: Optional[int] = None,
    chunk_size: Optional[int] = None,
    estimate_token_count: bool = False,
    model: str = "gpt-4",
    execute: bool = False,
    include_metadata: bool = True,
    output_format: Optional[str] = None,
    output_path: Optional[str] = None,
    include_metadata_in_chunks: bool = True
) -> Union[str, List[str], Dict[str, Any]]:
    """
    Extract content from a Jupyter notebook and format for LLM consumption.
    
    Args:
        notebook_path: Path to the .ipynb file
        include_code: Whether to include code cells
        include_outputs: Whether to include output cells
        max_output_length: Maximum length for any single output
        chunk_size: If set, split result into chunks of this approximate size
        estimate_token_count: If True, estimate and return token count
        model: Model to use for token estimation (default: gpt-4)
        execute: Whether to execute the notebook before extraction
        include_metadata: Whether to include notebook metadata
        output_format: Output format (markdown, json, text)
        output_path: Path to save output (determines format if output_format not specified)
        include_metadata_in_chunks: Whether to include metadata in each chunk when chunking
        
    Returns:
        - If chunk_size is None, returns a formatted string
        - If chunk_size is not None, returns a list of strings
        - If estimate_token_count is True, returns a dict with 'content' and 'token_count' keys
    """
    logger.info(f"Extracting notebook: {notebook_path}")
    
    # Determine output format
    if not output_format and output_path:
        output_format = detect_output_format(output_path)
    elif not output_format:
        from .constants import FORMAT_MARKDOWN
        output_format = FORMAT_MARKDOWN
    
    # Read the notebook
    try:
        with open(notebook_path, 'r', encoding='utf-8') as f:
            nb = nbformat.read(f, as_version=4)
    except Exception as e:
        logger.error(f"Failed to read notebook: {str(e)}")
        raise
    
    # Execute the notebook if requested
    if execute:
        try:
            logger.info("Executing notebook...")
            client = nbclient.NotebookClient(nb, timeout=600)
            nb = client.execute()
            logger.info("Notebook execution complete")
        except Exception as e:
            logger.error(f"Failed to execute notebook: {str(e)}")
            logger.warning("Continuing with extraction of the original notebook")
    
    # Extract metadata
    notebook_metadata = {}
    if include_metadata:
        try:
            notebook_metadata = extract_metadata(nb)
            logger.debug(f"Extracted metadata: {list(notebook_metadata.keys())}")
        except Exception as e:
            logger.error(f"Failed to extract metadata: {str(e)}")
    
    # Process the notebook
    markdown_content = []
    
    # Add notebook title
    title = get_notebook_title(notebook_path, nb)
    markdown_content.append(f"# {title}\n\n")
    
    # Process each cell
    logger.info(f"Processing {len(nb.cells)} cells...")
    for i, cell in enumerate(nb.cells):
        try:
            formatted_cell = format_cell(
                cell, 
                include_code=include_code,
                include_outputs=include_outputs,
                max_output_length=max_output_length
            )
            if formatted_cell:
                markdown_content.append(formatted_cell)
        except Exception as e:
            logger.error(f"Error processing cell {i}: {str(e)}")
            markdown_content.append(f"*Error processing cell {i}*\n\n")
    
    # Join all content
    result = "".join(markdown_content)
    
    # Implement chunking if needed
    if chunk_size:
        logger.info(f"Chunking content with target size of {chunk_size} tokens...")
        chunked_result = smart_chunk_notebook(
            result, 
            notebook_metadata, 
            chunk_size, 
            model=model,
            include_metadata_in_each_chunk=include_metadata_in_chunks
        )
        
        # Save to file if requested
        if output_path:
            try:
                for i, chunk in enumerate(chunked_result):
                    chunk_path = f"{os.path.splitext(output_path)[0]}_chunk{i+1}{os.path.splitext(output_path)[1]}"
                    formatted_chunk = format_for_output_type(chunk, notebook_metadata, output_format)
                    with open(chunk_path, 'w', encoding='utf-8') as f:
                        f.write(formatted_chunk)
                logger.info(f"Saved {len(chunked_result)} chunks to {output_path} (with chunk suffixes)")
            except Exception as e:
                logger.error(f"Failed to save chunks: {str(e)}")
        
        if estimate_token_count:
            token_counts = [estimate_tokens(chunk, model) for chunk in chunked_result]
            return {
                'content': chunked_result,
                'token_count': token_counts,
                'total_tokens': sum(token_counts),
                'metadata': notebook_metadata
            }
        
        return chunked_result
    
    # Format for output type
    formatted_result = format_for_output_type(result, notebook_metadata, output_format)
    
    # Save to file if requested
    if output_path:
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(formatted_result)
            logger.info(f"Saved output to {output_path}")
        except Exception as e:
            logger.error(f"Failed to save output: {str(e)}")
    
    if estimate_token_count:
        token_count = estimate_tokens(formatted_result, model)
        return {
            'content': formatted_result,
            'token_count': token_count,
            'metadata': notebook_metadata
        }
    
    return formatted_result
