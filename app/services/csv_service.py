"""Service for CSV file processing."""
import pandas as pd
import logging
from typing import List, Dict, Optional, Any
from io import BytesIO
from app.models.customer import CustomerCreate
from app.models.csv_validation import InvalidRowDetail, CSVValidationResult

logger = logging.getLogger(__name__)


class CSVService:
    """Service for importing and processing CSV files."""
    
    # Expected columns in CSV - Only Portuguese and English standard terms
    EXPECTED_COLUMNS = {
        "name": ["nome", "name"],
        "email": ["email"],
        "phone": ["telefone", "phone"],
        "license_type": ["tipo_licenca", "license_type"],
        "company": ["empresa", "company"]
    }
    
    @classmethod
    def normalize_columns(cls, df: pd.DataFrame) -> pd.DataFrame:
        """Normalizes DataFrame column names."""
        df = df.copy()
        df.columns = df.columns.str.lower().str.strip()
        
        # Maps columns to standard names
        mapping = {}
        for standard_col, variations in cls.EXPECTED_COLUMNS.items():
            for col in df.columns:
                if col in variations:
                    mapping[col] = standard_col
                    break
        
        df.rename(columns=mapping, inplace=True)
        return df
    
    @classmethod
    def validate_phone(cls, phone: str) -> Optional[str]:
        """Validates and normalizes phone number."""
        if pd.isna(phone):
            return None
        
        phone = str(phone).strip()
        # Remove non-numeric characters
        phone = ''.join(filter(str.isdigit, phone))
        
        # Basic validation: must have at least 10 digits
        if len(phone) < 10:
            return None
        
        # Adds country code if not present (assumes Brazil +55)
        if not phone.startswith('55') and len(phone) == 10 or len(phone) == 11:
            phone = '55' + phone
        
        return phone
    
    @classmethod
    def validate_license_type(cls, license_type: str) -> Optional[str]:
        """Validates and normalizes license type."""
        if pd.isna(license_type):
            return None
        
        license_type = str(license_type).strip().capitalize()
        
        # Normalizes common variations
        type_map = {
            "Start": "Start",
            "Hub": "Hub",
            "S": "Start",
            "H": "Hub",
            "Starter": "Start",
            "Basic": "Start"
        }
        
        return type_map.get(license_type, license_type if license_type in ["Start", "Hub"] else None)
    
    @classmethod
    async def process_csv(cls, file: BytesIO) -> Dict:
        """
        Processes a CSV file and returns list of validated customers.
        
        Args:
            file: BytesIO of the CSV file
            
        Returns:
            Dict with 'customers' (list of CustomerCreate) and 'errors' (list of errors)
        """
        try:
            logger.info("Starting CSV file reading...")
            # Reads CSV
            df = pd.read_csv(file, encoding='utf-8')
            logger.info(f"CSV read successfully: {len(df)} rows found")
            
            # Normalizes columns
            logger.debug("Normalizing column names...")
            df = cls.normalize_columns(df)
            logger.debug(f"Columns after normalization: {list(df.columns)}")
            
            # Validates required columns
            required_columns = ["name", "phone", "license_type"]
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                logger.error(f"Required columns missing: {missing_columns}")
                logger.error(f"Available columns in CSV: {list(df.columns)}")
                raise ValueError(f"Required columns missing: {', '.join(missing_columns)}. Available columns: {', '.join(df.columns)}")
            
            customers = []
            errors = []
            invalid_rows_details: List[InvalidRowDetail] = []
            
            logger.info(f"Processing {len(df)} CSV rows...")
            for index, row in df.iterrows():
                row_number = index + 2  # +2 because index is 0-based and we skip header
                row_errors: List[str] = []
                raw_row_data = {col: str(row.get(col, "")) if pd.notna(row.get(col)) else "" for col in df.columns}
                
                try:
                    # Validates and normalizes phone
                    phone_raw = row.get("phone")
                    phone = cls.validate_phone(phone_raw)
                    if not phone:
                        error_msg = f"Invalid or missing phone (value: '{phone_raw}')"
                        row_errors.append(error_msg)
                        logger.warning(f"Row {row_number}: {error_msg}")
                    
                    # Validates and normalizes license type
                    license_type_raw = row.get("license_type")
                    license_type = cls.validate_license_type(license_type_raw)
                    if not license_type:
                        error_msg = f"Invalid license type (value: '{license_type_raw}', must be 'Start' or 'Hub')"
                        row_errors.append(error_msg)
                        logger.warning(f"Row {row_number}: {error_msg}")
                    
                    # Validates name
                    name = str(row.get("name", "")).strip()
                    if not name:
                        error_msg = "Name cannot be empty"
                        row_errors.append(error_msg)
                        logger.warning(f"Row {row_number}: {error_msg}")
                    
                    # If there are errors, add to invalid rows and continue
                    if row_errors:
                        invalid_rows_details.append(InvalidRowDetail(
                            row_number=row_number,
                            raw_data=raw_row_data,
                            errors=row_errors
                        ))
                        errors.extend([f"Row {row_number}: {err}" for err in row_errors])
                        continue
                    
                    # Creates CustomerCreate object
                    customer = CustomerCreate(
                        name=name,
                        email=str(row.get("email", "")).strip() if pd.notna(row.get("email")) else None,
                        phone=phone,
                        license_type=license_type,
                        company=str(row.get("company", "")).strip() if pd.notna(row.get("company")) else None,
                        active=True
                    )
                    
                    customers.append(customer)
                    logger.debug(f"Row {row_number} processed successfully: {name} ({license_type})")
                    
                except Exception as e:
                    error_msg = f"Unexpected error: {str(e)}"
                    row_errors.append(error_msg)
                    invalid_rows_details.append(InvalidRowDetail(
                        row_number=row_number,
                        raw_data=raw_row_data,
                        errors=row_errors
                    ))
                    errors.append(f"Row {row_number}: {error_msg}")
                    logger.error(f"Error processing row {row_number}: {type(e).__name__}: {e}")
                    logger.error(f"Problematic row data: {raw_row_data}", exc_info=True)
            
            logger.info(f"Processing completed: {len(customers)} valid customers, {len(invalid_rows_details)} invalid rows")
            
            # Creates validation result
            validation_result = CSVValidationResult(
                total_rows=len(df),
                valid_rows=len(customers),
                invalid_rows=len(invalid_rows_details),
                invalid_rows_details=invalid_rows_details,
                has_errors=len(invalid_rows_details) > 0
            )
            
            return {
                "customers": customers,
                "errors": errors,
                "validation": validation_result,
                "total_rows": len(df),
                "success": len(customers),
                "failures": len(invalid_rows_details)
            }
            
        except pd.errors.EmptyDataError:
            logger.error("CSV file is empty")
            raise ValueError("CSV file is empty")
        except pd.errors.ParserError as e:
            logger.error(f"CSV parsing error: {type(e).__name__}: {e}")
            logger.error(f"Details: {str(e)}", exc_info=True)
            raise ValueError(f"Error processing CSV (invalid format): {str(e)}")
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error processing CSV: {type(e).__name__}: {e}")
            logger.error(f"Complete details:", exc_info=True)
            raise ValueError(f"Error processing CSV file: {str(e)}")

