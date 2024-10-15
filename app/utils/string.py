"""Utility functions for string operations.

This module provides utility functions for various string operations,
including URL decoding.
"""

from urllib.parse import unquote

def decode_url_string(encoded_string: str) -> str:
    """
    Decodes a URL-encoded string.
    
    Args:
        encoded_string (str): The URL-encoded string to decode.
    
    Returns:
        str: The decoded string.
    
    Example:
        >>> decode_url_string("hello%40world.com")
        'hello@world.com'
    """
    return unquote(encoded_string)
