"""Routes for CSV import."""
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from typing import Dict, Optional
import logging
from io import BytesIO
from app.services.csv_service import CSVService
from app.repositories.customer_repository import CustomerRepository
from app.models.customer import CustomerResponse
from app.models.csv_validation import CSVValidationResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/csv", tags=["CSV"])


@router.post("/upload", response_model=Dict)
async def upload_csv(
    file: UploadFile = File(...),
    skip_invalid: bool = Query(True, description="If True, only valid rows are saved. If False, returns error if any row is invalid"),
    return_invalid_details: bool = Query(True, description="If True, returns detailed information about invalid rows"),
    skip_duplicates: bool = Query(True, description="If True, skips duplicate customers (by phone or email). If False, returns error if duplicates found")
):
    """
    Uploads and processes a CSV file with customer data.
    
    The CSV must contain the following columns (required):
    - name/nome: Customer name
    - phone/telefone: Phone with area code and country code
    - license_type/tipo_licenca: 'Start' or 'Hub'
    
    Optional columns:
    - email: Customer email
    - company/empresa: Company name
    
    **Note:** Column names can be in Portuguese or English. The system accepts only standard terms:
    - nome/name
    - email
    - telefone/phone
    - tipo_licenca/license_type
    - empresa/company
    
    Query Parameters:
    - skip_invalid: If True (default), only valid rows are saved. If False, returns error if any row is invalid.
    - return_invalid_details: If True (default), returns detailed information about invalid rows.
    - skip_duplicates: If True (default), skips duplicate customers (by phone or email). If False, returns error if duplicates found.
    
    Returns processing statistics, list of created customers, validation details, and duplicate information.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    try:
        logger.info(f"Starting CSV upload: {file.filename} (size: {file.size if hasattr(file, 'size') else 'unknown'})")
        
        # Reads file content
        content = await file.read()
        logger.debug(f"File read: {len(content)} bytes")
        
        file_bytes = BytesIO(content)
        
        # Processes CSV
        logger.info("Processing CSV file...")
        result = await CSVService.process_csv(file_bytes)
        validation: CSVValidationResult = result.get("validation")
        
        logger.info(f"CSV processed: {result['success']} valid customers, {validation.invalid_rows} invalid rows")
        
        # If skip_invalid is False and there are invalid rows, return error
        if not skip_invalid and validation.has_errors:
            logger.warning(f"CSV has invalid rows and skip_invalid=False. Returning error.")
            return {
                "success": False,
                "message": "CSV contains invalid rows. Use skip_invalid=true to save only valid rows.",
                "validation": validation.model_dump() if return_invalid_details else None,
                "total_rows": result["total_rows"],
                "valid_rows": validation.valid_rows,
                "invalid_rows": validation.invalid_rows
            }
        
        # If no valid customers, return error
        if not result["customers"]:
            logger.warning(f"No valid customers found. Total errors: {validation.invalid_rows}")
            return {
                "success": False,
                "message": "No valid customers found in CSV",
                "validation": validation.model_dump() if return_invalid_details else None,
                "total_rows": result["total_rows"],
                "valid_rows": 0,
                "invalid_rows": validation.invalid_rows
            }
        
        # Check for duplicates
        logger.info(f"Checking for duplicates among {len(result['customers'])} customers...")
        duplicates = await CustomerRepository.check_duplicates(result["customers"])
        
        # Filter out duplicates
        customers_to_create = []
        duplicate_details = []
        
        for customer in result["customers"]:
            is_duplicate = False
            duplicate_reason = None
            existing_customer = None
            
            # Check by phone
            if customer.phone in duplicates:
                is_duplicate = True
                existing_customer = duplicates[customer.phone]
                duplicate_reason = f"Phone {customer.phone} already exists"
            
            # Check by email (if email provided and not already found by phone)
            elif customer.email and customer.email.strip() and customer.email in duplicates:
                is_duplicate = True
                existing_customer = duplicates[customer.email]
                duplicate_reason = f"Email {customer.email} already exists"
            
            if is_duplicate:
                duplicate_details.append({
                    "customer": {
                        "name": customer.name,
                        "phone": customer.phone,
                        "email": customer.email,
                        "license_type": customer.license_type
                    },
                    "reason": duplicate_reason,
                    "existing_customer_id": str(existing_customer.id) if existing_customer else None,
                    "existing_customer_name": existing_customer.name if existing_customer else None
                })
                logger.debug(f"Duplicate customer skipped: {customer.name} ({customer.phone}) - {duplicate_reason}")
            else:
                customers_to_create.append(customer)
        
        # If skip_duplicates is False and there are duplicates, return error
        if not skip_duplicates and duplicates:
            logger.warning(f"CSV has duplicate customers and skip_duplicates=False. Returning error.")
            return {
                "success": False,
                "message": f"CSV contains {len(duplicates)} duplicate customer(s). Use skip_duplicates=true to skip duplicates.",
                "duplicates": duplicate_details,
                "total_rows": result["total_rows"],
                "valid_rows": validation.valid_rows,
                "duplicate_count": len(duplicates)
            }
        
        # If no customers to create after filtering duplicates
        if not customers_to_create:
            logger.warning(f"All customers are duplicates. Total duplicates: {len(duplicates)}")
            return {
                "success": False,
                "message": "All customers in CSV are duplicates",
                "duplicates": duplicate_details if return_invalid_details else None,
                "duplicate_count": len(duplicates),
                "total_rows": result["total_rows"]
            }
        
        # Creates customers in database (only non-duplicates)
        logger.info(f"Creating {len(customers_to_create)} new customers in database (skipping {len(duplicates)} duplicate(s))...")
        try:
            customers_created = await CustomerRepository.create_many(customers_to_create)
            logger.info(f"Customers created successfully: {len(customers_created)}")
        except Exception as db_error:
            logger.error(f"Error creating customers in database: {type(db_error).__name__}: {db_error}")
            logger.error(f"Error details: {str(db_error)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Error saving customers to database: {str(db_error)}"
            )
        
        # Converts to response
        logger.debug("Converting customers to response format...")
        customers_response = []
        for c in customers_created:
            try:
                customer_resp = CustomerResponse(
                    id=str(c.id),
                    name=c.name,
                    email=c.email,
                    phone=c.phone,
                    license_type=c.license_type,
                    company=c.company,
                    active=c.active,
                    created_at=c.created_at,
                    updated_at=c.updated_at
                )
                customers_response.append(customer_resp)
            except Exception as conv_error:
                logger.error(f"Error converting customer to response: {type(conv_error).__name__}: {conv_error}")
                logger.error(f"Problematic customer - ID: {c.id if hasattr(c, 'id') else 'N/A'}, Name: {c.name if hasattr(c, 'name') else 'N/A'}")
                raise
        
        logger.info(f"CSV upload completed successfully: {len(customers_created)} customers created")
        
        # Build message
        message_parts = [f"Successfully created {len(customers_created)} customers"]
        if validation.has_errors:
            message_parts.append(f"{validation.invalid_rows} rows were invalid and skipped")
        if duplicates:
            message_parts.append(f"{len(duplicates)} duplicate(s) were skipped")
        
        response = {
            "success": True,
            "message": ". ".join(message_parts) + ".",
            "total_rows": result["total_rows"],
            "customers_created": len(customers_created),
            "customers": customers_response
        }
        
        # Adds validation details if requested
        if return_invalid_details:
            response["validation"] = validation.model_dump()
        else:
            # Still include basic error count
            response["errors_count"] = len(result["errors"])
            if validation.has_errors:
                response["errors_summary"] = f"{validation.invalid_rows} rows had validation errors"
        
        # Adds duplicate details if there are any
        if duplicates:
            response["duplicate_count"] = len(duplicates)
            if return_invalid_details:
                response["duplicates"] = duplicate_details
            else:
                response["duplicates_summary"] = f"{len(duplicates)} customer(s) were duplicates and skipped"
        
        return response
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error processing CSV: {type(e).__name__}: {e}")
        logger.error(f"Details: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Error processing CSV: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error processing CSV: {type(e).__name__}: {e}")
        logger.error(f"Complete error details:", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal error processing CSV: {str(e)}"
        )


@router.post("/validate", response_model=Dict)
async def validate_csv(
    file: UploadFile = File(...),
    return_invalid_details: bool = Query(True, description="If True, returns detailed information about invalid rows")
):
    """
    Validates a CSV file without saving to database.
    
    This endpoint only validates the CSV structure and data, but does not create any customers.
    Useful for checking CSV validity before actual import.
    
    **Note:** Column names can be in Portuguese or English. The system automatically normalizes them.
    
    Returns validation results including detailed information about invalid rows.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    try:
        logger.info(f"Validating CSV file: {file.filename}")
        
        # Reads file content
        content = await file.read()
        file_bytes = BytesIO(content)
        
        # Processes CSV (validation only, no database save)
        result = await CSVService.process_csv(file_bytes)
        validation: CSVValidationResult = result.get("validation")
        
        logger.info(f"CSV validation completed: {validation.valid_rows} valid rows, {validation.invalid_rows} invalid rows")
        
        response = {
            "valid": not validation.has_errors,
            "total_rows": validation.total_rows,
            "valid_rows": validation.valid_rows,
            "invalid_rows": validation.invalid_rows,
            "message": (
                f"CSV is valid. {validation.valid_rows} rows are ready to import." 
                if not validation.has_errors 
                else f"CSV has {validation.invalid_rows} invalid rows out of {validation.total_rows} total rows."
            )
        }
        
        if return_invalid_details:
            response["validation"] = validation.model_dump()
        
        return response
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error processing CSV: {type(e).__name__}: {e}")
        logger.error(f"Details: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Error processing CSV: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error processing CSV: {type(e).__name__}: {e}")
        logger.error(f"Complete error details:", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal error processing CSV: {str(e)}"
        )
