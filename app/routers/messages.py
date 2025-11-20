"""Routes for message management."""
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import List, Optional, Dict
import logging
from app.repositories.message_repository import MessageRepository
from app.repositories.customer_repository import CustomerRepository
from app.models.message import MessageResponse, MessageCreate, MessageUpdate
from app.services.whatsapp_service import WhatsAppService
from app.services.segmentation_service import SegmentationService
from bson.errors import InvalidId

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/messages", tags=["Messages"])

whatsapp_service = WhatsAppService()


@router.post("/send-mass", response_model=Dict)
async def send_mass_message(
    license_type: str = Query(..., pattern="^(Start|Hub)$", description="License type for segmentation"),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Sends mass messages to all customers of a license type.
    
    Process:
    1. Finds all active customers of the specified license type
    2. Creates message records
    3. Sends messages via WhatsApp (background processing)
    """
    try:
        # 1. Find customers by license type
        customers = await CustomerRepository.list_by_license_type(license_type, active=True)
        
        if not customers:
            return {
                "success": False,
                "message": f"No active customers found for license type '{license_type}'",
                "total": 0,
                "sent": 0
            }
        
        # 2. Get segmented message
        message_template = SegmentationService.get_mass_message(license_type)
        
        # 3. Create message records
        messages_create = []
        for customer in customers:
            personalized_message = SegmentationService.personalize_message(
                message_template,
                {"name": customer.name, "company": customer.company}
            )
            
            message_create = MessageCreate(
                customer_id=customer.id,
                phone=customer.phone,
                license_type=license_type,
                content=personalized_message,
                message_type="text",
                status="pending"
            )
            messages_create.append(message_create)
        
        # 4. Save messages to database
        messages = await MessageRepository.create_many(messages_create)
        
        # 5. Schedule background sending
        background_tasks.add_task(process_message_sending, [str(m.id) for m in messages])
        
        return {
            "success": True,
            "message": f"Sending {len(messages)} messages started in background",
            "total": len(messages),
            "license_type": license_type
        }
        
    except Exception as e:
        logger.error(f"Error sending mass message: {type(e).__name__}: {e}")
        logger.error(f"Error details:", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def process_message_sending(message_ids: List[str]):
    """Processes message sending in background."""
    for message_id in message_ids:
        try:
            message = await MessageRepository.find_by_id(message_id)
            if not message:
                continue
            
            # Send message
            result = await whatsapp_service.send_text_message(
                phone=message.phone,
                message=message.content
            )
            
            # Update status
            message_update = MessageUpdate(
                status="sent" if result["success"] else "failed",
                whatsapp_message_id=result.get("message_id"),
                error=result.get("error")
            )
            
            await MessageRepository.update(message_id, message_update)
            
        except Exception as e:
            logger.error(f"Error processing message {message_id}: {type(e).__name__}: {e}")
            logger.error(f"Error details:", exc_info=True)


@router.get("", response_model=List[MessageResponse])
async def list_messages(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None, pattern="^(pending|sent|failed)$"),
    customer_id: Optional[str] = Query(None)
):
    """Lists messages with optional filters."""
    try:
        if status:
            messages = await MessageRepository.list_by_status(status, skip=skip, limit=limit)
        elif customer_id:
            messages = await MessageRepository.list_by_customer(customer_id, skip=skip, limit=limit)
        else:
            messages = await MessageRepository.list_all(skip=skip, limit=limit)
        
        return [
            MessageResponse(
                id=str(m.id),
                customer_id=str(m.customer_id) if m.customer_id else None,
                phone=m.phone,
                license_type=m.license_type,
                content=m.content,
                message_type=m.message_type,
                status=m.status,
                whatsapp_message_id=m.whatsapp_message_id,
                error=m.error,
                created_at=m.created_at,
                updated_at=m.updated_at
            )
            for m in messages
        ]
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ID")
    except Exception as e:
        logger.error(f"Error listing messages: {type(e).__name__}: {e}")
        logger.error(f"Error details:", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{message_id}", response_model=MessageResponse)
async def get_message(message_id: str):
    """Gets a message by ID."""
    try:
        message = await MessageRepository.find_by_id(message_id)
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        
        return MessageResponse(
            id=str(message.id),
            customer_id=str(message.customer_id) if message.customer_id else None,
            phone=message.phone,
            license_type=message.license_type,
            content=message.content,
            message_type=message.message_type,
            status=message.status,
            whatsapp_message_id=message.whatsapp_message_id,
            error=message.error,
            created_at=message.created_at,
            updated_at=message.updated_at
        )
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ID")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting message: {type(e).__name__}: {e}")
        logger.error(f"Error details:", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

