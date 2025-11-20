"""Service for message segmentation logic."""
from typing import Dict
import logging

logger = logging.getLogger(__name__)


class SegmentationService:
    """Service for segmenting messages by license type."""
    
    # Message templates by license type
    MESSAGE_TEMPLATES = {
        "Start": {
            "welcome": (
                "🎉 Welcome to *Start*!\n\n"
                "Your Start license has been successfully activated. "
                "You now have access to essential resources to get started.\n\n"
                "We're here to help you succeed! 🚀"
            ),
            "mass_message": (
                "Hello! 👋\n\n"
                "We have important news for you who use the *Start* plan.\n\n"
                "Stay tuned for updates and make the most of the available resources!"
            )
        },
        "Hub": {
            "welcome": (
                "🎉 Welcome to *Hub*!\n\n"
                "Your Hub license has been successfully activated. "
                "You now have access to all advanced features and priority support.\n\n"
                "Our team is ready to help you achieve your goals! 🚀"
            ),
            "mass_message": (
                "Hello! 👋\n\n"
                "We have exclusive news for you who use the *Hub* plan.\n\n"
                "Enjoy all premium features and our priority support!"
            )
        }
    }
    
    @classmethod
    def get_welcome_message(cls, license_type: str) -> str:
        """
        Returns the welcome message for the license type.
        
        Args:
            license_type: License type ('Start' or 'Hub')
            
        Returns:
            Personalized welcome message
        """
        if license_type not in cls.MESSAGE_TEMPLATES:
            logger.warning(f"Unknown license type: {license_type}. Using default template.")
            license_type = "Start"
        
        return cls.MESSAGE_TEMPLATES[license_type]["welcome"]
    
    @classmethod
    def get_mass_message(cls, license_type: str) -> str:
        """
        Returns the mass message for the license type.
        
        Args:
            license_type: License type ('Start' or 'Hub')
            
        Returns:
            Personalized mass message
        """
        if license_type not in cls.MESSAGE_TEMPLATES:
            logger.warning(f"Unknown license type: {license_type}. Using default template.")
            license_type = "Start"
        
        return cls.MESSAGE_TEMPLATES[license_type]["mass_message"]
    
    @classmethod
    def personalize_message(cls, template: str, customer_data: Dict = None) -> str:
        """
        Personalizes a message template with customer data.
        
        Args:
            template: Message template
            customer_data: Dictionary with customer data (name, company, etc.)
            
        Returns:
            Personalized message
        """
        if not customer_data:
            return template
        
        message = template
        
        # Replaces common variables
        if "name" in customer_data:
            message = message.replace("{name}", customer_data["name"])
        
        if "company" in customer_data:
            message = message.replace("{company}", customer_data["company"])
        
        return message

