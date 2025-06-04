from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime, Boolean, Text, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

# Base model for SQLAlchemy
Base = declarative_base()

# Define database models - the schema is generated using these
class Users(Base):
    __tablename__ = 'users'
    
    UserID = Column(String, primary_key=True)
    Source = Column(String, nullable=False)  # Telegram/WhatsApp
    SourceUserId = Column(String, nullable=False)
    Status = Column(String, nullable=False, default="active")  # active/deleted
    DateTimeCreated = Column(DateTime, nullable=False)
    
    submissions = relationship("Submissions", back_populates="user", cascade="all, delete-orphan")

class Submissions(Base):
    __tablename__ = 'submissions'
    
    SubmissionID = Column(String, primary_key=True)
    UserID = Column(String, ForeignKey('users.UserID'), nullable=False)
    SubmissionDate = Column(DateTime, nullable=False)
    SubmissionReference = Column(String, nullable=False)  # FileID
    
    user = relationship("Users", back_populates="submissions")
    chats = relationship("SubmissionChats", back_populates="submission", cascade="all, delete-orphan")

class SubmissionChats(Base):
    __tablename__ = 'submission_chats'
    
    SubmissionChatID = Column(String, primary_key=True)
    SubmissionID = Column(String, ForeignKey('submissions.SubmissionID'), nullable=False)
    SourceChatID = Column(String, nullable=False)
    FirstMessageDate = Column(DateTime, nullable=False)
    LastMessageDate = Column(DateTime, nullable=False)
    ParticipantCount = Column(Integer, nullable=True)
    MessageCount = Column(Integer, nullable=False, default=0)
    
    submission = relationship("Submissions", back_populates="chats")
    messages = relationship("ChatMessages", back_populates="chat", cascade="all, delete-orphan")

class ChatMessages(Base):
    __tablename__ = 'chat_messages'
    
    MessageID = Column(String, primary_key=True)
    SubmissionChatID = Column(String, ForeignKey('submission_chats.SubmissionChatID'), nullable=False)
    SourceMessageID = Column(String, nullable=False)
    SenderID = Column(String, nullable=False)  # AuthorId
    MessageDate = Column(DateTime, nullable=False)
    ContentType = Column(String, nullable=False)  # text/image/video/audio
    Content = Column(Text, nullable=True)  # text content
    ContentData = Column(LargeBinary, nullable=True)  # media data
    
    chat = relationship("SubmissionChats", back_populates="messages")
