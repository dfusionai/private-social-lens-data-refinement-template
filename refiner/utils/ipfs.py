"""
IPFS utilities - now uses relay-based offchain storage.

This module is kept for backward compatibility.
All functions now use the relay upload URL instead of direct Pinata access.
"""

# Re-export from storage module for backward compatibility
from refiner.utils.storage import (
    upload_file_to_ipfs,
    upload_json_to_ipfs,
    upload_file_to_storage,
    upload_json_to_storage,
)

__all__ = [
    'upload_file_to_ipfs',
    'upload_json_to_ipfs',
    'upload_file_to_storage',
    'upload_json_to_storage',
]
