from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

# Base model for SQLAlchemy
Base = declarative_base()

# Define database models - the schema is generated using these
class UserRefined(Base):
    __tablename__ = 'users'
    
    user_id = Column(String, primary_key=True)
    email = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    locale = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    
    auth_sources = relationship("AuthSource", back_populates="user")
    telegram_account = relationship("TelegramAccount", back_populates="user", uselist=False)

class AuthSource(Base):
    __tablename__ = 'auth_sources'
    
    auth_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey('users.user_id'), nullable=False)
    source = Column(String, nullable=False)
    collection_date = Column(DateTime, nullable=False)
    data_type = Column(String, nullable=False)
    
    user = relationship("UserRefined", back_populates="auth_sources")

class TelegramAccount(Base):
    __tablename__ = 'telegram_accounts'
    
    account_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey('users.user_id'), nullable=False, unique=True)
    username = Column(String, nullable=False)
    phone_masked = Column(String, nullable=True)  # Masked phone number for privacy
    is_bot = Column(Boolean, nullable=False, default=False)
    is_premium = Column(Boolean, nullable=False, default=False)
    join_date = Column(DateTime, nullable=False)
    
    user = relationship("UserRefined", back_populates="telegram_account")
    chats = relationship("TelegramChat", back_populates="account")
    messages = relationship("TelegramMessage", back_populates="account")

class TelegramChat(Base):
    __tablename__ = 'telegram_chats'
    
    chat_id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey('telegram_accounts.account_id'), nullable=False)
    type = Column(String, nullable=False)  # private, group, channel
    title = Column(String, nullable=False)
    username = Column(String, nullable=True)
    member_count = Column(Integer, nullable=True)
    subscriber_count = Column(Integer, nullable=True)
    message_count = Column(Integer, nullable=False, default=0)
    last_activity = Column(DateTime, nullable=False)
    
    account = relationship("TelegramAccount", back_populates="chats")
    messages = relationship("TelegramMessage", back_populates="chat")

class TelegramMessage(Base):
    __tablename__ = 'telegram_messages'
    
    message_id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey('telegram_chats.chat_id'), nullable=False)
    account_id = Column(Integer, ForeignKey('telegram_accounts.account_id'), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    text = Column(Text, nullable=True)
    is_outgoing = Column(Boolean, nullable=False)
    reply_to_message_id = Column(Integer, nullable=True)
    has_media = Column(Boolean, nullable=False, default=False)
    
    chat = relationship("TelegramChat", back_populates="messages")
    account = relationship("TelegramAccount", back_populates="messages")
    media = relationship("TelegramMedia", back_populates="message", uselist=False)
    forward_info = relationship("TelegramForward", back_populates="message", uselist=False)

class TelegramMedia(Base):
    __tablename__ = 'telegram_media'
    
    media_id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(Integer, ForeignKey('telegram_messages.message_id'), nullable=False, unique=True)
    media_type = Column(String, nullable=False)  # photo, video, document, etc.
    caption = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)
    
    message = relationship("TelegramMessage", back_populates="media")

class TelegramForward(Base):
    __tablename__ = 'telegram_forwards'
    
    forward_id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(Integer, ForeignKey('telegram_messages.message_id'), nullable=False, unique=True)
    original_sender = Column(String, nullable=False)
    original_date = Column(DateTime, nullable=False)
    
    message = relationship("TelegramMessage", back_populates="forward_info")
