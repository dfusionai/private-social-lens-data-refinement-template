# Telegram Data Refinement Tests

This directory contains tests and validation scripts for the Telegram data refinement process.

## Purpose

These scripts verify that the data has been correctly refined from the raw Telegram export format into the structured database format required by the application.

## Available Scripts

### `validate_telegram_data.py`

This script validates that Telegram data has been properly refined by checking:

- Database structure (tables and relationships)
- Telegram account information
- Chat data integrity
- Message content and relationships
- Media attachments
- Forwarded message details

### `validate_miner_data.py`

This script validates that Telegram miner data has been properly refined by checking:

- Database structure with the new schema (Users, Submissions, SubmissionChats, ChatMessages)
- User record validation
- Submission record validation
- Chat metadata validation
- Message content validation
- Relationships between tables

## Usage

Run the validation scripts from the project root directory:

```bash
# For traditional Telegram data format
python tests/validate_telegram_data.py

# For miner-fileDto format
python tests/validate_miner_data.py
```

The scripts will:
1. Load the input data from their respective input files
2. Connect to the refined database at `output/db.libsql`
3. Perform comprehensive validation checks
4. Output the results with detailed error messages if any issues are found

## Expected Output for `validate_miner_data.py`

If all validation checks pass, you'll see:

```
Starting validation...
Loaded input data: input/miner-fileDto.json
Connected to database: output/db.libsql
✅ Valid database structure, found all 4 tables
  - users: 1 records
  - submissions: 1 records
  - submission_chats: 2 records
  - chat_messages: 100 records
✅ Users data is valid
✅ Submissions data is valid
✅ Submission chats data is valid (2 chats)
✅ Chat messages data is valid (100 messages total)

🎉 All validation checks passed! Data has been correctly refined.
```

## Manually checking the new schema:

### Validate user source
```bash
sqlite3 output/db.libsql "SELECT UserID, Source, SourceUserId FROM users"
```

### Validate submissions
```bash
sqlite3 output/db.libsql "SELECT SubmissionID, UserID, SubmissionReference FROM submissions"
```

### Check chat metadata
```bash
sqlite3 output/db.libsql "SELECT SourceChatID, FirstMessageDate, LastMessageDate, MessageCount FROM submission_chats"
```

### Query messages
```bash
sqlite3 output/db.libsql "SELECT SourceMessageID, SenderID, ContentType, substr(Content, 1, 30) FROM chat_messages LIMIT 5"
```

```bash
sqlite3 output/db.libsql "SELECT SourceMessageID, SenderID, ContentType, substr(Content, 1, 30), ContentData FROM chat_messages where ContentType='photo' LIMIT 10"
```