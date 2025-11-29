"""Dashboard models."""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class LicenseStats(BaseModel):
    """License statistics."""
    start: int = Field(..., description="Total Start licenses")
    hub: int = Field(..., description="Total Hub licenses")
    total: int = Field(..., description="Total licenses")


class CompanyStats(BaseModel):
    """Company statistics."""
    total: int = Field(..., description="Total companies")
    active: int = Field(..., description="Active companies")
    linked: int = Field(..., description="Linked companies")
    by_license_type: Dict[str, int] = Field(..., description="Companies by license type")


class MessageStats(BaseModel):
    """Message statistics."""
    total: int = Field(..., description="Total messages")
    sent: int = Field(..., description="Sent messages")
    pending: int = Field(..., description="Pending messages")
    failed: int = Field(..., description="Failed messages")
    by_license_type: Dict[str, int] = Field(..., description="Messages by license type")


class UsersByCompany(BaseModel):
    """Users count by company."""
    empresa: str = Field(..., description="Company name")
    Start: int = Field(..., description="Start licenses count")
    Hub: int = Field(..., description="Hub licenses count")
    total: int = Field(..., description="Total licenses count")


class MessagesByDate(BaseModel):
    """Messages count by date."""
    data: str = Field(..., description="Date in format DD/MM")
    notificacoes: int = Field(..., description="Total notifications/messages")
    mensagens: int = Field(..., description="Messages sent")
    sent: int = Field(..., description="Sent messages")
    failed: int = Field(..., description="Failed messages")


class TeamStats(BaseModel):
    """Team statistics."""
    direta: int = Field(..., description="Total Direta members")
    indicador: int = Field(..., description="Total Indicadores")
    parceiro: int = Field(..., description="Total Parceiros")
    negocios: int = Field(..., description="Total Negocios")


class DashboardStatsResponse(BaseModel):
    """Complete dashboard statistics response."""
    total_users: int = Field(..., description="Total users/customers")
    license_stats: LicenseStats = Field(..., description="License statistics")
    company_stats: CompanyStats = Field(..., description="Company statistics")
    message_stats: MessageStats = Field(..., description="Message statistics")
    team_stats: TeamStats = Field(..., description="Team statistics")
    users_by_company: List[UsersByCompany] = Field(..., description="Users grouped by company")
    messages_by_date: List[MessagesByDate] = Field(..., description="Messages grouped by date")


class DashboardSummaryResponse(BaseModel):
    """Summary dashboard response with key metrics."""
    total_users: int
    start_licenses: int
    hub_licenses: int
    total_companies: int
    active_companies: int
    total_messages: int
    sent_messages: int

