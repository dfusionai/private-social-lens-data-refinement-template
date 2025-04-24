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

## Data Mapping Documentation

This section explains how data from the input JSON structure is mapped to the database models.

### Input JSON Structure

The input data follows this general format:

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

### Database Models → JSON Field Mapping

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

| Model Field | JSON Source | Logic/Condition |
|-------------|-------------|----------------|
| `UserID` | N/A | Generated using `str(uuid.uuid4())` |
| `Source` | N/A | Hard-coded value: `"Telegram"` |
| `SourceUserId` | `input_data.user` | Direct mapping from root `user` field |
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

| Model Field | JSON Source | Logic/Condition |
|-------------|-------------|----------------|
| `SubmissionID` | N/A | Generated using `str(uuid.uuid4())` |
| `UserID` | N/A | Foreign key reference to generated Users.UserID |
| `SubmissionDate` | N/A | Current timestamp: `datetime.now()` |
| `SubmissionReference` | `input_data.submission_token` | Direct mapping from root `submission_token` field |

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

| Model Field | JSON Source | Logic/Condition |
|-------------|-------------|----------------|
| `SubmissionChatID` | N/A | Generated using `str(uuid.uuid4())` |
| `SubmissionID` | N/A | Foreign key reference to generated Submissions.SubmissionID |
| `SourceChatID` | `chat_data.chat_id` | Converted to string: `str(chat_data.chat_id)` |
| `FirstMessageDate` | `chat_data.contents[*].date` | Converted to datetime: `min(datetime.fromtimestamp(msg.date) for msg in chat_data.contents)` |
| `LastMessageDate` | `chat_data.contents[*].date` | Converted to datetime: `max(datetime.fromtimestamp(msg.date) for msg in chat_data.contents)` |
| `ParticipantCount` | `chat_data.contents[*].fromId.userId` | Count of unique user IDs: `len(participants)` where `participants` is a set of all sender IDs |
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

| Model Field | JSON Source | Logic/Condition |
|-------------|-------------|----------------|
| `MessageID` | N/A | Generated using `str(uuid.uuid4())` |
| `SubmissionChatID` | N/A | Foreign key reference to generated SubmissionChats.SubmissionChatID |
| `SourceMessageID` | `msg_content.id` | Converted to string: `str(msg_content.id)` |
| `SenderID` | `msg_content.fromId.userId` | Direct mapping if exists, otherwise `"unknown"` |
| `MessageDate` | `msg_content.date` | Converted to datetime: `datetime.fromtimestamp(msg_content.date)` |
| `ContentType` | N/A | Derived based on message properties (see below) |
| `Content` | Various (see below) | Depends on ContentType |
| `ContentData` | N/A | Currently set to `None` (placeholder for future media processing) |

##### ContentType and Content Determination

The `ContentType` and `Content` fields are populated based on message properties:

```python
# Default values
content_type = "text"
content = None

# Case 1: Regular text message
if msg_content.className == "Message" and hasattr(msg_content, 'message') and msg_content.message:
    content_type = "text"
    content = msg_content.message

# Case 2: Service message
elif msg_content.className == "MessageService":
    content_type = "service"
    if hasattr(msg_content, 'action'):
        content = f"Service message: {msg_content.action.className}"

# Case 3: Media message
elif hasattr(msg_content, 'media') and msg_content.media:
    content_type = "media"
    content = "Media content"  # Placeholder for actual media processing
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

