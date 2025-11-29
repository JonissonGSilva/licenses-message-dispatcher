"""Service for Company CSV file processing."""
import pandas as pd
import logging
from typing import List, Dict, Optional, Any
from io import BytesIO
from datetime import datetime
from app.models.company import CompanyCreate
from app.models.csv_validation import InvalidRowDetail, CSVValidationResult

logger = logging.getLogger(__name__)


class CompanyCSVService:
    """Service for importing and processing Company CSV files."""
    
    # Expected columns in CSV - Only Portuguese and English standard terms
    EXPECTED_COLUMNS = {
        "name": ["nome", "name"],
        "cnpj": ["cnpj"],
        "email": ["email"],
        "phone": ["telefone", "phone"],
        "address": ["endereco", "address"],
        "city": ["cidade", "city"],
        "state": ["estado", "state"],
        "zip_code": ["cep", "zip_code", "zipcode"],
        "linked": ["vinculada", "linked"],
        "active": ["ativa", "active"],
        "license_timeout": ["timeout_licenca", "license_timeout", "timeout"],
        "contract_expiration": ["expiracao_contrato", "contract_expiration", "expiration"],
        "employee_count": ["quantidade_funcionarios", "employee_count", "employees"],
        "license_type": ["tipo_licenca", "license_type"],
        "portal_id": ["portal_id", "portal"],
        "notes": ["notas", "notes"]
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
        if not phone.startswith('55') and (len(phone) == 10 or len(phone) == 11):
            phone = '55' + phone
        
        return phone
    
    @classmethod
    def validate_cnpj(cls, cnpj: str) -> Optional[str]:
        """Validates and normalizes CNPJ by removing formatting."""
        if pd.isna(cnpj):
            return None
        
        cnpj = str(cnpj).strip()
        if not cnpj:
            return None
        
        # Remove all non-numeric characters
        cnpj_clean = ''.join(filter(str.isdigit, cnpj))
        
        # CNPJ must have exactly 14 digits
        if len(cnpj_clean) != 14:
            return None
        
        return cnpj_clean
    
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
    def validate_boolean(cls, value: Any) -> Optional[bool]:
        """Validates and converts boolean value."""
        if pd.isna(value):
            return None
        
        value_str = str(value).strip().lower()
        
        # True values
        if value_str in ["true", "1", "yes", "sim", "s", "y", "t"]:
            return True
        
        # False values
        if value_str in ["false", "0", "no", "nao", "n", "f"]:
            return False
        
        return None
    
    @classmethod
    def validate_int(cls, value: Any, min_value: Optional[int] = None) -> Optional[int]:
        """Validates and converts integer value."""
        if pd.isna(value):
            return None
        
        try:
            int_value = int(float(str(value).strip()))
            if min_value is not None and int_value < min_value:
                return None
            return int_value
        except (ValueError, TypeError):
            return None
    
    @classmethod
    def validate_datetime(cls, value: Any) -> Optional[datetime]:
        """Validates and converts datetime value."""
        if pd.isna(value):
            return None
        
        value_str = str(value).strip()
        if not value_str:
            return None
        
        # Try different datetime formats
        formats = [
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%d/%m/%Y %H:%M:%S",
            "%d/%m/%Y"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(value_str, fmt)
            except ValueError:
                continue
        
        return None
    
    @classmethod
    async def process_csv(cls, file: BytesIO) -> Dict:
        """
        Processes a CSV file and returns list of validated companies.
        
        Args:
            file: BytesIO of the CSV file
            
        Returns:
            Dict with 'companies' (list of CompanyCreate) and 'errors' (list of errors)
        """
        try:
            logger.info("Starting Company CSV file reading...")
            # Reads CSV
            df = pd.read_csv(file, encoding='utf-8')
            logger.info(f"CSV read successfully: {len(df)} rows found")
            
            # Normalizes columns
            logger.debug("Normalizing column names...")
            df = cls.normalize_columns(df)
            logger.debug(f"Columns after normalization: {list(df.columns)}")
            
            # Validates that CSV does NOT contain ID columns (IDs are auto-generated by MongoDB)
            id_columns = ["id", "_id", "customer_id", "company_id", "user_id"]
            found_id_columns = [col for col in id_columns if col in df.columns]
            
            if found_id_columns:
                logger.error(f"CSV contains ID columns which are not allowed: {found_id_columns}")
                logger.error(f"IDs are automatically generated by MongoDB. Please remove these columns from the CSV.")
                raise ValueError(
                    f"CSV contains ID columns which are not allowed: {', '.join(found_id_columns)}. "
                    f"IDs are automatically generated by MongoDB. Please remove these columns from the CSV."
                )
            
            # Validates that this is NOT a customer CSV
            # Customer CSVs require phone and license_type, and don't have company-specific columns
            customer_required_columns = ["phone", "license_type"]
            has_customer_required = all(col in df.columns for col in customer_required_columns)
            
            # Company-specific columns that indicate this is a company CSV
            company_specific_columns = ["cnpj", "employee_count", "contract_expiration", "license_timeout", "portal_id", "linked", "address", "city", "state", "zip_code"]
            has_company_columns = any(col in df.columns for col in company_specific_columns)
            
            # If it has customer required columns but no company-specific columns, it's likely a customer CSV
            if has_customer_required and not has_company_columns:
                logger.error(f"CSV appears to be a Customer CSV (has customer required columns but no company-specific columns)")
                logger.error(f"Available columns in CSV: {list(df.columns)}")
                raise ValueError(
                    f"This CSV appears to be for Customers, not Companies. "
                    f"Found customer-specific pattern (phone and license_type without company-specific columns). "
                    f"Please use the /api/csv/customers/upload endpoint instead."
                )
            
            # Validates required columns
            required_columns = ["name"]
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                logger.error(f"Required columns missing: {missing_columns}")
                logger.error(f"Available columns in CSV: {list(df.columns)}")
                raise ValueError(f"Required columns missing: {', '.join(missing_columns)}. Available columns: {', '.join(df.columns)}")
            
            companies = []
            errors = []
            invalid_rows_details: List[InvalidRowDetail] = []
            
            logger.info(f"Processing {len(df)} CSV rows...")
            for index, row in df.iterrows():
                row_number = index + 2  # +2 because index is 0-based and we skip header
                row_errors: List[str] = []
                raw_row_data = {col: str(row.get(col, "")) if pd.notna(row.get(col)) else "" for col in df.columns}
                
                try:
                    # Validates name (required)
                    name = str(row.get("name", "")).strip()
                    if not name:
                        error_msg = "Name cannot be empty"
                        row_errors.append(error_msg)
                        logger.warning(f"Row {row_number}: {error_msg}")
                    
                    # Validates and normalizes CNPJ (optional but recommended)
                    cnpj = None
                    cnpj_raw = row.get("cnpj")
                    if pd.notna(cnpj_raw):
                        cnpj = cls.validate_cnpj(cnpj_raw)
                        if not cnpj:
                            error_msg = f"Invalid CNPJ format (value: '{cnpj_raw}', must be 14 digits)"
                            row_errors.append(error_msg)
                            logger.warning(f"Row {row_number}: {error_msg}")
                    
                    # Validates and normalizes phone (optional)
                    phone = None
                    phone_raw = row.get("phone")
                    if pd.notna(phone_raw):
                        phone = cls.validate_phone(phone_raw)
                        if not phone:
                            error_msg = f"Invalid phone format (value: '{phone_raw}')"
                            row_errors.append(error_msg)
                            logger.warning(f"Row {row_number}: {error_msg}")
                    
                    # Validates and normalizes license type (optional)
                    license_type = None
                    license_type_raw = row.get("license_type")
                    if pd.notna(license_type_raw):
                        license_type = cls.validate_license_type(license_type_raw)
                        if not license_type:
                            error_msg = f"Invalid license type (value: '{license_type_raw}', must be 'Start' or 'Hub')"
                            row_errors.append(error_msg)
                            logger.warning(f"Row {row_number}: {error_msg}")
                    
                    # Validates boolean fields
                    linked = cls.validate_boolean(row.get("linked")) if pd.notna(row.get("linked")) else False
                    active = cls.validate_boolean(row.get("active")) if pd.notna(row.get("active")) else True
                    
                    # Validates integer fields
                    license_timeout = cls.validate_int(row.get("license_timeout"), min_value=0) if pd.notna(row.get("license_timeout")) else None
                    employee_count = cls.validate_int(row.get("employee_count"), min_value=0) if pd.notna(row.get("employee_count")) else None
                    
                    # Validates datetime field
                    contract_expiration = None
                    contract_expiration_raw = row.get("contract_expiration")
                    if pd.notna(contract_expiration_raw):
                        contract_expiration = cls.validate_datetime(contract_expiration_raw)
                        if not contract_expiration:
                            error_msg = f"Invalid date format for contract_expiration (value: '{contract_expiration_raw}')"
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
                    
                    # Creates CompanyCreate object
                    company = CompanyCreate(
                        name=name,
                        cnpj=cnpj,
                        email=str(row.get("email", "")).strip() if pd.notna(row.get("email")) else None,
                        phone=phone,
                        address=str(row.get("address", "")).strip() if pd.notna(row.get("address")) else None,
                        city=str(row.get("city", "")).strip() if pd.notna(row.get("city")) else None,
                        state=str(row.get("state", "")).strip() if pd.notna(row.get("state")) else None,
                        zip_code=str(row.get("zip_code", "")).strip() if pd.notna(row.get("zip_code")) else None,
                        linked=linked if linked is not None else False,
                        active=active if active is not None else True,
                        license_timeout=license_timeout,
                        contract_expiration=contract_expiration,
                        employee_count=employee_count,
                        license_type=license_type,
                        portal_id=str(row.get("portal_id", "")).strip() if pd.notna(row.get("portal_id")) else None,
                        notes=str(row.get("notes", "")).strip() if pd.notna(row.get("notes")) else None
                    )
                    
                    companies.append(company)
                    logger.debug(f"Row {row_number} processed successfully: {name}")
                    
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
            
            logger.info(f"Processing completed: {len(companies)} valid companies, {len(invalid_rows_details)} invalid rows")
            
            # Creates validation result
            validation_result = CSVValidationResult(
                total_rows=len(df),
                valid_rows=len(companies),
                invalid_rows=len(invalid_rows_details),
                invalid_rows_details=invalid_rows_details,
                has_errors=len(invalid_rows_details) > 0
            )
            
            return {
                "companies": companies,
                "errors": errors,
                "validation": validation_result,
                "total_rows": len(df),
                "success": len(companies),
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

