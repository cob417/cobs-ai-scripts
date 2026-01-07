"""
Markdown formatting utilities for Run AI Script
"""

import markdown
import re
from html import escape


def ensure_strict_markdown(content: str) -> str:
    """
    Ensure content follows strict markdown formatting rules.
    Cleans up common markdown issues and ensures proper formatting.
    """
    # Remove any trailing whitespace from lines
    lines = content.split('\n')
    cleaned_lines = [line.rstrip() for line in lines]
    content = '\n'.join(cleaned_lines)
    
    # Ensure proper spacing around headers (at least one blank line before)
    content = re.sub(r'\n(#{1,6}\s)', r'\n\n\1', content)
    content = re.sub(r'([^\n])\n(#{1,6}\s)', r'\1\n\n\2', content)
    
    # Ensure proper spacing around lists (at least one blank line before)
    content = re.sub(r'\n([-*+]\s)', r'\n\n\1', content)
    content = re.sub(r'([^\n])\n([-*+]\s)', r'\1\n\n\2', content)
    
    # Ensure proper spacing around code blocks
    content = re.sub(r'([^\n])\n(```)', r'\1\n\n\2', content)
    content = re.sub(r'(```)\n([^\n])', r'\1\n\n\2', content)
    
    # Remove multiple consecutive blank lines (max 2)
    content = re.sub(r'\n{3,}', r'\n\n', content)
    
    # Ensure file ends with a single newline
    content = content.rstrip() + '\n'
    
    return content


def _add_inline_styles(html: str) -> str:
    """
    Add inline styles to HTML elements for email client compatibility.
    Email clients often strip <style> tags, so we need inline styles.
    """
    # Add inline styles to headings
    html = re.sub(r'<h1>', r'<h1 style="font-size: 2em; font-weight: 600; margin-top: 24px; margin-bottom: 16px; color: #333;">', html)
    html = re.sub(r'<h2>', r'<h2 style="font-size: 1.5em; font-weight: 600; margin-top: 24px; margin-bottom: 16px; color: #333;">', html)
    html = re.sub(r'<h3>', r'<h3 style="font-size: 1.25em; font-weight: 600; margin-top: 24px; margin-bottom: 16px; color: #333;">', html)
    html = re.sub(r'<h4>', r'<h4 style="font-size: 1.1em; font-weight: 600; margin-top: 20px; margin-bottom: 12px; color: #333;">', html)
    html = re.sub(r'<h5>', r'<h5 style="font-size: 1em; font-weight: 600; margin-top: 16px; margin-bottom: 12px; color: #333;">', html)
    html = re.sub(r'<h6>', r'<h6 style="font-size: 0.9em; font-weight: 600; margin-top: 16px; margin-bottom: 12px; color: #333;">', html)
    
    # Add inline styles to paragraphs
    html = re.sub(r'<p>', r'<p style="margin-bottom: 16px; line-height: 1.6; color: #333;">', html)
    
    # Add inline styles to lists
    html = re.sub(r'<ul>', r'<ul style="margin-bottom: 16px; padding-left: 30px; line-height: 1.6;">', html)
    html = re.sub(r'<ol>', r'<ol style="margin-bottom: 16px; padding-left: 30px; line-height: 1.6;">', html)
    html = re.sub(r'<li>', r'<li style="margin-bottom: 8px; color: #333;">', html)
    
    # Add inline styles to links
    html = re.sub(r'<a href="([^"]+)">', r'<a href="\1" style="color: #0066cc; text-decoration: underline;">', html)
    
    # Add inline styles to code
    html = re.sub(r'<code>', r'<code style="background-color: #f4f4f4; padding: 2px 6px; border-radius: 3px; font-family: \'Courier New\', monospace; font-size: 0.9em;">', html)
    html = re.sub(r'<pre>', r'<pre style="background-color: #f4f4f4; padding: 16px; border-radius: 5px; overflow-x: auto; margin-bottom: 16px; line-height: 1.4;">', html)
    
    # Add inline styles to blockquotes
    html = re.sub(r'<blockquote>', r'<blockquote style="border-left: 4px solid #ddd; margin: 16px 0; padding-left: 16px; color: #666; font-style: italic;">', html)
    
    # Add inline styles to tables
    html = re.sub(r'<table>', r'<table style="border-collapse: collapse; width: 100%; margin-bottom: 16px;">', html)
    html = re.sub(r'<th>', r'<th style="border: 1px solid #ddd; padding: 8px 12px; text-align: left; background-color: #f4f4f4; font-weight: 600;">', html)
    html = re.sub(r'<td>', r'<td style="border: 1px solid #ddd; padding: 8px 12px; text-align: left;">', html)
    
    return html


def markdown_to_html(content: str) -> str:
    """
    Convert markdown content to HTML for email clients with inline styles.
    Uses standard markdown extensions for better formatting.
    Email clients strip <style> tags, so we use inline styles.
    """
    # Convert markdown to HTML
    html = markdown.markdown(
        content,
        extensions=['extra', 'nl2br', 'sane_lists'],
        output_format='html5'
    )
    
    # Add inline styles for email client compatibility
    html = _add_inline_styles(html)
    
    # Wrap in a simple HTML template for email clients with inline body styles
    html_email = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; background-color: #ffffff;">
{html}
</body>
</html>"""
    
    return html_email
