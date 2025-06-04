import json
import logging
import os
import requests
from refiner.config import settings

PINATA_FILE_API_ENDPOINT = "https://api.pinata.cloud/pinning/pinFileToIPFS"
PINATA_JSON_API_ENDPOINT = "https://api.pinata.cloud/pinning/pinJSONToIPFS"

def upload_json_to_ipfs(data):
    """
    Uploads JSON data to IPFS using Pinata API.
    Reference: https://pinata-cloud.readme.io/reference/post_pinning-pinjsontoipfs
    :param data: JSON data to upload (dictionary or list)
    :return: IPFS hash
    """
    if not settings.PINATA_API_JWT:
        raise Exception("Error: Pinata IPFS API credentials not found, please check your environment variables")

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {settings.PINATA_API_JWT}"
    }

    try:
        response = requests.post(
            PINATA_JSON_API_ENDPOINT,
            data=json.dumps(data),
            headers=headers
        )
        response.raise_for_status()

        result = response.json()
        logging.info(f"Successfully uploaded JSON to IPFS with hash: {result['IpfsHash']}")
        return result['IpfsHash']

    except requests.exceptions.RequestException as e:
        logging.error(f"An error occurred while uploading JSON to IPFS: {e}")
        raise e

def upload_file_to_ipfs(file_path=None):
    """
    Uploads a file to IPFS using Pinata API (https://pinata.cloud/).
    Reference: https://pinata-cloud.readme.io/reference/post_pinning-pinfiletoipfs
    :param file_path: Path to the file to upload (defaults to encrypted database)
    :return: IPFS hash
    """
    if file_path is None:
        # Default to the encrypted database file
        file_path = os.path.join(settings.OUTPUT_DIR, "db.libsql.pgp")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    if not settings.PINATA_API_JWT:
        raise Exception("Error: Pinata IPFS API credentials not found, please check your environment variables")

    headers = {
        "authorization": f"Bearer {settings.PINATA_API_JWT}"
    }

    try:
        with open(file_path, 'rb') as file:
            files = {
                'file': file
            }
            response = requests.post(
                PINATA_FILE_API_ENDPOINT,
                files=files,
                headers=headers
            )

        response.raise_for_status()
        result = response.json()
        logging.info(f"Successfully uploaded file to IPFS with hash: {result['IpfsHash']}")
        return result['IpfsHash']

    except requests.exceptions.RequestException as e:
        logging.error(f"An error occurred while uploading file to IPFS: {e}")
        raise e

# Test with: python -m refiner.utils.ipfs
if __name__ == "__main__":
    ipfs_hash = upload_file_to_ipfs()
    print(f"File uploaded to IPFS with hash: {ipfs_hash}")
    print(f"Access at: https://ipfs.vana.org/ipfs/{ipfs_hash}")

    ipfs_hash = upload_json_to_ipfs()
    print(f"JSON uploaded to IPFS with hash: {ipfs_hash}")
    print(f"Access at: https://ipfs.vana.org/ipfs/{ipfs_hash}")