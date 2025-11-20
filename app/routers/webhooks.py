"""Routes for webhooks."""
from fastapi import APIRouter, HTTPException, Request, Query
from typing import Optional, Dict
import logging
from app.models.license import WebhookLicenseCreated
from app.services.whatsapp_service import WhatsAppService
from app.services.segmentation_service import SegmentationService
from app.repositories.customer_repository import CustomerRepository
from app.repositories.license_repository import LicenseRepository
from app.repositories.message_repository import MessageRepository
from app.models.license import LicenseCreate
from app.models.customer import CustomerCreate
from app.models.message import MessageCreate
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/webhooks", tags=["Webhooks"])

whatsapp_service = WhatsAppService()


@router.get("/whatsapp")
async def verify_whatsapp_webhook(
    mode: str = Query(..., description="Verification mode"),
    token: str = Query(..., description="Verification token"),
    challenge: str = Query(..., description="Challenge string")
):
    """
    Endpoint for WhatsApp webhook verification.
    Used by Meta to validate webhook configuration.
    """
    challenge_response = await whatsapp_service.verify_webhook(mode, token, challenge)
    
    if challenge_response:
        return int(challenge_response)
    else:
        raise HTTPException(status_code=403, detail="Invalid verification token")


@router.post("/whatsapp")
async def receive_whatsapp_webhook(request: Request):
    """
    Endpoint to receive WhatsApp webhooks.
    Processes events like message status, received messages, etc.
    """
    try:
        data = await request.json()
        logger.info(f"Webhook received from WhatsApp: {data}")
        
        # Here you can process different types of events
        # For example: message status, received messages, etc.
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Error processing WhatsApp webhook: {type(e).__name__}: {e}")
        logger.error(f"Error details:", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/license-created", response_model=Dict)
async def receive_license_created_webhook(webhook_data: WebhookLicenseCreated):
    """
    Receives webhook from License Portal when a new license is created.
    
    Process:
    1. Finds or creates the customer in the database
    2. Creates the associated license
    3. Sends segmented welcome message via WhatsApp
    """
    try:
        logger.info(f"Processing license-created webhook: portal_id={webhook_data.portal_id}, license_type={webhook_data.license_type}")
        
        # 1. Find or create customer
        customer = None
        
        if webhook_data.customer_phone:
            customer = await CustomerRepository.find_by_phone(webhook_data.customer_phone)
            logger.debug(f"Customer search by phone: {webhook_data.customer_phone} - {'Found' if customer else 'Not found'}")
        
        if not customer and webhook_data.customer_email:
            customer = await CustomerRepository.find_by_email(webhook_data.customer_email)
            logger.debug(f"Customer search by email: {webhook_data.customer_email} - {'Found' if customer else 'Not found'}")
        
        # If not found, create a new customer
        if not customer:
            if not webhook_data.customer_phone:
                logger.error("Customer phone is required but not provided")
                raise HTTPException(
                    status_code=400,
                    detail="Customer phone is required to create a new customer"
                )
            
            customer_data = webhook_data.extra_data if webhook_data.extra_data else {}
            customer_create = CustomerCreate(
                name=customer_data.get("name", "Customer"),
                email=webhook_data.customer_email,
                phone=webhook_data.customer_phone,
                license_type=webhook_data.license_type,
                company=customer_data.get("company"),
                active=True
            )
            
            customer = await CustomerRepository.create(customer_create)
            logger.info(f"Customer created: ID={customer.id}, Name={customer.name}")
        else:
            # Updates license type if necessary
            if customer.license_type != webhook_data.license_type:
                from app.models.customer import CustomerUpdate
                customer_update = CustomerUpdate(license_type=webhook_data.license_type)
                customer = await CustomerRepository.update(str(customer.id), customer_update)
                logger.info(f"License type updated for customer {customer.id}")
        
        # 2. Create the license
        license_create = LicenseCreate(
            customer_id=customer.id,
            license_type=webhook_data.license_type,
            status="active",
            portal_id=webhook_data.portal_id
        )
        
        license = await LicenseRepository.create(license_create)
        logger.info(f"License created: ID={license.id}, Portal ID={license.portal_id}")
        
        # 3. Get segmented welcome message
        welcome_message = SegmentationService.get_welcome_message(webhook_data.license_type)
        
        # Personalize with customer data
        customer_data = {
            "name": customer.name,
            "company": customer.company
        }
        welcome_message = SegmentationService.personalize_message(welcome_message, customer_data)
        
        # 4. Create message record
        message_create = MessageCreate(
            customer_id=customer.id,
            phone=customer.phone,
            license_type=webhook_data.license_type,
            content=welcome_message,
            message_type="text",
            status="pending"
        )
        
        message = await MessageRepository.create(message_create)
        logger.debug(f"Message record created: ID={message.id}")
        
        # 5. Send message via WhatsApp
        send_result = await whatsapp_service.send_text_message(
            phone=customer.phone,
            message=welcome_message
        )
        
        # 6. Update message status
        from app.models.message import MessageUpdate
        message_update = MessageUpdate(
            status="sent" if send_result["success"] else "failed",
            whatsapp_message_id=send_result.get("message_id"),
            error=send_result.get("error")
        )
        
        await MessageRepository.update(str(message.id), message_update)
        
        if send_result["success"]:
            logger.info(f"Welcome message sent successfully to {customer.phone}")
            return {
                "success": True,
                "message": "License created and welcome message sent successfully",
                "customer_id": str(customer.id),
                "license_id": str(license.id),
                "message_id": str(message.id),
                "whatsapp_message_id": send_result.get("message_id")
            }
        else:
            logger.error(f"Error sending message: {send_result.get('error')}")
            return {
                "success": False,
                "message": "License created, but failed to send welcome message",
                "customer_id": str(customer.id),
                "license_id": str(license.id),
                "message_id": str(message.id),
                "error": send_result.get("error")
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing license-created webhook: {type(e).__name__}: {e}")
        logger.error(f"Error details:", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
