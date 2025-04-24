#!/usr/bin/env python3
"""
Script to validate that Telegram miner data has been properly refined.
"""
import json
import sqlite3
import os
import sys
import re
import uuid
from datetime import datetime

# Paths to files
DB_PATH = "output/db.libsql"
INPUT_PATH = "input/miner-fileDto.json"

class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass

def load_input_data():
    """Read input data"""
    try:
        with open(INPUT_PATH, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error reading input file: {e}")
        sys.exit(1)

def connect_db():
    """Connect to the SQLite database"""
    try:
        if not os.path.exists(DB_PATH):
            raise FileNotFoundError(f"Database file not found: {DB_PATH}")
        return sqlite3.connect(DB_PATH)
    except Exception as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)

def validate_db_structure(conn):
    """Check database structure"""
    cursor = conn.cursor()
    
    # List of tables to check
    expected_tables = [
        "users", "submissions", "submission_chats", "chat_messages"
    ]
    
    # Check if tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    actual_tables = [row[0] for row in cursor.fetchall()]
    
    missing_tables = set(expected_tables) - set(actual_tables)
    if missing_tables:
        raise ValidationError(f"Missing tables: {', '.join(missing_tables)}")
    
    print(f"✅ Valid database structure, found all {len(expected_tables)} tables")
    
    # Check record count in each table
    for table in expected_tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  - {table}: {count} records")
    
    return True

def validate_users(conn, input_data):
    """Check that users data has been properly refined"""
    cursor = conn.cursor()
    
    # Check user record
    cursor.execute("SELECT UserID, Source, SourceUserId, Status, DateTimeCreated FROM users")
    user = cursor.fetchone()
    
    if not user:
        raise ValidationError("No records found in users table")
    
    user_id, source, source_user_id, status, date_created = user
    
    # Check user ID format (should be a valid UUID)
    try:
        uuid.UUID(user_id)
    except ValueError:
        raise ValidationError(f"Invalid UUID format for UserID: {user_id}")
    
    # Check specific fields
    assert source == "Telegram", f"Source mismatch: {source} != Telegram"
    assert source_user_id == input_data.get("user"), f"SourceUserId mismatch: {source_user_id} != {input_data.get('user')}"
    assert status == "active", f"Status mismatch: {status} != active"
    
    print(f"✅ Users data is valid")
    return user_id

def validate_submissions(conn, user_id, input_data):
    """Check that submissions data has been properly refined"""
    cursor = conn.cursor()
    
    # Get submission record
    cursor.execute("SELECT SubmissionID, UserID, SubmissionDate, SubmissionReference FROM submissions")
    submission = cursor.fetchone()
    
    if not submission:
        raise ValidationError("No records found in submissions table")
    
    submission_id, db_user_id, submission_date, submission_reference = submission
    
    # Check submission ID format (should be a valid UUID)
    try:
        uuid.UUID(submission_id)
    except ValueError:
        raise ValidationError(f"Invalid UUID format for SubmissionID: {submission_id}")
    
    # Check foreign key relationship
    assert db_user_id == user_id, f"UserID mismatch in submission: {db_user_id} != {user_id}"
    
    # Check reference
    assert submission_reference == input_data.get("submission_token"), f"SubmissionReference mismatch: {submission_reference} != {input_data.get('submission_token')}"
    
    print(f"✅ Submissions data is valid")
    return submission_id

def validate_submission_chats(conn, submission_id, input_data):
    """Check that submission_chats data has been properly refined"""
    cursor = conn.cursor()
    
    # Get all chats
    cursor.execute("""
        SELECT SubmissionChatID, SubmissionID, SourceChatID, FirstMessageDate, 
               LastMessageDate, ParticipantCount, MessageCount 
        FROM submission_chats
    """)
    chats = cursor.fetchall()
    
    input_chats = input_data.get("chats", [])
    
    if len(chats) != len(input_chats):
        raise ValidationError(f"Chat count mismatch: {len(chats)} != {len(input_chats)}")
    
    # Create lookup dictionary for input chats
    input_chats_lookup = {str(chat["chat_id"]): chat for chat in input_chats}
    chat_ids = []
    
    for chat in chats:
        chat_id, db_submission_id, source_chat_id, first_date, last_date, participant_count, message_count = chat
        
        # Store chat_id for later message validation
        chat_ids.append(chat_id)
        
        # Check UUID format
        try:
            uuid.UUID(chat_id)
        except ValueError:
            raise ValidationError(f"Invalid UUID format for SubmissionChatID: {chat_id}")
        
        # Remove leading "-" if present in source_chat_id (telegram format)
        source_chat_id_clean = source_chat_id.lstrip("-")
        
        # Check if source_chat_id exists in input data
        found = False
        for input_chat_id, input_chat in input_chats_lookup.items():
            if str(abs(int(input_chat_id))) == source_chat_id_clean:
                found = True
                break
                
        if not found:
            raise ValidationError(f"source_chat_id {source_chat_id} not found in input data")
        
        # Check submission_id foreign key
        assert db_submission_id == submission_id, f"SubmissionID mismatch for chat {chat_id}: {db_submission_id} != {submission_id}"
        
        # Check message count (this may need to be adjusted based on your filtering logic)
        input_message_count = len(input_chat["contents"])
        # Since we might only process a subset of messages, we just check if it's reasonable
        assert message_count <= input_message_count, f"MessageCount too high: {message_count} > {input_message_count}"
    
    print(f"✅ Submission chats data is valid ({len(chats)} chats)")
    return chat_ids

def validate_chat_messages(conn, chat_ids, input_data):
    """Check that chat_messages data has been properly refined"""
    cursor = conn.cursor()
    
    # Get total message count
    cursor.execute("SELECT COUNT(*) FROM chat_messages")
    total_message_count = cursor.fetchone()[0]
    
    # Count messages in input data
    input_message_count = sum(len(chat["contents"]) for chat in input_data.get("chats", []))
    
    # Since we might filter some messages or only process a subset, just check if it's reasonable
    assert total_message_count <= input_message_count, f"Total message count too high: {total_message_count} > {input_message_count}"
    
    # Check a sample of messages from each chat
    for chat_id in chat_ids:
        cursor.execute("""
            SELECT MessageID, SubmissionChatID, SourceMessageID, SenderID, 
                   MessageDate, ContentType, Content 
            FROM chat_messages 
            WHERE SubmissionChatID = ? 
            LIMIT 5
        """, (chat_id,))
        messages = cursor.fetchall()
        
        if not messages:
            print(f"Warning: No messages found for chat {chat_id}")
            continue
        
        for message in messages:
            msg_id, db_chat_id, source_msg_id, sender_id, msg_date, content_type, content = message
            
            # Check UUID format
            try:
                uuid.UUID(msg_id)
            except ValueError:
                raise ValidationError(f"Invalid UUID format for MessageID: {msg_id}")
            
            # Check chat_id foreign key
            assert db_chat_id == chat_id, f"SubmissionChatID mismatch for message {msg_id}: {db_chat_id} != {chat_id}"
            
            # Check content type is valid
            assert content_type in ["text", "service", "media"], f"Invalid ContentType: {content_type}"
            
            # For text messages, content should not be null
            if content_type == "text":
                assert content is not None, f"Content is null for text message {msg_id}"
    
    print(f"✅ Chat messages data is valid ({total_message_count} messages total)")
    return True

def main():
    """Run validation checks"""
    print("Starting validation...")
    
    # Load input data
    input_data = load_input_data()
    print(f"Loaded input data: {INPUT_PATH}")
    
    # Connect to DB
    conn = connect_db()
    print(f"Connected to database: {DB_PATH}")
    
    try:
        # Validate structure
        validate_db_structure(conn)
        
        # Validate users
        user_id = validate_users(conn, input_data)
        
        # Validate submissions
        submission_id = validate_submissions(conn, user_id, input_data)
        
        # Validate submission chats
        chat_ids = validate_submission_chats(conn, submission_id, input_data)
        
        # Validate chat messages
        validate_chat_messages(conn, chat_ids, input_data)
        
        print("\n🎉 All validation checks passed! Data has been correctly refined.")
        return 0
        
    except ValidationError as e:
        print(f"\n❌ Validation error: {e}")
        return 1
    except AssertionError as e:
        print(f"\n❌ Assertion failed: {e}")
        return 1
    finally:
        conn.close()

if __name__ == "__main__":
    sys.exit(main()) 