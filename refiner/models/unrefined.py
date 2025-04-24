from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field


class Profile(BaseModel):
    name: str
    locale: str

class Metadata(BaseModel):
    source: str
    collectionDate: str
    dataType: str

class ForwardInfo(BaseModel):
    originalSender: str
    originalDate: int

class Media(BaseModel):
    flags: Optional[int] = None
    nopremium: Optional[bool] = None
    spoiler: Optional[bool] = None
    forceSmall: Optional[bool] = None
    forceLargeMedia: Optional[bool] = None
    className: Optional[str] = None  # MessageMediaWebPage, MessageMediaDocument, MessageMediaPhoto, etc.
    
    # Legacy fields
    type: Optional[str] = None
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
    metadata: Optional[Metadata] = None
    telegramData: Optional[TelegramData] = None

class FromId(BaseModel):
    userId: str
    className: str


class PeerId(BaseModel):
    chatId: str
    className: str


class ReplyTo(BaseModel):
    flags: int
    replyToScheduled: bool = False
    forumTopic: bool = False
    quote: bool = False
    replyToMsgId: Optional[int] = None
    replyToPeerId: Optional[Any] = None
    replyFrom: Optional[Any] = None
    replyMedia: Optional[Any] = None
    replyToTopId: Optional[Any] = None
    quoteText: Optional[str] = None
    quoteEntities: Optional[Any] = None
    quoteOffset: Optional[int] = None
    className: str


class Action(BaseModel):
    inviterId: Optional[str] = None
    className: str


class FwdFrom(BaseModel):
    flags: int
    imported: bool = False
    savedOut: bool = False
    fromId: Optional[FromId] = None
    fromName: Optional[str] = None
    date: int
    channelPost: Optional[int] = None
    postAuthor: Optional[str] = None
    savedFromPeer: Optional[Any] = None
    savedFromMsgId: Optional[int] = None
    savedFromId: Optional[Any] = None
    savedFromName: Optional[str] = None
    savedDate: Optional[int] = None
    psaType: Optional[str] = None
    className: str


class MessageContent(BaseModel):
    flags: int
    out: bool
    mentioned: bool
    mediaUnread: bool
    reactionsArePossible: Optional[bool] = None
    silent: bool
    post: bool
    legacy: bool
    id: int
    fromId: Optional[FromId] = None
    fromBoostsApplied: Optional[Any] = None
    peerId: PeerId
    savedPeerId: Optional[Any] = None
    fwdFrom: Optional[FwdFrom] = None
    viaBotId: Optional[Any] = None
    viaBusinessBotId: Optional[Any] = None
    replyTo: Optional[ReplyTo] = None
    date: int
    message: Optional[str] = None
    media: Optional[Media] = None
    replyMarkup: Optional[Any] = None
    entities: Optional[Any] = None
    views: Optional[int] = None
    forwards: Optional[int] = None
    replies: Optional[Any] = None
    editDate: Optional[int] = None
    postAuthor: Optional[str] = None
    groupedId: Optional[Any] = None
    reactions: Optional[Any] = None
    restrictionReason: Optional[Any] = None
    ttlPeriod: Optional[int] = None
    action: Optional[Action] = None
    className: str = Field(..., description="Type of message: Message or MessageService")


class ChatData(BaseModel):
    chat_id: int
    contents: List[MessageContent]


class MinerFileDto(BaseModel):
    revision: str
    source: str
    user: str
    submission_token: str
    chats: List[ChatData]