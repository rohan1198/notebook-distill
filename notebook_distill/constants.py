# Output formats
FORMAT_MARKDOWN = "markdown"
FORMAT_TEXT = "text"
FORMAT_JSON = "json"

# Cell types
CELL_TYPE_CODE = "code"
CELL_TYPE_MARKDOWN = "markdown"
CELL_TYPE_RAW = "raw"

# Output formats for code cells
OUTPUT_TEXT_PLAIN = "text/plain"
OUTPUT_TEXT_HTML = "text/html"
OUTPUT_TEXT_LATEX = "text/latex"
OUTPUT_TEXT_MARKDOWN = "text/markdown"
OUTPUT_IMAGE_PNG = "image/png"
OUTPUT_IMAGE_JPEG = "image/jpeg"
OUTPUT_IMAGE_SVG = "image/svg+xml"
OUTPUT_APPLICATION_JSON = "application/json"

# Max sizes
DEFAULT_MAX_OUTPUT_LENGTH = 2000  # Default maximum output length in characters
MAX_CHUNK_SIZE = 100000  # Maximum chunk size in characters

# Special markers
LATEX_INLINE_MARKER = "$"
LATEX_BLOCK_START_MARKER = "$$"
LATEX_BLOCK_END_MARKER = "$$"
CODE_BLOCK_START_MARKER = "```"
CODE_BLOCK_END_MARKER = "```"

# HTML tags to keep when converting
HTML_MARKDOWN_CONVERTIBLE_TAGS = [
    "p", "h1", "h2", "h3", "h4", "h5", "h6", 
    "strong", "em", "b", "i", "a", "ul", "ol", "li",
    "table", "tr", "td", "th", "thead", "tbody"
]

# Important metadata keys
IMPORTANT_METADATA_KEYS = [
    "title", "authors", "kernelspec", "language_info", 
    "creation_date", "last_modified", "tags"
]

# Import note templates
HTML_CONTENT_NOTE = "Note: This cell contained complex HTML content that was simplified for LLM compatibility."
IMAGE_CONTENT_NOTE = "Note: This cell contained an image that couldn't be included in text format."
WIDGET_CONTENT_NOTE = "Note: This cell contained an interactive widget that couldn't be included in text format."

