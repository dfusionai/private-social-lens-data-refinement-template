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

########################################
# Miner-fileDto.json specific models
########################################

class MinerFromId(BaseModel):
    userId: str
    className: str

class MinerPeerId(BaseModel):
    chatId: Optional[str] = None
    userId: Optional[str] = None
    channelId: Optional[str] = None
    className: str

class PeerUser(BaseModel):
    userId: Optional[str] = None
    className: str

class PeerChat(BaseModel):
    chatId: Optional[str] = None
    className: str

class PeerChannel(BaseModel):
    channelId: Optional[str] = None
    className: str

class MinerReplyTo(BaseModel):
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

class MinerAction(BaseModel):
    inviterId: Optional[str] = None
    className: str

class MinerFwdFrom(BaseModel):
    flags: int
    imported: bool = False
    savedOut: bool = False
    fromId: Optional[Any] = None
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

class MinerMedia(BaseModel):
    flags: Optional[int] = None
    className: Optional[str] = None
    document: Optional[Dict[str, Any]] = None
    attributes: Optional[List[Dict[str, Any]]] = None
    
class MinerMessageData(BaseModel):
    flags: int
    out: bool
    mentioned: Optional[bool] = False
    mediaUnread: Optional[bool] = False
    reactionsArePossible: Optional[bool] = True
    silent: Optional[bool] = False
    post: Optional[bool] = False
    legacy: Optional[bool] = False
    id: int
    fromId: Optional[Union[MinerFromId, PeerChannel, PeerChat]] = None
    peerId: Optional[MinerPeerId] = None
    fwdFrom: Optional[MinerFwdFrom] = None
    replyTo: Optional[MinerReplyTo] = None
    date: int
    message: Optional[str] = None
    media: Optional[MinerMedia] = None
    action: Optional[MinerAction] = None
    className: str

class MinerChatData(BaseModel):
    chat_id: int
    contents: List[MinerMessageData]

class MinerFileDto(BaseModel):
    """Root model for miner-fileDto.json"""
    revision: str
    source: str
    user: Union[int, str]
    submission_token: str
    chats: List[MinerChatData]


########################################
# Webapp-fileDto.json specific models
########################################

class File(BaseModel):
    """Model for file data"""
    type: str = Field(..., alias="@type")
    id: int
    size: int
    expected_size: int

class PhotoSize(BaseModel):
    """Model for photo size information"""
    type: str = Field(..., alias="@type")
    type_attr: str = Field(..., alias="type")
    photo: Optional[File] = None
    width: Optional[int] = None
    height: Optional[int] = None
    progressive_sizes: Optional[List[int]] = None

class Minithumbnail(BaseModel):
    """Model for minithumbnail"""
    type: str = Field(..., alias="@type")
    width: int
    height: int
    data: str

class Photo(BaseModel):
    """Model for photo content"""
    type: str = Field(..., alias="@type")
    has_stickers: bool
    minithumbnail: Optional[Minithumbnail] = None
    sizes: List[PhotoSize]

class TextEntity(BaseModel):
    """Model for text entity"""
    type: str = Field(..., alias="@type")
    offset: int
    length: int
    type_attr: Optional[Dict[str, Any]] = None

class FormattedText(BaseModel):
    """Model for formatted text content"""
    type: str = Field(..., alias="@type")
    text: str
    entities: Optional[List[TextEntity]] = []

class SenderUser(BaseModel):
    """Model for message sender user identification"""
    type: str = Field(..., alias="@type")
    user_id: int

class SenderChat(BaseModel):
    """Model for message sender chat identification"""
    type: str = Field(..., alias="@type")
    chat_id: int

class MessageContent(BaseModel):
    """Model for message content"""
    type: str = Field(..., alias="@type")
    photo: Optional[Photo] = None
    caption: Optional[FormattedText] = None
    text: Optional[Union[str, FormattedText]] = None
    show_caption_above_media: Optional[bool] = None
    has_spoiler: Optional[bool] = None
    is_secret: Optional[bool] = None

class InteractionInfo(BaseModel):
    """Model for message interaction information"""
    type: str = Field(..., alias="@type")
    view_count: int
    forward_count: int

class WebappMessageData(BaseModel):
    """Model for message data"""
    type: str = Field(..., alias="@type")
    id: int
    sender_id: Union[SenderUser, SenderChat]
    chat_id: int
    date: int
    edit_date: Optional[int] = None
    is_outgoing: bool
    is_pinned: bool
    is_from_offline: Optional[bool] = None
    can_be_saved: Optional[bool] = None
    has_timestamped_media: Optional[bool] = None
    is_channel_post: Optional[bool] = None
    is_topic_message: Optional[bool] = None
    contains_unread_mention: Optional[bool] = None
    interaction_info: Optional[InteractionInfo] = None
    content: MessageContent

class WebappChatData(BaseModel):
    """Model for chat data"""
    chat_id: int
    contents: List[WebappMessageData]

class WebappFileDto(BaseModel):
    """Root model for webapp-fileDto.json"""
    revision: str
    source: str
    user: Union[int, str]
    submission_token: str
    chats: List[WebappChatData]