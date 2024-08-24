import os
import pandas as pd
import statsmodels.api as sm
import json
from nvflare.apis.executor import Executor
from nvflare.apis.shareable import Shareable
from nvflare.apis.fl_context import FLContext
from nvflare.apis.signal import Signal
from utils.utils import get_data_directory_path, get_output_directory_path


TASK_NAME_VALIDATE_RUN_INPUT = "validate_run_input"
TASK_NAME_PERFORM_REGRESSION = "perform_regression"
TASK_NAME_SAVE_GLOBAL_RESULTS = "save_global_results"

class SrrExecutor(Executor):
    def execute(
        self,
        task_name: str,
        shareable: Shareable,
        fl_ctx: FLContext,
        abort_signal: Signal,
    ) -> Shareable:
        if task_name == TASK_NAME_VALIDATE_RUN_INPUT:
            return self._do_task_validate_run_input(shareable, fl_ctx, abort_signal)
        elif task_name == TASK_NAME_PERFORM_REGRESSION:
            return self._do_task_perform_regression(shareable, fl_ctx, abort_signal)
        elif task_name == TASK_NAME_SAVE_GLOBAL_RESULTS:
            self._do_task_save_global_results(shareable, fl_ctx, abort_signal)
        else:
            raise ValueError(f"Unknown task name: {task_name}")

    def _do_task_validate_run_input(
        self,
        shareable: Shareable,
        fl_ctx: FLContext,
        abort_signal: Signal
    ) -> Shareable:
        """
        Validate the computation parameters and ensure they match the site data.
        """
        # Retrieve the computation parameters from the shareable
        comp_params = fl_ctx.get_peer_context().get_prop("COMPUTATION_PARAMETERS")
        dependents = comp_params.get("Dependents", {})
        covariates = comp_params.get("Covariates", {})

        # Retrieve the paths to the data files
        data_directory = get_data_directory_path()
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

        # Prepare the validation result as a Shareable
        validation_result = Shareable()
        validation_result["is_valid"] = len(missing_columns) == 0
        validation_result["missing_columns"] = missing_columns

        return validation_result

    def _do_task_perform_regression(
        self,
        shareable: Shareable,
        fl_ctx: FLContext,
        abort_signal: Signal,
    ) -> Shareable:
        """
        Perform the regression analysis on the merged site data.
        """
        # Extract the relevant columns from the shareable
        comp_params = fl_ctx.get_peer_context().get_prop("COMPUTATION_PARAMETERS")
        dependents = list(comp_params.get("Dependents", {}).keys())
        covariates = list(comp_params.get("Covariates", {}).keys())

        # Retrieve the paths to the data files
        data_directory = get_data_directory_path()
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

        # Prepare the result as a Shareable
        site_result = Shareable()
        site_result["coefficients"] = model.params.tolist()
        site_result["p_values"] = model.pvalues.tolist()
        site_result["r_squared"] = model.rsquared
        site_result["adjusted_r_squared"] = model.rsquared_adj
        site_result["residuals"] = model.resid.tolist()

        return site_result

    def _do_task_save_global_results(
        self,
        shareable: Shareable,
        fl_ctx: FLContext,
        abort_signal: Signal,
    ) -> None:
        """
        Save the aggregated global results to a file.
        """
        # Assume shareable contains the results to save
        results = shareable.get("results")

        # Save the results to a file
        self.save_json_to_output_dir(results, "global_results.json")

    def save_json_to_output_dir(self, data: dict, filename: str):
        """
        Save a dictionary as a JSON file in the output directory.
        """
        output_dir = get_output_directory_path()
        output_path = output_dir + filename
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=4)
