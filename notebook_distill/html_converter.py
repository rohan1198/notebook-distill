import re
from html.parser import HTMLParser
from html import unescape
from typing import Dict, List, Optional, Tuple, Set

from .constants import HTML_MARKDOWN_CONVERTIBLE_TAGS, HTML_CONTENT_NOTE
from .logger import Logger

logger = Logger("html_converter")

class HTMLToMarkdownConverter(HTMLParser):
    """Converts HTML to Markdown with special handling for Jupyter notebook content."""
    
    def __init__(self):
        super().__init__()
        self.result = []
        self.in_paragraph = False
        self.in_heading = False
        self.heading_level = 0
        self.in_list = False
        self.list_type = None
        self.list_items = []
        self.in_table = False
        self.in_table_row = False
        self.in_table_header = False
        self.current_table = []
        self.current_row = []
        self.link_href = ""
        self.in_link = False
        self.complex_html_detected = False
        self.inside_tags = []
        self.buffer = []
        
    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]):
        """Process opening HTML tags."""
        self.inside_tags.append(tag)
        attrs_dict = dict(attrs)
        
        # Track if we encounter complex HTML
        if tag not in HTML_MARKDOWN_CONVERTIBLE_TAGS:
            self.complex_html_detected = True
            
        if tag == "p":
            self.in_paragraph = True
            self.result.append("\n\n")
        elif tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            self.in_heading = True
            self.heading_level = int(tag[1])
            self.result.append("\n" + "#" * self.heading_level + " ")
        elif tag in ["strong", "b"]:
            self.result.append("**")
        elif tag in ["em", "i"]:
            self.result.append("*")
        elif tag == "a":
            self.in_link = True
            self.link_href = attrs_dict.get("href", "")
            self.result.append("[")
        elif tag == "code":
            self.result.append("`")
        elif tag == "pre":
            self.result.append("\n```\n")
        elif tag == "br":
            self.result.append("\n")
        elif tag in ["ul", "ol"]:
            self.in_list = True
            self.list_type = tag
            self.list_items = []
        elif tag == "li":
            self.buffer = []
        elif tag == "table":
            self.in_table = True
            self.current_table = []
        elif tag == "tr":
            self.in_table_row = True
            self.current_row = []
        elif tag in ["th", "thead"]:
            self.in_table_header = True
        
    def handle_endtag(self, tag: str):
        """Process closing HTML tags."""
        if self.inside_tags and self.inside_tags[-1] == tag:
            self.inside_tags.pop()
        
        if tag == "p":
            self.in_paragraph = False
            self.result.append("\n")
        elif tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            self.in_heading = False
            self.result.append("\n")
        elif tag in ["strong", "b"]:
            self.result.append("**")
        elif tag in ["em", "i"]:
            self.result.append("*")
        elif tag == "a":
            self.in_link = False
            self.result.append(f"]({self.link_href})")
        elif tag == "code":
            self.result.append("`")
        elif tag == "pre":
            self.result.append("\n```\n")
        elif tag in ["ul", "ol"]:
            prefix = "1. " if tag == "ol" else "- "
            for item in self.list_items:
                self.result.append(f"\n{prefix}{item}")
            self.in_list = False
            self.list_type = None
            self.list_items = []
            self.result.append("\n")
        elif tag == "li":
            self.list_items.append("".join(self.buffer))
        elif tag == "table":
            if self.current_table:
                # Convert table to markdown
                table_md = []
                
                # Add headers
                if self.current_table and any(self.current_table):
                    headers = self.current_table[0]
                    table_md.append("| " + " | ".join(headers) + " |")
                    table_md.append("| " + " | ".join(["---"] * len(headers)) + " |")
                
                    # Add rows
                    for row in self.current_table[1:]:
                        # Pad shorter rows
                        padded_row = row + [""] * (len(headers) - len(row))
                        table_md.append("| " + " | ".join(padded_row) + " |")
                
                self.result.append("\n" + "\n".join(table_md) + "\n")
            
            self.in_table = False
            self.current_table = []
        elif tag == "tr":
            if self.current_row:
                self.current_table.append(self.current_row)
            self.in_table_row = False
            self.current_row = []
        elif tag in ["th", "thead"]:
            self.in_table_header = False
            
    def handle_data(self, data: str):
        """Process text content."""
        if self.in_list and self.inside_tags and self.inside_tags[-1] == "li":
            self.buffer.append(data)
        elif self.in_table_row and data.strip():
            self.current_row.append(data.strip())
        else:
            self.result.append(data)
            
    def convert(self, html: str) -> Tuple[str, bool]:
        """
        Convert HTML to Markdown.
        
        Args:
            html: HTML string to convert
            
        Returns:
            Tuple containing converted markdown and flag indicating if complex HTML was detected
        """
        self.result = []
        self.complex_html_detected = False
        self.feed(html)
        markdown = "".join(self.result)
        
        # Clean up extra whitespace
        markdown = re.sub(r'\n\s*\n\s*\n', '\n\n', markdown)
        
        # If complex HTML was detected, add a note
        if self.complex_html_detected:
            markdown += f"\n\n*{HTML_CONTENT_NOTE}*\n"
            
        return markdown, self.complex_html_detected

def convert_html_to_markdown(html: str) -> Tuple[str, bool]:
    """
    Convert HTML to Markdown.
    
    Args:
        html: HTML string to convert
        
    Returns:
        Tuple containing converted markdown and flag indicating if complex HTML was detected
    """
    try:
        converter = HTMLToMarkdownConverter()
        return converter.convert(html)
    except Exception as e:
        logger.error(f"Error converting HTML to Markdown: {str(e)}")
        return f"\n\n*HTML content (conversion error: {str(e)})*\n", True
