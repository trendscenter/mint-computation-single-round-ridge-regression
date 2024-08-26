import logging
import os
import pandas as pd
from typing import Dict, Any

def validate_run_input(covariates_path: str, data_path: str, computation_parameters: Dict[str, Any], log_path: str) -> bool:
    try:
        # Load the data
        covariates = pd.read_csv(covariates_path)
        data = pd.read_csv(data_path)
        
        # Extract expected headers from computation parameters
        expected_covariates = computation_parameters.get("Covariates", [])
        expected_dependents = computation_parameters.get("Dependents", [])

        # Validate covariates headers
        covariates_headers = set(covariates.columns)
        if not set(expected_covariates).issubset(covariates_headers):
            error_message = f"Covariates headers do not contain all expected headers. Expected at least {expected_covariates}, but got {covariates_headers}."
            _log_validation_error(error_message, log_path)
            return False
        
        # Validate data headers
        data_headers = set(data.columns)
        if not set(expected_dependents).issubset(data_headers):
            error_message = f"Data headers do not contain all expected headers. Expected at least {expected_dependents}, but got {data_headers}."
            _log_validation_error(error_message, log_path)
            return False

        # If all checks pass
        return True

    except Exception as e:
        error_message = f"An error occurred during validation: {str(e)}"
        _log_validation_error(error_message, log_path)
        return False


def _log_validation_error(message: str, log_path: str) -> None:
    """
    Log the validation error message to the console and write it to validation_log.txt.
    """
    logging.error(message)
    try:
        with open(log_path, 'a') as f:
            f.write(f"{message}\n")
            f.flush()  # Ensure data is written to the file
    except IOError as e:
        logging.error(f"Failed to write to log file {log_path}: {e}")
