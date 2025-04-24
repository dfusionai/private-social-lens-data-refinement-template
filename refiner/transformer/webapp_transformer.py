from typing import Dict, Any, List
from refiner.models.refined import Base
from refiner.transformer.base_transformer import DataTransformer
from refiner.models.refined import Users, Submissions, SubmissionChats, ChatMessages
from refiner.models.unrefined import MinerFileDto
from datetime import datetime
import uuid
import logging
import base64

class WebappTransformer(DataTransformer):
    """
    Transformer for Telegram chat data from webapp-fileDto.json format.
    """
    
    def transform(self, data: Dict[str, Any]) -> List[Base]:
        """
        Transform raw Telegram webapp data into SQLAlchemy model instances.
        
        Args:
            data: Dictionary containing Telegram webapp data
            
        Returns:
            List of SQLAlchemy model instances
        """
        # Validate data with Pydantic
        try:
            miner_data = MinerFileDto.model_validate(data)
        except Exception as e:
            logging.error(f"Error validating webapp data: {e}")
            raise
        
        models = []
        
        # Create user record
        user_id = str(uuid.uuid4())
        user = Users(
            UserID=user_id,
            Source=miner_data.source,
            SourceUserId=str(miner_data.user),
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
            SubmissionReference=miner_data.submission_token or f"webapp-{datetime.now().timestamp()}"
        )
        models.append(submission)
        
        # Process each chat
        for chat_data in miner_data.chats:
            # Calculate chat statistics
            message_count = len(chat_data.contents)
            
            # Determine first and last message dates
            message_dates = [datetime.fromtimestamp(msg.date) for msg in chat_data.contents]
            first_message_date = min(message_dates) if message_dates else datetime.now()
            last_message_date = max(message_dates) if message_dates else datetime.now()
            
            # Count unique participants
            participants = set()
            for msg in chat_data.contents:
                if msg.sender_id.type == "messageSenderChat":
                    participants.add(str(msg.sender_id.chat_id))
                elif msg.sender_id.type == "messageSenderUser":
                    participants.add(str(msg.sender_id.user_id))
            
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
                # Get sender ID
                sender_id = None
                if msg_content.sender_id.type == "messageSenderChat":
                    sender_id = str(msg_content.sender_id.chat_id)
                elif msg_content.sender_id.type == "messageSenderUser":
                    sender_id = str(msg_content.sender_id.user_id)
                else:
                    sender_id = "unknown"
                
                # Determine content type and actual content
                content_type = "unknown"
                content = None
                content_data = None
                
                if msg_content.content.type == "messageText":
                    content_type = "text"
                    # Handle either string or FormattedText
                    if hasattr(msg_content.content, 'text'):
                        if isinstance(msg_content.content.text, str):
                            content = msg_content.content.text
                        elif hasattr(msg_content.content.text, 'text'):
                            content = msg_content.content.text.text
                
                elif msg_content.content.type == "messagePhoto":
                    content_type = "photo"
                    if hasattr(msg_content.content, 'caption') and msg_content.content.caption:
                        content = msg_content.content.caption.text
                    
                    # Extract photo data
                    if hasattr(msg_content.content, 'photo') and msg_content.content.photo:
                        # Try to get minithumbnail data
                        if hasattr(msg_content.content.photo, 'minithumbnail') and msg_content.content.photo.minithumbnail:
                            try:
                                # Convert base64 data to binary
                                thumb_data = msg_content.content.photo.minithumbnail.data
                                content_data = base64.b64decode(thumb_data)
                                logging.info(f"Extracted photo thumbnail data for message {msg_content.id}")
                            except Exception as e:
                                logging.error(f"Error extracting photo data: {e}")
                
                elif msg_content.content.type == "messageVideo":
                    content_type = "video"
                    if hasattr(msg_content.content, 'caption') and msg_content.content.caption:
                        content = msg_content.content.caption.text
                    
                    # For videos, we could extract thumbnail if available
                    if hasattr(msg_content.content, 'video') and msg_content.content.video:
                        if hasattr(msg_content.content.video, 'minithumbnail') and msg_content.content.video.minithumbnail:
                            try:
                                thumb_data = msg_content.content.video.minithumbnail.data
                                content_data = base64.b64decode(thumb_data)
                                logging.info(f"Extracted video thumbnail data for message {msg_content.id}")
                            except Exception as e:
                                logging.error(f"Error extracting video thumbnail: {e}")
                
                elif msg_content.content.type == "messageDocument":
                    content_type = "document"
                    if hasattr(msg_content.content, 'caption') and msg_content.content.caption:
                        content = msg_content.content.caption.text
                    
                    # For documents, we could extract thumbnail if available
                    if hasattr(msg_content.content, 'document') and msg_content.content.document:
                        if hasattr(msg_content.content.document, 'minithumbnail') and msg_content.content.document.minithumbnail:
                            try:
                                thumb_data = msg_content.content.document.minithumbnail.data
                                content_data = base64.b64decode(thumb_data)
                                logging.info(f"Extracted document thumbnail data for message {msg_content.id}")
                            except Exception as e:
                                logging.error(f"Error extracting document thumbnail: {e}")
                
                # Create ChatMessage record
                message = ChatMessages(
                    MessageID=str(uuid.uuid4()),
                    SubmissionChatID=chat_id,
                    SourceMessageID=str(msg_content.id),
                    SenderID=sender_id,
                    MessageDate=datetime.fromtimestamp(msg_content.date),
                    ContentType=content_type,
                    Content=content,
                    ContentData=content_data  # Now saving the binary data
                )
                models.append(message)
        
        return models 