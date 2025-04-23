#!/usr/bin/env python3
"""
Script to validate that Telegram data has been properly refined.
"""
import json
import sqlite3
import os
import sys
import re
from datetime import datetime

# Paths to files
DB_PATH = "output/db.libsql"
INPUT_PATH = "input/a_telegram_data.json"

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
        "users", "auth_sources", "telegram_accounts", 
        "telegram_chats", "telegram_messages", 
        "telegram_media", "telegram_forwards"
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

def validate_telegram_account(conn, input_data):
    """Check that telegram_accounts data has been properly refined"""
    cursor = conn.cursor()
    
    # Check Telegram account
    cursor.execute("SELECT account_id, user_id, username, phone_masked, is_bot, is_premium, join_date FROM telegram_accounts")
    account = cursor.fetchone()
    
    if not account:
        raise ValidationError("No records found in telegram_accounts table")
    
    account_id, user_id, username, phone_masked, is_bot, is_premium, join_date = account
    
    # Check specific fields
    input_telegram = input_data.get("telegramData", {})
    
    assert user_id == input_data.get("userId"), f"user_id mismatch: {user_id} != {input_data.get('userId')}"
    assert username == input_telegram.get("username"), f"username mismatch: {username} != {input_telegram.get('username')}"
    
    # Check phone_masked (Phone number must be masked)
    phone = input_telegram.get("phoneNumber", "")
    assert phone_masked != phone, "Phone number has not been masked"
    assert phone[-4:] in phone_masked, "Phone masking format is incorrect"
    
    # Check boolean values
    assert is_bot == (1 if input_telegram.get("isBot") else 0), f"is_bot mismatch: {is_bot} != {input_telegram.get('isBot')}"
    assert is_premium == (1 if input_telegram.get("isPremium") else 0), f"is_premium mismatch: {is_premium} != {input_telegram.get('isPremium')}"
    
    print(f"✅ Telegram account data is valid")
    return account_id

def validate_telegram_chats(conn, account_id, input_data):
    """Check that telegram_chats data has been properly refined"""
    cursor = conn.cursor()
    
    # Get all chats
    cursor.execute("SELECT chat_id, account_id, type, title, username, member_count, subscriber_count, message_count, last_activity FROM telegram_chats")
    chats = cursor.fetchall()
    
    input_chats = input_data.get("telegramData", {}).get("chats", [])
    
    if len(chats) != len(input_chats):
        raise ValidationError(f"Chat count mismatch: {len(chats)} != {len(input_chats)}")
    
    # Create lookup dictionary for input chats
    input_chats_lookup = {chat["chatId"]: chat for chat in input_chats}
    
    for chat in chats:
        chat_id, db_account_id, chat_type, title, username, member_count, subscriber_count, message_count, last_activity = chat
        
        # Check if chat_id exists in input data
        if chat_id not in input_chats_lookup:
            raise ValidationError(f"chat_id {chat_id} not found in input data")
        
        input_chat = input_chats_lookup[chat_id]
        
        # Check account_id
        assert db_account_id == account_id, f"account_id mismatch for chat {chat_id}: {db_account_id} != {account_id}"
        
        # Check other fields
        assert chat_type == input_chat.get("type"), f"type mismatch for chat {chat_id}: {chat_type} != {input_chat.get('type')}"
        assert title == input_chat.get("title"), f"title mismatch for chat {chat_id}: {title} != {input_chat.get('title')}"
        
        if "username" in input_chat:
            assert username == input_chat.get("username"), f"username mismatch for chat {chat_id}: {username} != {input_chat.get('username')}"
        
        if "memberCount" in input_chat:
            assert member_count == input_chat.get("memberCount"), f"member_count mismatch for chat {chat_id}: {member_count} != {input_chat.get('memberCount')}"
        
        if "subscriberCount" in input_chat:
            assert subscriber_count == input_chat.get("subscriberCount"), f"subscriber_count mismatch for chat {chat_id}: {subscriber_count} != {input_chat.get('subscriberCount')}"
        
        assert message_count == input_chat.get("messageCount"), f"message_count mismatch for chat {chat_id}: {message_count} != {input_chat.get('messageCount')}"
    
    print(f"✅ Telegram chats data is valid ({len(chats)} chats)")
    return True

def validate_telegram_messages(conn, account_id, input_data):
    """Check that telegram_messages data has been properly refined"""
    cursor = conn.cursor()
    
    # Get all messages
    cursor.execute("SELECT message_id, chat_id, account_id, text, is_outgoing, reply_to_message_id, has_media FROM telegram_messages")
    messages = cursor.fetchall()
    
    input_messages = input_data.get("telegramData", {}).get("messages", [])
    
    if len(messages) != len(input_messages):
        raise ValidationError(f"Message count mismatch: {len(messages)} != {len(input_messages)}")
    
    # Create lookup dictionary for input messages
    input_messages_lookup = {msg["messageId"]: msg for msg in input_messages}
    
    # Check each message
    for message in messages:
        message_id, chat_id, db_account_id, text, is_outgoing, reply_to_message_id, has_media = message
        
        # Check if message_id exists in input data
        if message_id not in input_messages_lookup:
            raise ValidationError(f"message_id {message_id} not found in input data")
        
        input_message = input_messages_lookup[message_id]
        
        # Check account_id
        assert db_account_id == account_id, f"account_id mismatch for message {message_id}: {db_account_id} != {account_id}"
        
        # Check chat_id
        assert chat_id == input_message.get("chatId"), f"chat_id mismatch for message {message_id}: {chat_id} != {input_message.get('chatId')}"
        
        # Check other fields
        assert text == input_message.get("text"), f"text mismatch for message {message_id}: {text} != {input_message.get('text')}"
        assert is_outgoing == (1 if input_message.get("isOutgoing") else 0), f"is_outgoing mismatch for message {message_id}: {is_outgoing} != {input_message.get('isOutgoing')}"
        
        # Check reply_to_message_id (may be NULL)
        input_reply = input_message.get("replyToMessageId")
        if input_reply is None:
            assert reply_to_message_id is None, f"reply_to_message_id mismatch for message {message_id}: {reply_to_message_id} != None"
        else:
            assert reply_to_message_id == input_reply, f"reply_to_message_id mismatch for message {message_id}: {reply_to_message_id} != {input_reply}"
        
        # Check has_media
        assert has_media == (1 if input_message.get("hasMedia") else 0), f"has_media mismatch for message {message_id}: {has_media} != {input_message.get('hasMedia')}"
        
        # Check media and forward data
        if has_media:
            validate_media(conn, message_id, input_message)
        
        if input_message.get("forwardInfo"):
            validate_forward(conn, message_id, input_message)
    
    print(f"✅ Telegram messages data is valid ({len(messages)} messages)")
    return True

def validate_media(conn, message_id, input_message):
    """Check that media data has been properly refined"""
    cursor = conn.cursor()
    
    # Get media for message
    cursor.execute("SELECT media_type, caption, file_size FROM telegram_media WHERE message_id = ?", (message_id,))
    media = cursor.fetchone()
    
    if not media:
        raise ValidationError(f"No media found for message_id {message_id}")
    
    media_type, caption, file_size = media
    input_media = input_message.get("media", {})
    
    # Check fields
    assert media_type == input_media.get("type"), f"media_type mismatch for message {message_id}: {media_type} != {input_media.get('type')}"
    
    if "caption" in input_media:
        assert caption == input_media.get("caption"), f"caption mismatch for message {message_id}: {caption} != {input_media.get('caption')}"
    
    if "fileSize" in input_media:
        assert file_size == input_media.get("fileSize"), f"file_size mismatch for message {message_id}: {file_size} != {input_media.get('fileSize')}"
    
    return True

def validate_forward(conn, message_id, input_message):
    """Check that forward data has been properly refined"""
    cursor = conn.cursor()
    
    # Get forward info for message
    cursor.execute("SELECT original_sender, original_date FROM telegram_forwards WHERE message_id = ?", (message_id,))
    forward = cursor.fetchone()
    
    if not forward:
        raise ValidationError(f"No forward info found for message_id {message_id}")
    
    original_sender, original_date = forward
    input_forward = input_message.get("forwardInfo", {})
    
    # Check fields
    assert original_sender == input_forward.get("originalSender"), f"original_sender mismatch for message {message_id}: {original_sender} != {input_forward.get('originalSender')}"
    
    return True

def validate_relationships(conn):
    """Check relationships between tables"""
    cursor = conn.cursor()
    
    # Check user -> telegram_account relationship
    cursor.execute("""
        SELECT u.user_id, ta.account_id 
        FROM users u
        JOIN telegram_accounts ta ON u.user_id = ta.user_id
    """)
    user_accounts = cursor.fetchall()
    
    if not user_accounts:
        raise ValidationError("No relationship found between users and telegram_accounts")
    
    # Check telegram_account -> telegram_chats relationship
    cursor.execute("""
        SELECT ta.account_id, COUNT(tc.chat_id) 
        FROM telegram_accounts ta
        JOIN telegram_chats tc ON ta.account_id = tc.account_id
        GROUP BY ta.account_id
    """)
    account_chats = cursor.fetchall()
    
    if not account_chats:
        raise ValidationError("No relationship found between telegram_accounts and telegram_chats")
    
    # Check telegram_chats -> telegram_messages relationship
    cursor.execute("""
        SELECT tc.chat_id, COUNT(tm.message_id) 
        FROM telegram_chats tc
        JOIN telegram_messages tm ON tc.chat_id = tm.chat_id
        GROUP BY tc.chat_id
    """)
    chat_messages = cursor.fetchall()
    
    if not chat_messages:
        raise ValidationError("No relationship found between telegram_chats and telegram_messages")
    
    # Check account -> messages relationship
    cursor.execute("""
        SELECT ta.account_id, COUNT(tm.message_id) 
        FROM telegram_accounts ta
        JOIN telegram_messages tm ON ta.account_id = tm.account_id
        GROUP BY ta.account_id
    """)
    account_messages = cursor.fetchall()
    
    if not account_messages:
        raise ValidationError("No relationship found between telegram_accounts and telegram_messages")
    
    print("✅ Relationships between tables are valid")
    return True

def main():
    """Main function to run validation"""
    try:
        print(f"🔍 Starting Telegram data validation from {INPUT_PATH} -> {DB_PATH}")
        
        # Read input data
        input_data = load_input_data()
        
        # Connect to database
        conn = connect_db()
        
        # Check database structure
        validate_db_structure(conn)
        
        # Check Telegram account data
        account_id = validate_telegram_account(conn, input_data)
        
        # Check Telegram chats data
        validate_telegram_chats(conn, account_id, input_data)
        
        # Check Telegram messages data
        validate_telegram_messages(conn, account_id, input_data)
        
        # Check relationships between tables
        validate_relationships(conn)
        
        # Close connection
        conn.close()
        
        print("\n✅ All checks passed! Telegram data has been properly refined.")
        return 0
        
    except ValidationError as e:
        print(f"\n❌ Validation error: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 