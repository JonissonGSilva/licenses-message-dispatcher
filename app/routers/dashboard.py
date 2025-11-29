"""Routes for dashboard statistics."""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from app.repositories.customer_repository import CustomerRepository
from app.repositories.company_repository import CompanyRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.team_repository import (
    DiretaRepository, IndicadorRepository, ParceiroRepository, NegocioRepository
)
from app.models.dashboard import (
    DashboardStatsResponse, DashboardSummaryResponse,
    LicenseStats, CompanyStats, MessageStats, TeamStats,
    UsersByCompany, MessagesByDate
)
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    start_date: Optional[str] = Query(None, description="Start date for messages filter (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date for messages filter (YYYY-MM-DD)")
):
    """
    Gets comprehensive dashboard statistics.
    
    Returns:
        Complete dashboard statistics including users, licenses, companies, messages, and teams.
    """
    try:
        # Get customer/license statistics
        total_customers = await CustomerRepository.count()
        start_customers = await CustomerRepository.count({"license_type": "Start", "active": True})
        hub_customers = await CustomerRepository.count({"license_type": "Hub", "active": True})
        
        license_stats = LicenseStats(
            start=start_customers,
            hub=hub_customers,
            total=total_customers
        )
        
        # Get company statistics
        total_companies = await CompanyRepository.count()
        active_companies = await CompanyRepository.count({"active": True})
        linked_companies = await CompanyRepository.count({"linked": True})
        start_companies = await CompanyRepository.count({"license_type": "Start"})
        hub_companies = await CompanyRepository.count({"license_type": "Hub"})
        
        company_stats = CompanyStats(
            total=total_companies,
            active=active_companies,
            linked=linked_companies,
            by_license_type={
                "Start": start_companies,
                "Hub": hub_companies
            }
        )
        
        # Get message statistics
        message_collection = MessageRepository.get_collection()
        
        # Build date filter for messages
        date_filter = {}
        if start_date or end_date:
            date_filter["created_at"] = {}
            if start_date:
                try:
                    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                    date_filter["created_at"]["$gte"] = start_dt
                except ValueError:
                    logger.warning(f"Invalid start_date format: {start_date}")
            if end_date:
                try:
                    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                    # Include the entire end date
                    end_dt = end_dt.replace(hour=23, minute=59, second=59)
                    date_filter["created_at"]["$lte"] = end_dt
                except ValueError:
                    logger.warning(f"Invalid end_date format: {end_date}")
        
        total_messages = await message_collection.count_documents(date_filter)
        sent_messages = await message_collection.count_documents({**date_filter, "status": "sent"})
        pending_messages = await message_collection.count_documents({**date_filter, "status": "pending"})
        failed_messages = await message_collection.count_documents({**date_filter, "status": "failed"})
        
        start_messages = await message_collection.count_documents({**date_filter, "license_type": "Start"})
        hub_messages = await message_collection.count_documents({**date_filter, "license_type": "Hub"})
        
        message_stats = MessageStats(
            total=total_messages,
            sent=sent_messages,
            pending=pending_messages,
            failed=failed_messages,
            by_license_type={
                "Start": start_messages,
                "Hub": hub_messages
            }
        )
        
        # Get team statistics
        direta_count = await DiretaRepository.count()
        indicador_count = await IndicadorRepository.count()
        parceiro_count = await ParceiroRepository.count()
        negocios_collection = NegocioRepository.get_collection()
        negocios_count = await negocios_collection.count_documents({})
        
        team_stats = TeamStats(
            direta=direta_count,
            indicador=indicador_count,
            parceiro=parceiro_count,
            negocios=negocios_count
        )
        
        # Get users by company
        customers_collection = CustomerRepository.get_collection()
        
        # Aggregate customers by company
        pipeline = [
            {
                "$match": {
                    "active": True,
                    "company": {"$exists": True, "$ne": None}
                }
            },
            {
                "$group": {
                    "_id": {
                        "company_name": {
                            "$cond": {
                                "if": {"$eq": [{"$type": "$company"}, "object"]},
                                "then": "$company.name",
                                "else": "$company"
                            }
                        },
                        "license_type": "$license_type"
                    },
                    "count": {"$sum": 1}
                }
            }
        ]
        
        users_by_company_raw = await customers_collection.aggregate(pipeline).to_list(length=None)
        
        # Process aggregation results
        company_users_map: Dict[str, Dict[str, int]] = {}
        for item in users_by_company_raw:
            company_name = item["_id"]["company_name"]
            license_type = item["_id"]["license_type"]
            count = item["count"]
            
            if company_name not in company_users_map:
                company_users_map[company_name] = {"Start": 0, "Hub": 0}
            
            company_users_map[company_name][license_type] = count
        
        users_by_company = [
            UsersByCompany(
                empresa=company_name,
                Start=data.get("Start", 0),
                Hub=data.get("Hub", 0),
                total=data.get("Start", 0) + data.get("Hub", 0)
            )
            for company_name, data in company_users_map.items()
        ]
        
        # Sort by total descending
        users_by_company.sort(key=lambda x: x.total, reverse=True)
        
        # Get messages by date
        messages_by_date: List[MessagesByDate] = []
        
        # Determine date range
        if start_date and end_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                # Default to last 30 days if invalid dates
                end_dt = datetime.utcnow()
                start_dt = end_dt - timedelta(days=30)
        else:
            # Default to last 30 days
            end_dt = datetime.utcnow()
            start_dt = end_dt - timedelta(days=30)
        
        # Aggregate messages by date
        messages_pipeline = [
            {
                "$match": {
                    "created_at": {
                        "$gte": start_dt,
                        "$lte": end_dt
                    }
                }
            },
            {
                "$group": {
                    "_id": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$created_at"
                        }
                    },
                    "total": {"$sum": 1},
                    "sent": {
                        "$sum": {"$cond": [{"$eq": ["$status", "sent"]}, 1, 0]}
                    },
                    "failed": {
                        "$sum": {"$cond": [{"$eq": ["$status", "failed"]}, 1, 0]}
                    }
                }
            },
            {
                "$sort": {"_id": 1}
            }
        ]
        
        messages_by_date_raw = await message_collection.aggregate(messages_pipeline).to_list(length=None)
        
        for item in messages_by_date_raw:
            date_str = item["_id"]
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                formatted_date = date_obj.strftime("%d/%m")
            except ValueError:
                formatted_date = date_str
            
            messages_by_date.append(
                MessagesByDate(
                    data=formatted_date,
                    notificacoes=item["total"],
                    mensagens=item["sent"],
                    sent=item["sent"],
                    failed=item["failed"]
                )
            )
        
        return DashboardStatsResponse(
            total_users=total_customers,
            license_stats=license_stats,
            company_stats=company_stats,
            message_stats=message_stats,
            team_stats=team_stats,
            users_by_company=users_by_company,
            messages_by_date=messages_by_date
        )
        
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {type(e).__name__}: {e}")
        logger.error(f"Error details:", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary", response_model=DashboardSummaryResponse)
async def get_dashboard_summary():
    """
    Gets a summary of key dashboard metrics.
    
    Returns:
        Summary with key metrics for quick display.
    """
    try:
        total_customers = await CustomerRepository.count()
        start_customers = await CustomerRepository.count({"license_type": "Start", "active": True})
        hub_customers = await CustomerRepository.count({"license_type": "Hub", "active": True})
        
        total_companies = await CompanyRepository.count()
        active_companies = await CompanyRepository.count({"active": True})
        
        message_collection = MessageRepository.get_collection()
        total_messages = await message_collection.count_documents({})
        sent_messages = await message_collection.count_documents({"status": "sent"})
        
        return DashboardSummaryResponse(
            total_users=total_customers,
            start_licenses=start_customers,
            hub_licenses=hub_customers,
            total_companies=total_companies,
            active_companies=active_companies,
            total_messages=total_messages,
            sent_messages=sent_messages
        )
        
    except Exception as e:
        logger.error(f"Error getting dashboard summary: {type(e).__name__}: {e}")
        logger.error(f"Error details:", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users-by-company", response_model=List[UsersByCompany])
async def get_users_by_company(
    limit: int = Query(10, ge=1, le=100, description="Maximum number of companies to return")
):
    """
    Gets users grouped by company.
    
    Returns:
        List of companies with their user counts by license type.
    """
    try:
        customers_collection = CustomerRepository.get_collection()
        
        pipeline = [
            {
                "$match": {
                    "active": True,
                    "company": {"$exists": True, "$ne": None}
                }
            },
            {
                "$group": {
                    "_id": {
                        "company_name": {
                            "$ifNull": [
                                {"$ifNull": ["$company.name", "$company"]},
                                "Sem Empresa"
                            ]
                        },
                        "license_type": "$license_type"
                    },
                    "count": {"$sum": 1}
                }
            },
            {
                "$group": {
                    "_id": "$_id.company_name",
                    "licenses": {
                        "$push": {
                            "type": "$_id.license_type",
                            "count": "$count"
                        }
                    }
                }
            },
            {
                "$project": {
                    "empresa": "$_id",
                    "Start": {
                        "$sum": {
                            "$map": {
                                "input": {
                                    "$filter": {
                                        "input": "$licenses",
                                        "as": "lic",
                                        "cond": {"$eq": ["$$lic.type", "Start"]}
                                    }
                                },
                                "as": "lic",
                                "in": "$$lic.count"
                            }
                        }
                    },
                    "Hub": {
                        "$sum": {
                            "$map": {
                                "input": {
                                    "$filter": {
                                        "input": "$licenses",
                                        "as": "lic",
                                        "cond": {"$eq": ["$$lic.type", "Hub"]}
                                    }
                                },
                                "as": "lic",
                                "in": "$$lic.count"
                            }
                        }
                    }
                }
            },
            {
                "$project": {
                    "empresa": 1,
                    "Start": {"$ifNull": ["$Start", 0]},
                    "Hub": {"$ifNull": ["$Hub", 0]},
                    "total": {"$add": [{"$ifNull": ["$Start", 0]}, {"$ifNull": ["$Hub", 0]}]}
                }
            },
            {
                "$sort": {"total": -1}
            },
            {
                "$limit": limit
            }
        ]
        
        results = await customers_collection.aggregate(pipeline).to_list(length=None)
        
        return [
            UsersByCompany(
                empresa=item["empresa"],
                Start=item["Start"],
                Hub=item["Hub"],
                total=item["total"]
            )
            for item in results
        ]
        
    except Exception as e:
        logger.error(f"Error getting users by company: {type(e).__name__}: {e}")
        logger.error(f"Error details:", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/messages-by-date", response_model=List[MessagesByDate])
async def get_messages_by_date(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    days: int = Query(30, ge=1, le=365, description="Number of days to look back (if dates not provided)")
):
    """
    Gets messages grouped by date.
    
    Returns:
        List of dates with message counts.
    """
    try:
        message_collection = MessageRepository.get_collection()
        
        # Determine date range
        if start_date and end_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                end_dt = end_dt.replace(hour=23, minute=59, second=59)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        else:
            end_dt = datetime.utcnow()
            start_dt = end_dt - timedelta(days=days)
        
        pipeline = [
            {
                "$match": {
                    "created_at": {
                        "$gte": start_dt,
                        "$lte": end_dt
                    }
                }
            },
            {
                "$group": {
                    "_id": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$created_at"
                        }
                    },
                    "total": {"$sum": 1},
                    "sent": {
                        "$sum": {"$cond": [{"$eq": ["$status", "sent"]}, 1, 0]}
                    },
                    "failed": {
                        "$sum": {"$cond": [{"$eq": ["$status", "failed"]}, 1, 0]}
                    }
                }
            },
            {
                "$sort": {"_id": 1}
            }
        ]
        
        results = await message_collection.aggregate(pipeline).to_list(length=None)
        
        messages_by_date = []
        for item in results:
            date_str = item["_id"]
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                formatted_date = date_obj.strftime("%d/%m")
            except ValueError:
                formatted_date = date_str
            
            messages_by_date.append(
                MessagesByDate(
                    data=formatted_date,
                    notificacoes=item["total"],
                    mensagens=item["sent"],
                    sent=item["sent"],
                    failed=item["failed"]
                )
            )
        
        return messages_by_date
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting messages by date: {type(e).__name__}: {e}")
        logger.error(f"Error details:", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

