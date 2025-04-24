# Vana Data Refinement Template

This repository serves as a template for creating Dockerized data refinement tasks that transform raw user data into normalized (and potentially anonymized) SQLite-compatible databases. Once created, it's designed to be stored in Vana's Data Registry, and indexed for querying by Vana's Query Engine.

## Overview

This template provides a structure for building data refinement tasks that:

1. Read raw data files from the `/input` directory
2. Transform the data into a normalized SQLite database schema (specifically libSQL, a modern fork of SQLite)
3. Optionally mask or remove PII (Personally Identifiable Information)
4. Encrypt the refined data with a derivative of the original file encryption key
5. Upload the encrypted data to IPFS
6. Output the schema and IPFS URL to the `/output` directory

## Database Schema

The data refinement process transforms Telegram chat data into the following normalized database schema:

### Users Table
- **UserID**: guid (PK)
- **Source**: string (Telegram/WhatsApp)
- **SourceUserId**: string
- **Status**: string (active/deleted)
- **DateTimeCreated**: timestamp/int

### Submissions Table
- **SubmissionID**: guid (PK)
- **UserID**: guid (FK)
- **SubmissionDate**: timestamp/int
- **SubmissionReference**: string (FileID)

### SubmissionChats Table
- **SubmissionChatID**: guid (PK)
- **SubmissionID**: guid (FK)
- **SourceChatID**: string
- **FirstMessageDate**: timestamp/int
- **LastMessageDate**: timestamp/int
- **ParticipantCount**: int
- **MessageCount**: int

### ChatMessages Table
- **MessageID**: guid (PK)
- **SubmissionChatID**: guid (FK)
- **SourceMessageID**: string
- **SenderID**: string (AuthorId)
- **MessageDate**: timestamp/int
- **ContentType**: string (text/image/video/audio)
- **Content**: string (text)
- **ContentData**: ByteArray (media)

## Project Structure

- `refiner/`: Contains the main refinement logic
    - `refine.py`: Core refinement implementation
    - `config.py`: Environment variables and settings needed to run your refinement
    - `__main__.py`: Entry point for the refinement execution
    - `models/`: Pydantic and SQLAlchemy data models (for both unrefined and refined data)
    - `transformer/`: Data transformation logic
    - `utils/`: Utility functions for encryption, IPFS upload, etc.
- `input/`: Contains raw data files to be refined
- `output/`: Contains refined outputs:
    - `schema.json`: Database schema definition
    - `db.libsql`: SQLite database file
    - `db.libsql.pgp`: Encrypted database file
- `Dockerfile`: Defines the container image for the refinement task
- `requirements.txt`: Python package dependencies

## Getting Started

1. Fork this repository
1. Modify the config to match your environment, or add a .env file at the root
1. Update the schemas in `refiner/models/` to define your raw and normalized data models
1. Modify the refinement logic in `refiner/transformer/` to match your data structure
1. Build and test your refinement container

## Local Development

To run the refinement locally for testing:

```bash
# With Python
pip install --no-cache-dir -r requirements.txt
python -m refiner

# Or with Docker
docker build -t refiner .
docker run \
  --rm \
  --volume $(pwd)/input:/input \
  --volume $(pwd)/output:/output \
  --env PINATA_API_KEY=your_key \
  --env PINATA_API_SECRET=your_secret \
  refiner
```

## Contributing

If you have suggestions for improving this template, please open an issue or submit a pull request.

## License

[MIT License](LICENSE)

