import argparse
import sys
import os
from typing import List, Optional
import json

from .extractor import extract_notebook
from .logger import Logger
from .constants import FORMAT_MARKDOWN, FORMAT_JSON, FORMAT_TEXT

logger = Logger("cli")

def parse_args(args: Optional[List[str]] = None):
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Distill Jupyter notebooks into clean formats optimized for LLMs."
    )
    
    parser.add_argument(
        "notebook_path",
        help="Path to the Jupyter notebook (.ipynb) file"
    )
    
    parser.add_argument(
        "-o", "--output",
        help="Output file path (defaults to stdout)"
    )
    
    parser.add_argument(
        "--format",
        choices=[FORMAT_MARKDOWN, FORMAT_JSON, FORMAT_TEXT],
        help=f"Output format (defaults to markdown or based on output file extension)"
    )
    
    parser.add_argument(
        "--no-code",
        action="store_true",
        help="Exclude code cells from the output"
    )
    
    parser.add_argument(
        "--no-outputs",
        action="store_true",
        help="Exclude cell outputs from the output"
    )
    
    parser.add_argument(
        "--no-metadata",
        action="store_true",
        help="Exclude notebook metadata from the output"
    )
    
    parser.add_argument(
        "--max-output-length",
        type=int,
        help="Maximum length for any single output"
    )
    
    parser.add_argument(
        "--chunk-size",
        type=int,
        help="Split output into chunks of this approximate token size"
    )
    
    parser.add_argument(
        "--no-metadata-in-chunks",
        action="store_true",
        help="Do not include metadata in each chunk (only in the first chunk)"
    )
    
    parser.add_argument(
        "--estimate-tokens",
        action="store_true",
        help="Estimate and display token count"
    )
    
    parser.add_argument(
        "--model",
        default="gpt-4",
        help="Model to use for token estimation (default: gpt-4)"
    )
    
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute the notebook before extraction"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args(args)

def main(args: Optional[List[str]] = None):
    """Main entry point for the CLI."""
    parsed_args = parse_args(args)
    
    # Set up logging
    if parsed_args.verbose:
        import logging
        import os
        os.environ["LOG_LEVEL"] = str(logging.DEBUG)
        logger.log_level = logging.DEBUG
        logger.debug("Verbose logging enabled")
    
    try:
        logger.info(f"Processing notebook: {parsed_args.notebook_path}")
        
        result = extract_notebook(
            notebook_path=parsed_args.notebook_path,
            include_code=not parsed_args.no_code,
            include_outputs=not parsed_args.no_outputs,
            max_output_length=parsed_args.max_output_length,
            chunk_size=parsed_args.chunk_size,
            estimate_token_count=parsed_args.estimate_tokens,
            model=parsed_args.model,
            execute=parsed_args.execute,
            include_metadata=not parsed_args.no_metadata,
            output_format=parsed_args.format,
            output_path=parsed_args.output,
            include_metadata_in_chunks=not parsed_args.no_metadata_in_chunks
        )
        
        if parsed_args.estimate_tokens:
            if isinstance(result, dict):
                if 'token_count' in result and isinstance(result['token_count'], list):
                    total_tokens = result['total_tokens']
                    print(f"Estimated total tokens: {total_tokens}", file=sys.stderr)
                    print(f"Chunks: {len(result['content'])}", file=sys.stderr)
                    
                    for i, count in enumerate(result['token_count']):
                        print(f"Chunk {i+1}: ~{count} tokens", file=sys.stderr)
                    
                    # Only print to stdout if not saving to file
                    if not parsed_args.output:
                        for i, chunk in enumerate(result['content']):
                            print(f"\n--- CHUNK {i+1} ---\n", file=sys.stdout)
                            print(chunk, file=sys.stdout)
                else:
                    print(f"Estimated tokens: {result['token_count']}", file=sys.stderr)
                    
                    # Only print to stdout if not saving to file
                    if not parsed_args.output:
                        print(result['content'], file=sys.stdout)
        else:
            # Only print to stdout if not saving to file
            if not parsed_args.output:
                if isinstance(result, list):
                    for i, chunk in enumerate(result):
                        print(f"\n--- CHUNK {i+1} ---\n", file=sys.stdout)
                        print(chunk, file=sys.stdout)
                else:
                    print(result, file=sys.stdout)
                    
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
