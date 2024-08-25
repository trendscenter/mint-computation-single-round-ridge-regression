import logging
import os
import pandas as pd
import statsmodels.api as sm
import json
from nvflare.apis.executor import Executor
from nvflare.apis.shareable import Shareable
from nvflare.apis.fl_context import FLContext
from nvflare.apis.signal import Signal
from utils.utils import get_data_directory_path, get_output_directory_path

# Task names
TASK_NAME_PERFORM_RUN_INPUT_VALIDATION = "perform_run_input_validation"
TASK_NAME_SAVE_GLOBAL_VALIDATION_REPORT = "save_global_validation_report"
TASK_NAME_PERFORM_REGRESSION = "perform_regression"
TASK_NAME_SAVE_GLOBAL_REGRESSION_RESULTS = "save_global_regression_results"

class SrrExecutor(Executor):
    def __init__(self):
        logging.info("SrrExecutor initialized")
    
    def execute(
        self,
        task_name: str,
        shareable: Shareable,
        fl_ctx: FLContext,
        abort_signal: Signal,
    ) -> Shareable:
        if task_name == TASK_NAME_PERFORM_RUN_INPUT_VALIDATION:
            return self._do_task_run_input_validation(shareable, fl_ctx, abort_signal)
        elif task_name == TASK_NAME_SAVE_GLOBAL_VALIDATION_REPORT:
            self._do_task_save_global_validation_report(shareable, fl_ctx, abort_signal)
        elif task_name == TASK_NAME_PERFORM_REGRESSION:
            return self._do_task_perform_regression(shareable, fl_ctx, abort_signal)
        elif task_name == TASK_NAME_SAVE_GLOBAL_REGRESSION_RESULTS:
            self._do_task_save_global_regression_results(shareable, fl_ctx, abort_signal)
        else:
            raise ValueError(f"Unknown task name: {task_name}")

    def _do_task_run_input_validation(
        self,
        shareable: Shareable,
        fl_ctx: FLContext,
        abort_signal: Signal
    ) -> Shareable:
        """
        Validate the computation parameters and ensure they match the site data.
        """
        # Retrieve the computation parameters from the FL context
        comp_params = fl_ctx.get_peer_context().get_prop("COMPUTATION_PARAMETERS")
        dependents = comp_params.get("Dependents", {})
        covariates = comp_params.get("Covariates", {})

        # Retrieve the paths to the data files
        data_directory = get_data_directory_path(fl_ctx)
        covariates_path = os.path.join(data_directory, "covariates.csv")
        data_path = os.path.join(data_directory, "data.csv")

        # Load the site data
        covariates_df = pd.read_csv(covariates_path)
        data_df = pd.read_csv(data_path)

        # Extract the headers from the data
        covariates_headers = set(covariates_df.columns)
        data_headers = set(data_df.columns)

        # Check for required columns in either file
        missing_columns = []
        for col in covariates.keys():
            if col not in covariates_headers:
                missing_columns.append(col)
        for col in dependents.keys():
            if col not in data_headers:
                missing_columns.append(col)

        # Save local validation report
        validation_report = {
            "site_id": fl_ctx.get_identity_name(),
            "validation_status": len(missing_columns) == 0,
            "missing_columns": missing_columns,
            "data_headers": {
                "covariates_headers": list(covariates_headers),
                "data_headers": list(data_headers)
            },
            "computation_parameters": comp_params,
            "timestamp": pd.Timestamp.now().isoformat(),
            "notes": "Validation completed." if not missing_columns else "Validation failed."
        }
        self._save_local_validation_report(validation_report, fl_ctx)

        # Prepare the validation result as a Shareable
        validation_result = Shareable()
        validation_result["is_valid"] = len(missing_columns) == 0
        validation_result["missing_columns"] = missing_columns

        return validation_result

    def _do_task_save_global_validation_report(
        self,
        shareable: Shareable,
        fl_ctx: FLContext,
        abort_signal: Signal
    ) -> None:
        """
        Save the global validation report to a file.
        """
        validation_report = shareable.get("validation_report")
        self.save_json_to_output_dir(validation_report, "global_validation_report.json", fl_ctx)

    def _do_task_perform_regression(
        self,
        shareable: Shareable,
        fl_ctx: FLContext,
        abort_signal: Signal,
    ) -> Shareable:
        """
        Perform the regression analysis on the merged site data.
        """
        # Retrieve the computation parameters from the FL context
        comp_params = fl_ctx.get_peer_context().get_prop("COMPUTATION_PARAMETERS")
        dependents = list(comp_params.get("Dependents", {}).keys())
        covariates = list(comp_params.get("Covariates", {}).keys())

        # Retrieve the paths to the data files
        data_directory = get_data_directory_path(fl_ctx)
        covariates_path = os.path.join(data_directory, "covariates.csv")
        data_path = os.path.join(data_directory, "data.csv")

        # Load the data
        covariates_df = pd.read_csv(covariates_path)
        data_df = pd.read_csv(data_path)

        # Merge the data on the common key (e.g., ICV)
        merged_data = pd.merge(covariates_df, data_df, on="ICV", how="outer")

        # Ensure the dependent and independent variables are present in the merged data
        for col in dependents + covariates:
            if col not in merged_data.columns:
                raise ValueError(f"Column {col} is missing from the data.")

        # Prepare the regression input
        y = merged_data[dependents]
        X = merged_data[covariates]
        X = sm.add_constant(X)  # Add a constant term to the model

        # Fit the model (assuming multiple dependent variables can be handled)
        model = sm.OLS(y, X).fit()

        # Save local regression output
        regression_output = {
            "site_id": fl_ctx.get_identity_name(),
            "regression_model": {
                "dependent_variables": dependents,
                "independent_variables": covariates
            },
            "coefficients": model.params.tolist(),
            "p_values": model.pvalues.tolist(),
            "r_squared": model.rsquared,
            "adjusted_r_squared": model.rsquared_adj,
            "residuals": model.resid.tolist(),
            "timestamp": pd.Timestamp.now().isoformat(),
            "notes": "Regression completed successfully."
        }
        self._save_local_regression_output(regression_output, fl_ctx)

        # Prepare the result as a Shareable
        site_result = Shareable()
        site_result["coefficients"] = model.params.tolist()
        site_result["p_values"] = model.pvalues.tolist()
        site_result["r_squared"] = model.rsquared
        site_result["adjusted_r_squared"] = model.rsquared_adj
        site_result["residuals"] = model.resid.tolist()

        return site_result

    def _do_task_save_global_regression_results(
        self,
        shareable: Shareable,
        fl_ctx: FLContext,
        abort_signal: Signal
    ) -> None:
        """
        Save the global regression results to a file.
        """
        results = shareable.get("results")
        self.save_json_to_output_dir(results, "global_regression_results.json", fl_ctx)

    def _save_local_validation_report(self, validation_report: dict, fl_ctx: FLContext) -> None:
        """
        Save a local validation report that contains detailed information about the validation results.
        """
        self.save_json_to_output_dir(validation_report, "local_validation_report.json", fl_ctx)

    def _save_local_regression_output(self, regression_output: dict, fl_ctx: FLContext) -> None:
        """
        Save a local regression output that contains detailed information about the regression results.
        """
        self.save_json_to_output_dir(regression_output, "local_regression_output.json", fl_ctx)

    def save_json_to_output_dir(self, data: dict, filename: str, fl_ctx: FLContext) -> None:
        """
        Save a dictionary as a JSON file in the output directory.
        """
        output_dir = get_output_directory_path(fl_ctx)
        output_path = os.path.join(output_dir, filename)
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=4)
