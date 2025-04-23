from typing import Optional, List
from pydantic import BaseModel


class Profile(BaseModel):
    name: str
    locale: str

class Storage(BaseModel):
    percentUsed: float

class Metadata(BaseModel):
    source: str
    collectionDate: str
    dataType: str

class ForwardInfo(BaseModel):
    originalSender: str
    originalDate: int

class Media(BaseModel):
    type: str
    caption: Optional[str] = None
    fileSize: Optional[int] = None

class Message(BaseModel):
    messageId: int
    chatId: int
    chatType: str
    chatTitle: str
    timestamp: int
    text: str
    isOutgoing: bool
    replyToMessageId: Optional[int] = None
    forwardInfo: Optional[ForwardInfo] = None
    hasMedia: bool
    media: Optional[Media] = None

class Chat(BaseModel):
    chatId: int
    type: str
    title: str
    username: Optional[str] = None
    memberCount: Optional[int] = None
    subscriberCount: Optional[int] = None
    messageCount: int
    lastActivity: int

class TelegramData(BaseModel):
    username: str
    phoneNumber: str
    isBot: bool
    isPremium: bool
    joinDate: int
    messages: List[Message]
    chats: List[Chat]

class User(BaseModel):
    userId: str
    email: str
    timestamp: int
    profile: Profile
    storage: Optional[Storage] = None
    metadata: Optional[Metadata] = None
    telegramData: Optional[TelegramData] = None