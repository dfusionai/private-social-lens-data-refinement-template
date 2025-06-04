import json
import logging
import os
import sys
import traceback
import zipfile
import shutil

from refiner.refine import Refiner
from refiner.config import settings

logging.basicConfig(level=logging.INFO, format='%(message)s')


def run(port=None) -> None:
    """Transform all input files into the database."""
    input_files_exist = os.path.isdir(settings.INPUT_DIR) and bool(os.listdir(settings.INPUT_DIR))

    if not input_files_exist:
        raise FileNotFoundError(f"No input files found in {settings.INPUT_DIR}")
    extract_input()

    refiner = Refiner()
    output = refiner.transform()
    
    output_path = os.path.join(settings.OUTPUT_DIR, "output.json")
    with open(output_path, 'w') as f:
        json.dump(output.model_dump(), f, indent=2)    
    logging.info(f"Data transformation complete: {output}")


def extract_input() -> None:
    """
    If the input directory contains any zip files, extract them
    If there are files with .zip extension that are actually JSON files, rename them to .json
    :return:
    """
    for input_filename in os.listdir(settings.INPUT_DIR):
        input_file = os.path.join(settings.INPUT_DIR, input_filename)

        if input_filename.endswith('.zip'):
            if zipfile.is_zipfile(input_file):
                with zipfile.ZipFile(input_file, 'r') as zip_ref:
                    zip_ref.extractall(settings.INPUT_DIR)
                    logging.info(f"Extracted {input_file} to {settings.INPUT_DIR}")
            else:
                # Check if the file with .zip extension is actually a JSON file
                try:
                    with open(input_file, 'r') as f:
                        json.load(f)  # Try to load as JSON
                    
                    # If we get here, it's a valid JSON file
                    new_filename = os.path.splitext(input_file)[0] + '.json'
                    shutil.copy2(input_file, new_filename)
                    logging.info(f"File {input_file} is actually a JSON file. Copied to {new_filename}")
                except json.JSONDecodeError:
                    logging.info(f"{input_file} is not a zip file nor a valid JSON file")
                except Exception as e:
                    logging.error(f"Error processing {input_file}: {str(e)}")

if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        logging.error(f"Error during data transformation: {e}")
        traceback.print_exc()
        sys.exit(1)
