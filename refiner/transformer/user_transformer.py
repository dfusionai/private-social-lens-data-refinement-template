from typing import Dict, Any, List
from refiner.models.refined import Base
from refiner.transformer.base_transformer import DataTransformer
from refiner.models.refined import Users, Submissions, SubmissionChats, ChatMessages
from refiner.models.unrefined import MinerFileDto
from refiner.utils.date import parse_timestamp
from refiner.utils.pii import mask_phone
from sqlalchemy.orm import Session
import uuid
import logging
from datetime import datetime

class UserTransformer(DataTransformer):
    """
    Transformer for Telegram chat data from miner-fileDto.json format.
    """
    
    def transform(self, data: Dict[str, Any]) -> List[Base]:
        """
        Transform raw Telegram data into SQLAlchemy model instances.
        
        Args:
            data: Dictionary containing Telegram data
            
        Returns:
            List of SQLAlchemy model instances
        """
        # Validate data with Pydantic
        try:
            miner_data = MinerFileDto.model_validate(data)
        except Exception as e:
            logging.error(f"Error validating miner data: {e}")
            raise
        
        models = []
        
        # Create user record
        user_id = str(uuid.uuid4())
        user = Users(
            UserID=user_id,
            Source="Telegram",
            SourceUserId=miner_data.user,
            Status="active",
            DateTimeCreated=datetime.now()
        )
        models.append(user)
        
        # Create submission record
        submission_id = str(uuid.uuid4())
        submission = Submissions(
            SubmissionID=submission_id,
            UserID=user_id,
            SubmissionDate=datetime.now(),
            SubmissionReference=miner_data.submission_token
        )
        models.append(submission)
        
        # Process each chat
        for chat_data in miner_data.chats:
            # Calculate chat statistics
            message_count = len(chat_data.contents)
            
            # Determine first and last message dates
            message_dates = []
            for msg in chat_data.contents:
                if hasattr(msg, 'date') and msg.date:
                    message_dates.append(datetime.fromtimestamp(msg.date))
            
            first_message_date = min(message_dates) if message_dates else datetime.now()
            last_message_date = max(message_dates) if message_dates else datetime.now()
            
            # Count unique participants
            participants = set()
            for msg in chat_data.contents:
                if hasattr(msg, 'fromId') and msg.fromId and hasattr(msg.fromId, 'userId'):
                    participants.add(msg.fromId.userId)
            
            # Create SubmissionChat record
            chat_id = str(uuid.uuid4())
            chat = SubmissionChats(
                SubmissionChatID=chat_id,
                SubmissionID=submission_id,
                SourceChatID=str(chat_data.chat_id),
                FirstMessageDate=first_message_date,
                LastMessageDate=last_message_date,
                ParticipantCount=len(participants),
                MessageCount=message_count
            )
            models.append(chat)
            
            # Process each message in the chat
            for msg_content in chat_data.contents:
                # Initialize variables
                content_type = "text"
                content = None
                content_data = None
                
                # Get sender ID from fromId object
                sender_id = "unknown"
                if hasattr(msg_content, 'fromId') and msg_content.fromId and hasattr(msg_content.fromId, 'userId'):
                    sender_id = str(msg_content.fromId.userId)
                
                # Get chat ID
                chat_source_id = str(chat_data.chat_id)
                
                # Get outgoing status
                is_outgoing = False
                if hasattr(msg_content, 'out') and msg_content.out:
                    is_outgoing = True
                
                # Handle different message types
                if msg_content.className == "Message":
                    # Handle text messages
                    if hasattr(msg_content, 'message') and msg_content.message:
                        content_type = "text"
                        content = msg_content.message
                    
                    # Handle media messages
                    if hasattr(msg_content, 'media') and msg_content.media:
                        if hasattr(msg_content.media, 'className') and msg_content.media.className == "MessageMediaDocument":
                            content_type = "document"
                            # Try to get document filename if available
                            try:
                                if hasattr(msg_content.media, 'document') and msg_content.media.document:
                                    doc = msg_content.media.document
                                    if hasattr(doc, 'attributes') and doc.attributes:
                                        for attr in doc.attributes:
                                            if attr.get('className') == "DocumentAttributeFilename":
                                                content = f"Document: {attr.get('fileName', 'unnamed')}"
                                                break
                            except Exception as e:
                                logging.warning(f"Error processing document attributes: {e}")
                                content = "Document attachment"
                        else:
                            content_type = "media"
                            content = f"Media: {getattr(msg_content.media, 'className', 'unknown type')}"
                
                elif msg_content.className == "MessageService":
                    content_type = "service"
                    if hasattr(msg_content, 'action') and msg_content.action:
                        content = f"Service message: {getattr(msg_content.action, 'className', 'unknown action')}"
                    else:
                        content = "Service message"

                # Create ChatMessage record
                message = ChatMessages(
                    MessageID=str(uuid.uuid4()),
                    SubmissionChatID=chat_id,
                    SourceMessageID=str(msg_content.id),
                    SenderID=sender_id,
                    MessageDate=datetime.fromtimestamp(msg_content.date),
                    ContentType=content_type,
                    Content=content,
                    ContentData=content_data
                )
                models.append(message)
        
        return models