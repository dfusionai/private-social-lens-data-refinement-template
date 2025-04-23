from typing import Dict, Any, List
from refiner.models.refined import Base
from refiner.transformer.base_transformer import DataTransformer
from refiner.models.refined import UserRefined, AuthSource
from refiner.models.refined import TelegramAccount, TelegramChat, TelegramMessage, TelegramMedia, TelegramForward
from refiner.models.unrefined import User
from refiner.utils.date import parse_timestamp
from refiner.utils.pii import mask_email, mask_phone

class UserTransformer(DataTransformer):
    """
    Transformer for user data as defined in the example.
    """
    
    def transform(self, data: Dict[str, Any]) -> List[Base]:
        """
        Transform raw user data into SQLAlchemy model instances.
        
        Args:
            data: Dictionary containing user data
            
        Returns:
            List of SQLAlchemy model instances
        """
        # Validate data with Pydantic
        unrefined_user = User.model_validate(data)
        created_at = parse_timestamp(unrefined_user.timestamp)
        
        # Create user instance
        user = UserRefined(
            user_id=unrefined_user.userId,
            email=mask_email(unrefined_user.email),  # Apply any PII masking (optional)
            name=unrefined_user.profile.name,
            locale=unrefined_user.profile.locale,
            created_at=created_at
        )
        
        models = [user]
        
        if unrefined_user.metadata:
            collection_date = parse_timestamp(unrefined_user.metadata.collectionDate)
            auth_source = AuthSource(
                user_id=unrefined_user.userId,
                source=unrefined_user.metadata.source,
                collection_date=collection_date,
                data_type=unrefined_user.metadata.dataType
            )
            models.append(auth_source)
        
        # Process Telegram data if available
        if unrefined_user.telegramData:
            telegram_data = unrefined_user.telegramData
            
            # Create Telegram account
            account = TelegramAccount(
                user_id=unrefined_user.userId,
                username=telegram_data.username,
                phone_masked=mask_phone(telegram_data.phoneNumber),  # Apply PII masking
                is_bot=telegram_data.isBot,
                is_premium=telegram_data.isPremium,
                join_date=parse_timestamp(telegram_data.joinDate)
            )
            models.append(account)
            
            # Create Telegram chats
            for chat_data in telegram_data.chats:
                chat = TelegramChat(
                    chat_id=chat_data.chatId,
                    account_id=account.account_id,  # This will be populated after DB insertion
                    type=chat_data.type,
                    title=chat_data.title,
                    username=chat_data.username,
                    member_count=chat_data.memberCount,
                    subscriber_count=chat_data.subscriberCount,
                    message_count=chat_data.messageCount,
                    last_activity=parse_timestamp(chat_data.lastActivity)
                )
                models.append(chat)
            
            # Create Telegram messages
            for msg_data in telegram_data.messages:
                msg = TelegramMessage(
                    message_id=msg_data.messageId,
                    chat_id=msg_data.chatId,
                    account_id=account.account_id,  # This will be populated after DB insertion
                    timestamp=parse_timestamp(msg_data.timestamp),
                    text=msg_data.text,
                    is_outgoing=msg_data.isOutgoing,
                    reply_to_message_id=msg_data.replyToMessageId,
                    has_media=msg_data.hasMedia
                )
                models.append(msg)
                
                # Add media info if available
                if msg_data.hasMedia and msg_data.media:
                    media = TelegramMedia(
                        message_id=msg.message_id,
                        media_type=msg_data.media.type,
                        caption=msg_data.media.caption,
                        file_size=msg_data.media.fileSize
                    )
                    models.append(media)
                
                # Add forward info if available
                if msg_data.forwardInfo:
                    forward = TelegramForward(
                        message_id=msg.message_id,
                        original_sender=msg_data.forwardInfo.originalSender,
                        original_date=parse_timestamp(msg_data.forwardInfo.originalDate)
                    )
                    models.append(forward)
        
        return models