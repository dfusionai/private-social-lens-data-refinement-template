import json
import logging
import os

from refiner.models.offchain_schema import OffChainSchema
from refiner.models.output import Output
from refiner.transformer.miner_transformer import MinerTransformer
from refiner.transformer.webapp_transformer import WebappTransformer
from refiner.config import settings
from refiner.utils.encrypt import encrypt_file
from refiner.utils.storage import upload_file_to_storage, upload_json_to_storage

class Refiner:
    def __init__(self):
        self.db_path = os.path.join(settings.OUTPUT_DIR, 'db.libsql')

    def transform(self) -> Output:
        """Transform all input files into the database."""
        logging.info("Starting data transformation")
        output = Output()

        # Iterate through files and transform data
        for input_filename in os.listdir(settings.INPUT_DIR):
            input_file = os.path.join(settings.INPUT_DIR, input_filename)
            if os.path.splitext(input_file)[1].lower() == '.json':
                with open(input_file, 'r') as f:
                    input_data = json.load(f)
                    
                    # Determine which transformer to use based on source field
                    transformer = None
                    if 'source' in input_data:
                        if input_data['source'] == 'telegram':
                            logging.info(f"Using WebappTransformer for {input_filename}")
                            transformer = WebappTransformer(self.db_path)
                        elif input_data['source'] == 'telegramMiner':
                            logging.info(f"Using MinerTransformer for {input_filename}")
                            transformer = MinerTransformer(self.db_path)
                        else:
                            logging.warning(f"Unknown source '{input_data['source']}' in {input_filename}, defaulting to MinerTransformer")
                            transformer = MinerTransformer(self.db_path)
                    else:
                        logging.warning(f"No source field found in {input_filename}, defaulting to MinerTransformer")
                        transformer = MinerTransformer(self.db_path)
                    
                    # Process the data
                    transformer.process(input_data)
                    logging.info(f"Transformed {input_filename}")
                    
                    # Create a schema based on the SQLAlchemy schema
                    schema = OffChainSchema(
                        name=settings.SCHEMA_NAME,
                        version=settings.SCHEMA_VERSION,
                        description=settings.SCHEMA_DESCRIPTION,
                        dialect=settings.SCHEMA_DIALECT,
                        schema=transformer.get_schema()
                    )
                    output.schema = schema
                        
                    # Upload the schema to storage
                    schema_file = os.path.join(settings.OUTPUT_DIR, 'schema.json')
                    with open(schema_file, 'w') as f:
                        json.dump(schema.model_dump(), f, indent=4)
                    schema_result = upload_json_to_storage(schema.model_dump())
                    logging.info(f"Schema uploaded to storage - hash: {schema_result['hash'][:16]}...")
                    
                    # Encrypt and upload the database to storage
                    encrypted_path = encrypt_file(settings.REFINEMENT_ENCRYPTION_KEY, self.db_path)
                    upload_result = upload_file_to_storage(encrypted_path)
                    output.refinement_url = upload_result['url']
                    logging.info(f"Encrypted database uploaded - URL: {output.refinement_url}")
                    continue

        logging.info("Data transformation completed successfully")
        return output
