# Vana Data Refinement Template

This repository serves as a template for creating Dockerized *data refinement instructions* that transform raw user data into normalized (and potentially anonymized) SQLite-compatible databases, so data in Vana can be querying by Vana's Query Engine.

## Overview

Here is an overview of the data refinement process on Vana.

![How Refinements Work](https://files.readme.io/25f8f6a4c8e785a72105d6eb012d09449f63ab5682d1f385120eaf5af871f9a2-image.png "How Refinements Work")

1. DLPs upload user-contributed data through their UI, and run proof-of-contribution against it. Afterwards, they call the refinement service to refine this data point.
1. The refinement service downloads the file from the Data Registry and decrypts it.
1. The refinement container, containing the instructions for data refinement (this repo), is executed
   1. The decrypted data is mounted to the container's `/input` directory
   1. The raw data points are transformed against a normalized SQLite database schema (specifically libSQL, a modern fork of SQLite)
   1. Optionally, PII (Personally Identifiable Information) is removed or masked
   1. The refined data is symmetrically encrypted with a derivative of the original file encryption key
1. The encrypted refined data is uploaded and pinned to a DLP-owned IPFS
1. The IPFS CID is written to the refinement container's `/output` directory
1. The CID of the file is added as a refinement under the original file in the Data Registry
1. Vana's Query Engine indexes that data point, aggregating it with all other data points of a given refiner. This allows SQL queries to run against all data of a particular refiner (schema).

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

## Data Mapping Documentation

This section explains how data from the input JSON structure is mapped to the database models.

### Input JSON Structure

The system supports two different input formats:

#### miner-fileDto.json (telegramMiner source)

```json
{
  "revision": "01.01",
  "source": "telegramMiner",
  "user": "5619346142",
  "submission_token": "...",
  "chats": [
    {
      "chat_id": -919006036,
      "contents": [
        {
          "flags": 768,
          "out": false,
          "mentioned": false,
          "mediaUnread": false,
          "reactionsArePossible": true,
          "silent": false,
          "post": false,
          "legacy": false,
          "id": 1602,
          "fromId": {
            "userId": "5020274799",
            "className": "PeerUser"
          },
          "peerId": {
            "chatId": "919006036",
            "className": "PeerChat"
          },
          "replyTo": null,
          "date": 1716712252,
          "message": "...",
          "className": "Message"
          // Other message properties...
        }
        // More messages...
      ]
    }
    // More chats...
  ]
}
```

#### webapp-fileDto.json (telegram source)

```json
{
  "revision": "01.01",
  "source": "telegram",
  "user": "5619346142",
  "submission_token": "...",
  "chats": [
    {
      "chat_id": -919006036,
      "contents": [
        {
          "@type": "message",
          "id": 1602,
          "sender_id": {
            "@type": "messageSenderUser",
            "user_id": 5020274799
          },
          "chat_id": 919006036,
          "date": 1716712252,
          "is_outgoing": false,
          "is_pinned": false,
          "content": {
            "@type": "messageText",
            "text": {
              "@type": "formattedText",
              "text": "...",
              "entities": []
            }
          }
          // Other message properties...
        }
        // More messages...
      ]
    }
    // More chats...
  ]
}
```

### Database Models → JSON Field Mapping

The application uses two different transformers depending on the input source:
- `MinerTransformer` for "telegramMiner" source (miner-fileDto.json)
- `WebappTransformer` for "telegram" source (webapp-fileDto.json)

#### Users Table

```python
class Users(Base):
    __tablename__ = 'users'
    
    UserID = Column(String, primary_key=True)
    Source = Column(String, nullable=False)
    SourceUserId = Column(String, nullable=False)
    Status = Column(String, nullable=False, default="active")
    DateTimeCreated = Column(DateTime, nullable=False)
```

##### MinerTransformer (miner-fileDto.json)

| Model Field | JSON Source | Logic/Condition |
|-------------|-------------|----------------|
| `UserID` | N/A | Generated using `str(uuid.uuid4())` |
| `Source` | N/A | Hard-coded value: `"Telegram"` |
| `SourceUserId` | `input_data.user` | Direct mapping from root `user` field |
| `Status` | N/A | Hard-coded value: `"active"` |
| `DateTimeCreated` | N/A | Current timestamp: `datetime.now()` |

##### WebappTransformer (webapp-fileDto.json)

| Model Field | JSON Source | Logic/Condition |
|-------------|-------------|----------------|
| `UserID` | N/A | Generated using `str(uuid.uuid4())` |
| `Source` | `webapp_data.source` | Direct mapping from root `source` field |
| `SourceUserId` | `webapp_data.user` | Converted to string: `str(webapp_data.user)` |
| `Status` | N/A | Hard-coded value: `"active"` |
| `DateTimeCreated` | N/A | Current timestamp: `datetime.now()` |

#### Submissions Table

```python
class Submissions(Base):
    __tablename__ = 'submissions'
    
    SubmissionID = Column(String, primary_key=True)
    UserID = Column(String, ForeignKey('users.UserID'), nullable=False)
    SubmissionDate = Column(DateTime, nullable=False)
    SubmissionReference = Column(String, nullable=False)
```

##### MinerTransformer (miner-fileDto.json)

| Model Field | JSON Source | Logic/Condition |
|-------------|-------------|----------------|
| `SubmissionID` | N/A | Generated using `str(uuid.uuid4())` |
| `UserID` | N/A | Foreign key reference to generated Users.UserID |
| `SubmissionDate` | N/A | Current timestamp: `datetime.now()` |
| `SubmissionReference` | `miner_data.submission_token` | Direct mapping from root `submission_token` field |

##### WebappTransformer (webapp-fileDto.json)

| Model Field | JSON Source | Logic/Condition |
|-------------|-------------|----------------|
| `SubmissionID` | N/A | Generated using `str(uuid.uuid4())` |
| `UserID` | N/A | Foreign key reference to generated Users.UserID |
| `SubmissionDate` | N/A | Current timestamp: `datetime.now()` |
| `SubmissionReference` | `webapp_data.submission_token` | Direct mapping from root `submission_token` field, or generates a timestamp-based reference if empty |

#### SubmissionChats Table

```python
class SubmissionChats(Base):
    __tablename__ = 'submission_chats'
    
    SubmissionChatID = Column(String, primary_key=True)
    SubmissionID = Column(String, ForeignKey('submissions.SubmissionID'), nullable=False)
    SourceChatID = Column(String, nullable=False)
    FirstMessageDate = Column(DateTime, nullable=False)
    LastMessageDate = Column(DateTime, nullable=False)
    ParticipantCount = Column(Integer, nullable=True)
    MessageCount = Column(Integer, nullable=False, default=0)
```

##### MinerTransformer (miner-fileDto.json)

| Model Field | JSON Source | Logic/Condition |
|-------------|-------------|----------------|
| `SubmissionChatID` | N/A | Generated using `str(uuid.uuid4())` |
| `SubmissionID` | N/A | Foreign key reference to generated Submissions.SubmissionID |
| `SourceChatID` | `chat_data.chat_id` | Converted to string: `str(chat_data.chat_id)` |
| `FirstMessageDate` | `chat_data.contents[*].date` | Converted to datetime: `min(datetime.fromtimestamp(msg.date) for msg in chat_data.contents)` |
| `LastMessageDate` | `chat_data.contents[*].date` | Converted to datetime: `max(datetime.fromtimestamp(msg.date) for msg in chat_data.contents)` |
| `ParticipantCount` | `chat_data.contents[*].fromId.userId` | Count of unique user IDs: `len(participants)` where `participants` is a set of all sender user IDs |
| `MessageCount` | `chat_data.contents` | Length of contents array: `len(chat_data.contents)` |

##### WebappTransformer (webapp-fileDto.json)

| Model Field | JSON Source | Logic/Condition |
|-------------|-------------|----------------|
| `SubmissionChatID` | N/A | Generated using `str(uuid.uuid4())` |
| `SubmissionID` | N/A | Foreign key reference to generated Submissions.SubmissionID |
| `SourceChatID` | `chat_data.chat_id` | Converted to string: `str(chat_data.chat_id)` |
| `FirstMessageDate` | `chat_data.contents[*].date` | Converted to datetime: `min(datetime.fromtimestamp(msg.date) for msg in chat_data.contents)` |
| `LastMessageDate` | `chat_data.contents[*].date` | Converted to datetime: `max(datetime.fromtimestamp(msg.date) for msg in chat_data.contents)` |
| `ParticipantCount` | `chat_data.contents[*].sender_id` | Count of unique sender IDs (both users and chats): `len(participants)` |
| `MessageCount` | `chat_data.contents` | Length of contents array: `len(chat_data.contents)` |

#### ChatMessages Table

```python
class ChatMessages(Base):
    __tablename__ = 'chat_messages'
    
    MessageID = Column(String, primary_key=True)
    SubmissionChatID = Column(String, ForeignKey('submission_chats.SubmissionChatID'), nullable=False)
    SourceMessageID = Column(String, nullable=False)
    SenderID = Column(String, nullable=False)
    MessageDate = Column(DateTime, nullable=False)
    ContentType = Column(String, nullable=False)
    Content = Column(Text, nullable=True)
    ContentData = Column(LargeBinary, nullable=True)
```

##### MinerTransformer (miner-fileDto.json)

| Model Field | JSON Source | Logic/Condition |
|-------------|-------------|----------------|
| `MessageID` | N/A | Generated using `str(uuid.uuid4())` |
| `SubmissionChatID` | N/A | Foreign key reference to generated SubmissionChats.SubmissionChatID |
| `SourceMessageID` | `msg_content.id` | Converted to string: `str(msg_content.id)` |
| `SenderID` | `msg_content.fromId.userId` | Direct mapping if exists, otherwise `"unknown"` |
| `MessageDate` | `msg_content.date` | Converted to datetime: `datetime.fromtimestamp(msg_content.date)` |
| `ContentType` | Based on detection | "text", "service", "document", "photo", "audio", "video", or "media" based on message content |
| `Content` | Various (see below) | Depends on ContentType |
| `ContentData` | Various (see below) | For messages with media content: stores the binary media data<br>For text/service messages: stores the message metadata as UTF-8 encoded JSON |

**ContentType and Content Determination for MinerTransformer:**

```python
# Case 1: Regular text message
if msg_content.className == "Message" and hasattr(msg_content, 'message') and msg_content.message:
    content_type = "text"
    content = msg_content.message

# Case 2: Document media
if hasattr(msg_content.media, 'className') and msg_content.media.className == "MessageMediaDocument":
    content_type = "document"
    # Try to extract filename and other document attributes
    
# Case 3: Photo media
elif msg_content.media.className == "MessageMediaPhoto":
    content_type = "photo"
    # Extract caption text and photo data

# Case 4: Other media type
else:
    content_type = "media"
    content = f"Media: {getattr(msg_content.media, 'className', 'unknown type')}"

# Case 5: Service message
elif msg_content.className == "MessageService":
    content_type = "service"
    content = f"Service message: {getattr(msg_content.action, 'className', 'unknown action')}"
```

**ContentData Storage Logic for MinerTransformer:**

```python
# Create metadata dictionary for all message types
metadata = {
    "original_message": msg_content.dict() if hasattr(msg_content, 'dict') else _object_to_dict(msg_content),
    "is_outgoing": is_outgoing
}

# If binary media data is available, store it directly in ContentData
if media_binary:
    content_data = media_binary if isinstance(media_binary, bytes) else str(media_binary).encode('utf-8')
else:
    # Otherwise store metadata as encoded JSON
    content_data = json.dumps(metadata).encode('utf-8')
```

##### WebappTransformer (webapp-fileDto.json)

| Model Field | JSON Source | Logic/Condition |
|-------------|-------------|----------------|
| `MessageID` | N/A | Generated using `str(uuid.uuid4())` |
| `SubmissionChatID` | N/A | Foreign key reference to generated SubmissionChats.SubmissionChatID |
| `SourceMessageID` | `msg_content.id` | Converted to string: `str(msg_content.id)` |
| `SenderID` | `msg_content.sender_id.user_id` or `msg_content.sender_id.chat_id` | Extracts ID based on sender type |
| `MessageDate` | `msg_content.date` | Converted to datetime: `datetime.fromtimestamp(msg_content.date)` |
| `ContentType` | `msg_content.content.type` | "text", "photo", "video", "document", or "unknown" based on content type |
| `Content` | Various (see below) | Depends on ContentType |
| `ContentData` | Various (see below) | For messages with media content: stores thumbnail data as binary content<br>For text messages: may be null or contain additional metadata |

**ContentType and Content Determination for WebappTransformer:**

```python
# Case 1: Text message
if msg_content.content.type == "messageText":
    content_type = "text"
    # Extract text from either string or FormattedText

# Case 2: Photo message
elif msg_content.content.type == "messagePhoto":
    content_type = "photo"
    # Extract caption text and thumbnail data

# Case 3: Video message
elif msg_content.content.type == "messageVideo":
    content_type = "video"
    # Extract caption text and thumbnail data

# Case 4: Document message
elif msg_content.content.type == "messageDocument":
    content_type = "document"
    # Extract caption text and thumbnail data
```

**ContentData Storage Logic for WebappTransformer:**

```python
# For photos, videos, and documents, extract thumbnail when available
if content_type in ["photo", "video", "document"]:
    # Try to get minithumbnail data
    if hasattr(media_object, 'minithumbnail') and media_object.minithumbnail:
        try:
            # Convert base64 data to binary
            thumb_data = media_object.minithumbnail.data
            content_data = base64.b64decode(thumb_data)
        except Exception as e:
            logging.error(f"Error extracting thumbnail data: {e}")
```

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
1. Modify the config to match your environment, or add a .env file at the root. See below for defaults.
1. Update the schemas in `refiner/models/` to define your raw and normalized data models
1. Modify the refinement logic in `refiner/transformer/` to match your data structure
1. If needed, modify `refiner/refiner.py` with your file(s) that need to be refined
1. Build and test your refinement container

### Environment variables
```dotenv
# Local directories where inputs and outputs are found. When running on the refinement service, files will be mounted to the /input and /output directory of the container.
INPUT_DIR=input
OUTPUT_DIR=output

# This key is derived from the user file's original encryption key, automatically injected into the container by the refinement service. When developing locally, any string can be used here for testing.
REFINEMENT_ENCRYPTION_KEY=0x1234

# Required if using https://pinata.cloud (IPFS pinning service)
PINATA_API_KEY=xxx
PINATA_API_SECRET=yyy
```

## Local Development

To run the refinement locally for testing:

```bash
# With Python
pip install --no-cache-dir -r requirements.txt
python -m refiner

# Or with Docker
docker build -t refiner --platform linux/x86_64 .
docker save refiner:latest | gzip > refiner-20250602.tar.gz
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

