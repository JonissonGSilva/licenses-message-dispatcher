"""Repositories for database access."""
from app.repositories.customer_repository import CustomerRepository
from app.repositories.license_repository import LicenseRepository
from app.repositories.message_repository import MessageRepository

__all__ = ["CustomerRepository", "LicenseRepository", "MessageRepository"]
