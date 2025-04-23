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

## Usage

Run the validation script from the project root directory:

```bash
python tests/validate_telegram_data.py
```

The script will:
1. Load the input data from `input/a_telegram_data.json`
2. Connect to the refined database at `output/db.libsql`
3. Perform comprehensive validation checks
4. Output the results with detailed error messages if any issues are found

## Expected Output

If all validation checks pass, you'll see:

```
🔍 Starting Telegram data validation from input/a_telegram_data.json -> output/db.libsql
✅ Valid database structure, found all 7 tables
  - users: 1 records
  - auth_sources: 1 records
  - telegram_accounts: 1 records
  - telegram_chats: 3 records
  - telegram_messages: 4 records
  - telegram_media: 1 records
  - telegram_forwards: 1 records
✅ Telegram account data is valid
✅ Telegram chats data is valid (3 chats)
✅ Telegram messages data is valid (4 messages)
✅ Relationships between tables are valid

✅ All checks passed! Telegram data has been properly refined.
```

If any validation errors are found, the script will provide specific error messages to help identify and fix the issues. 


## Manually checking:

### Validate marked email
```bash
sqlite3 output/db.libsql "SELECT email FROM users"
```

### Validate marked phone number
```bash
sqlite3 output/db.libsql "SELECT phone_masked FROM telegram_accounts"
```

### Query messages
```bash
sqlite3 output/db.libsql "SELECT text FROM telegram_messages LIMIT 5"
```