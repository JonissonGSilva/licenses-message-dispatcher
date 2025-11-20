"""Serviço para integração com WhatsApp Cloud API."""
import httpx
import logging
from typing import Dict, Optional
from app.config import settings

logger = logging.getLogger(__name__)


class WhatsAppService:
    """Serviço para envio de mensagens via WhatsApp Cloud API."""
    
    def __init__(self):
        self.api_url = settings.whatsapp_api_url
        self.phone_number_id = settings.whatsapp_phone_number_id
        self.access_token = settings.whatsapp_access_token
        self.base_url = f"{self.api_url}/{self.phone_number_id}"
    
    async def send_text_message(
        self,
        phone: str,
        message: str
    ) -> Dict:
        """
        Sends a text message via WhatsApp Cloud API.
        
        Args:
            phone: Recipient phone number (international format)
            message: Message content
            
        Returns:
            Dict with 'success', 'message_id' and 'error' (if any)
        """
        url = f"{self.base_url}/messages"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        # Formats phone (removes non-numeric characters)
        formatted_phone = ''.join(filter(str.isdigit, phone))
        
        payload = {
            "messaging_product": "whatsapp",
            "to": formatted_phone,
            "type": "text",
            "text": {
                "body": message
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                message_id = data.get("messages", [{}])[0].get("id")
                
                logger.info(f"Message sent successfully to {formatted_phone}. Message ID: {message_id}")
                
                return {
                    "success": True,
                    "message_id": message_id,
                    "error": None
                }
                
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error {e.response.status_code}: {e.response.text}"
            logger.error(f"Error sending message to {formatted_phone}: {error_msg}")
            
            return {
                "success": False,
                "message_id": None,
                "error": error_msg
            }
            
        except httpx.RequestError as e:
            error_msg = f"Connection error: {str(e)}"
            logger.error(f"Connection error sending message: {error_msg}")
            
            return {
                "success": False,
                "message_id": None,
                "error": error_msg
            }
    
    async def send_hsm(
        self,
        phone: str,
        template_name: str,
        parameters: Optional[list] = None,
        language: str = "pt_BR"
    ) -> Dict:
        """
        Sends an HSM (Template Message) via WhatsApp Cloud API.
        
        Args:
            phone: Recipient phone number
            template_name: Name of the approved template in Meta
            parameters: List of parameters for the template
            language: Language code (default: pt_BR)
            
        Returns:
            Dict with 'success', 'message_id' and 'error' (if any)
        """
        url = f"{self.base_url}/messages"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        formatted_phone = ''.join(filter(str.isdigit, phone))
        
        template_data = {
            "name": template_name,
            "language": {
                "code": language
            }
        }
        
        if parameters:
            template_data["components"] = [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": str(param)} for param in parameters
                    ]
                }
            ]
        
        payload = {
            "messaging_product": "whatsapp",
            "to": formatted_phone,
            "type": "template",
            "template": template_data
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                message_id = data.get("messages", [{}])[0].get("id")
                
                logger.info(f"HSM sent successfully to {formatted_phone}. Message ID: {message_id}")
                
                return {
                    "success": True,
                    "message_id": message_id,
                    "error": None
                }
                
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error {e.response.status_code}: {e.response.text}"
            logger.error(f"Error sending HSM to {formatted_phone}: {error_msg}")
            
            return {
                "success": False,
                "message_id": None,
                "error": error_msg
            }
            
        except httpx.RequestError as e:
            error_msg = f"Connection error: {str(e)}"
            logger.error(f"Connection error sending HSM: {error_msg}")
            
            return {
                "success": False,
                "message_id": None,
                "error": error_msg
            }
    
    async def verify_webhook(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """
        Verifies the WhatsApp webhook (used in initial setup).
        
        Args:
            mode: Verification mode
            token: Verification token
            challenge: Challenge string
            
        Returns:
            Challenge string if verification is successful, None otherwise
        """
        if mode == "subscribe" and token == settings.whatsapp_verify_token:
            return challenge
        return None

