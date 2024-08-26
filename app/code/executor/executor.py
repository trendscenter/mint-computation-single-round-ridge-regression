import logging
import os
import json
from nvflare.apis.executor import Executor
from nvflare.apis.shareable import Shareable
from nvflare.apis.fl_context import FLContext
from nvflare.apis.signal import Signal
from utils.utils import get_data_directory_path, get_output_directory_path
from .perform_ridge_regression import perform_ridge_regression
from .json_to_html_results import json_to_html_results
from .validate_run_input import validate_run_input

# Task names
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

        if task_name == TASK_NAME_PERFORM_REGRESSION:
            return self._do_task_perform_regression(shareable, fl_ctx, abort_signal)
        elif task_name == TASK_NAME_SAVE_GLOBAL_REGRESSION_RESULTS:
            return self._do_task_save_global_regression_results(shareable, fl_ctx, abort_signal)
        else:
            raise ValueError(f"Unknown task name: {task_name}")
        
    def _do_task_perform_regression(
        self,
        shareable: Shareable,
        fl_ctx: FLContext,
        abort_signal: Signal,
    ) -> Shareable:
        """
        Perform the regression analysis on the merged site data.
        This function assumes that the data has already been validated and prepared.
        """

        data_directory = get_data_directory_path(fl_ctx)
        covariates_path = os.path.join(data_directory, "covariates.csv")
        data_path = os.path.join(data_directory, "data.csv")
        computation_parameters = fl_ctx.get_peer_context().get_prop("COMPUTATION_PARAMETERS")
        log_path = os.path.join(get_output_directory_path(fl_ctx), "validation_log.txt")
        
        is_valid = validate_run_input(covariates_path, data_path, computation_parameters, log_path)
        if not is_valid:
            raise ValueError(f"Invalid run input. Check validation log at {log_path}")
        
        covariates_headers = computation_parameters["Covariates"]
        data_headers = computation_parameters["Dependents"]
        
        result = perform_ridge_regression(covariates_path, data_path, covariates_headers, data_headers)
        
        self.save_json(result, "site_regression_result.json", fl_ctx)
        html = json_to_html_results(result, "Site Regression Results")
        self.save_html(html, "site_regression_result.html", fl_ctx)

        outgoing_shareable = Shareable()
        outgoing_shareable["result"] = result
        return outgoing_shareable

    def _do_task_save_global_regression_results(
        self,
        shareable: Shareable,
        fl_ctx: FLContext,
        abort_signal: Signal
    ) -> Shareable:
        """
        Save the global regression results to a file.
        """
        result = shareable.get("result")
        self.save_json(result, "global_regression_result.json", fl_ctx)
        html = json_to_html_results(result, "Global Regression Results")
        self.save_html(html, "global_regression_result.html", fl_ctx)
        return Shareable()


    def save_json(self, data: dict, filename: str, fl_ctx: FLContext) -> None:
        """
        Save a dictionary as a JSON file in the output directory.
        """
        output_dir = get_output_directory_path(fl_ctx)
        output_path = os.path.join(output_dir, filename)
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=4)

    def save_html(self, data: str, filename: str, fl_ctx: FLContext) -> None:
        """
        Save a string as an HTML file in the output directory.
        """
        output_dir = get_output_directory_path(fl_ctx)
        output_path = os.path.join(output_dir, filename)
        with open(output_path, 'w') as f:
            f.write(data)
