from typing import List
import re
import nltk
from .utils import estimate_tokens
from .logger import Logger

logger = Logger("chunker")

# Download necessary NLTK data if not already present
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

def chunk_content(content: str, chunk_size: int, model: str = "gpt-4") -> List[str]:
    """
    Split content into chunks of approximately chunk_size tokens.
    Uses NLTK for better natural language chunking.
    
    Args:
        content: The markdown content to split
        chunk_size: Target token size for each chunk
        model: Model to use for token estimation
        
    Returns:
        List of content chunks
    """
    # If content is already smaller than chunk_size, return as is
    content_tokens = estimate_tokens(content, model)
    logger.debug(f"Content size: {content_tokens} tokens")
    
    if content_tokens <= chunk_size:
        return [content]
    
    # Split by markdown headers to preserve structure
    logger.debug(f"Content exceeds chunk size, splitting into chunks of ~{chunk_size} tokens")
    header_pattern = r'(^|\n)(#+\s+.+)(\n|$)'
    sections = re.split(header_pattern, content, flags=re.MULTILINE)
    
    chunks = []
    current_chunk = []
    current_size = 0
    
    i = 0
    while i < len(sections):
        # Handle the case where header pattern creates empty strings
        if not sections[i].strip():
            i += 1
            continue
        
        # If we matched a header, we have a group of 3 elements: text before, header, text after
        # We need to combine them into a logical section
        if i + 2 < len(sections) and re.match(r'^#+\s+.+', sections[i+1].strip()):
            section = sections[i] + sections[i+1] + sections[i+2]
            i += 3
        else:
            section = sections[i]
            i += 1
        
        section_size = estimate_tokens(section, model)
        
        # If adding this section would exceed chunk size and we already have content,
        # start a new chunk
        if current_size + section_size > chunk_size and current_chunk:
            chunks.append("".join(current_chunk))
            current_chunk = []
            current_size = 0
        
        # If a single section is larger than chunk_size, we need to split it further
        if section_size > chunk_size:
            logger.debug(f"Section too large ({section_size} tokens), splitting further")
            
            # Special handling for code blocks - don't split inside them
            code_blocks = []
            code_block_pattern = r'```[\s\S]*?```'
            
            # Extract code blocks and replace with placeholders
            section_with_placeholders = re.sub(
                code_block_pattern,
                lambda m: f"__CODE_BLOCK_{len(code_blocks)}__" and code_blocks.append(m.group(0)) or f"__CODE_BLOCK_{len(code_blocks)-1}__",
                section
            )
            
            # Split by paragraphs
            paragraphs = re.split(r'\n\n+', section_with_placeholders)
            
            for para in paragraphs:
                # Restore code blocks
                for i, block in enumerate(code_blocks):
                    para = para.replace(f"__CODE_BLOCK_{i}__", block)
                
                para_size = estimate_tokens(para, model)
                
                if current_size + para_size > chunk_size and current_chunk:
                    chunks.append("".join(current_chunk))
                    current_chunk = []
                    current_size = 0
                
                # If even a single paragraph is too big, we need to split it by sentences using NLTK
                if para_size > chunk_size:
                    logger.debug(f"Paragraph too large ({para_size} tokens), splitting by sentences")
                    
                    # Check for code blocks, don't split them
                    has_code = '```' in para
                    if has_code:
                        # If there's a code block, add it as is to a chunk
                        if current_chunk:
                            chunks.append("".join(current_chunk))
                        chunks.append(para)
                        current_chunk = []
                        current_size = 0
                    else:
                        sentences = nltk.sent_tokenize(para)
                        for sent in sentences:
                            sent_size = estimate_tokens(sent, model)
                            if current_size + sent_size > chunk_size and current_chunk:
                                chunks.append("".join(current_chunk))
                                current_chunk = []
                                current_size = 0
                            
                            current_chunk.append(sent + " ")
                            current_size += sent_size
                else:
                    current_chunk.append(para + "\n\n")
                    current_size += para_size
        else:
            current_chunk.append(section)
            current_size += section_size
    
    # Add the final chunk if it has content
    if current_chunk:
        chunks.append("".join(current_chunk))
    
    logger.info(f"Split content into {len(chunks)} chunks")
    for i, chunk in enumerate(chunks):
        chunk_tokens = estimate_tokens(chunk, model)
        logger.debug(f"Chunk {i+1}: {chunk_tokens} tokens")
    
    return chunks

def smart_chunk_notebook(
    notebook_content: str, 
    metadata: dict,
    chunk_size: int, 
    model: str = "gpt-4",
    include_metadata_in_each_chunk: bool = True
) -> List[str]:
    """
    Intelligently chunk notebook content, preserving metadata where appropriate.
    
    Args:
        notebook_content: Formatted notebook content
        metadata: Notebook metadata
        chunk_size: Target token size for each chunk
        model: Model to use for token estimation
        include_metadata_in_each_chunk: Whether to include metadata in each chunk
        
    Returns:
        List of content chunks
    """
    from .metadata import format_metadata_as_markdown
    
    # Format metadata
    metadata_md = format_metadata_as_markdown(metadata)
    metadata_size = estimate_tokens(metadata_md, model)
    
    # Adjust chunk size to account for metadata if we're including it in each chunk
    effective_chunk_size = chunk_size
    if include_metadata_in_each_chunk:
        effective_chunk_size = max(chunk_size - metadata_size - 50, chunk_size // 2)  # Leave some room for separation
    
    # Chunk the content
    content_chunks = chunk_content(notebook_content, effective_chunk_size, model)
    
    # Add metadata to each chunk if requested
    if include_metadata_in_each_chunk and metadata_md:
        return [f"{metadata_md}\n\n---\n\n{chunk}" for chunk in content_chunks]
    
    # Otherwise, add metadata only to the first chunk
    if content_chunks and metadata_md:
        content_chunks[0] = f"{metadata_md}\n\n---\n\n{content_chunks[0]}"
    
    return content_chunks
