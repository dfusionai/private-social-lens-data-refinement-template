"""
Offchain storage utilities for uploading refined data.

Uploads go through the relay service which handles authentication
and forwards to the offchain storage service.
"""
import json
import logging
import os
import requests
from refiner.config import settings


def upload_file_to_storage(file_path=None):
    """
    Uploads a file to offchain storage via the relay service.

    :param file_path: Path to the file to upload (defaults to encrypted database)
    :return: Dict with hash and url from storage service
    """
    if file_path is None:
        # Default to the encrypted database file
        file_path = os.path.join(settings.OUTPUT_DIR, "db.libsql.pgp")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    if not settings.RELAY_UPLOAD_URL:
        raise Exception(
            "Error: RELAY_UPLOAD_URL not configured. "
            "This should be provided by the relay service via env_vars."
        )

    try:
        with open(file_path, 'rb') as file:
            files = {
                'file': (os.path.basename(file_path), file, 'application/octet-stream')
            }
            response = requests.post(
                settings.RELAY_UPLOAD_URL,
                files=files
            )

        response.raise_for_status()
        result = response.json()

        # Response format: { url, ipfsHash (which is now SHA-256 hash), size }
        content_hash = result.get('ipfsHash') or result.get('hash')
        url = result.get('url')

        logging.info(f"Successfully uploaded file to storage - hash: {content_hash[:16]}...")

        return {
            'hash': content_hash,
            'url': url,
            'size': result.get('size', os.path.getsize(file_path))
        }

    except requests.exceptions.RequestException as e:
        logging.error(f"An error occurred while uploading file to storage: {e}")
        raise e


def upload_json_to_storage(data):
    """
    Uploads JSON data to offchain storage via the relay service.

    :param data: JSON data to upload (dictionary or list)
    :return: Dict with hash and url from storage service
    """
    if not settings.RELAY_UPLOAD_URL:
        raise Exception(
            "Error: RELAY_UPLOAD_URL not configured. "
            "This should be provided by the relay service via env_vars."
        )

    try:
        # Convert JSON to bytes
        json_bytes = json.dumps(data).encode('utf-8')

        files = {
            'file': ('data.json', json_bytes, 'application/json')
        }
        response = requests.post(
            settings.RELAY_UPLOAD_URL,
            files=files
        )

        response.raise_for_status()
        result = response.json()

        content_hash = result.get('ipfsHash') or result.get('hash')
        url = result.get('url')

        logging.info(f"Successfully uploaded JSON to storage - hash: {content_hash[:16]}...")

        return {
            'hash': content_hash,
            'url': url,
            'size': result.get('size', len(json_bytes))
        }

    except requests.exceptions.RequestException as e:
        logging.error(f"An error occurred while uploading JSON to storage: {e}")
        raise e


# Backward compatibility aliases
def upload_file_to_ipfs(file_path=None):
    """
    Backward compatible alias for upload_file_to_storage.
    Returns just the hash string for compatibility with existing code.
    """
    result = upload_file_to_storage(file_path)
    return result['hash']


def upload_json_to_ipfs(data):
    """
    Backward compatible alias for upload_json_to_storage.
    Returns just the hash string for compatibility with existing code.
    """
    result = upload_json_to_storage(data)
    return result['hash']


# Test with: python -m refiner.utils.storage
if __name__ == "__main__":
    # Test file upload
    test_file = os.path.join(settings.OUTPUT_DIR, "db.libsql.pgp")
    if os.path.exists(test_file):
        result = upload_file_to_storage(test_file)
        print(f"File uploaded - hash: {result['hash']}")
        print(f"URL: {result['url']}")

    # Test JSON upload
    test_json = {"test": "data", "timestamp": "2024-01-01"}
    result = upload_json_to_storage(test_json)
    print(f"JSON uploaded - hash: {result['hash']}")
    print(f"URL: {result['url']}")
