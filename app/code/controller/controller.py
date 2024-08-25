import json
from nvflare.apis.impl.controller import Controller, Task, ClientTask
from nvflare.apis.fl_context import FLContext
from nvflare.apis.signal import Signal
from nvflare.apis.shareable import Shareable
from utils.utils import get_parameters_file_path
import logging

# Task names
TASK_NAME_PERFORM_RUN_INPUT_VALIDATION = "perform_run_input_validation"
TASK_NAME_SAVE_GLOBAL_VALIDATION_REPORT = "save_global_validation_report"
TASK_NAME_PERFORM_REGRESSION = "perform_regression"
TASK_NAME_SAVE_GLOBAL_REGRESSION_RESULTS = "save_global_regression_results"

class SrrController(Controller):
    def __init__(
        self,
        regression_aggregator_id="regression_aggregator",
        validation_aggregator_id="validation_aggregator",
        min_clients: int = 2,
        wait_time_after_min_received: int = 10,
        task_timeout: int = 0,
    ):
        super().__init__()
        self.regression_aggregator_id = regression_aggregator_id
        self.validation_aggregator_id = validation_aggregator_id
        self.regression_aggregator = None
        self.validation_aggregator = None
        self._task_timeout = task_timeout
        self._min_clients = min_clients
        self._wait_time_after_min_received = wait_time_after_min_received

    def start_controller(self, fl_ctx: FLContext) -> None:
        self.regression_aggregator = self._engine.get_component(self.regression_aggregator_id)
        self.validation_aggregator = self._engine.get_component(self.validation_aggregator_id)

    def stop_controller(self, fl_ctx: FLContext) -> None:
        pass

    def control_flow(self, abort_signal: Signal, fl_ctx: FLContext) -> None:
        fl_ctx.set_prop(key="CURRENT_ROUND", value=0)
        
        # Step 1: Load and set computation parameters
        self._load_and_set_computation_parameters(fl_ctx)

        # Step 2: Broadcast perform run input validation
        self._broadcast_task(
            task_name=TASK_NAME_PERFORM_RUN_INPUT_VALIDATION,
            data=Shareable(),
            result_cb=self._accept_site_validation_result,
            fl_ctx=fl_ctx,
            abort_signal=abort_signal
        )
        
        # Step 3: Aggregate and check validation results
        validation_report = self.validation_aggregator.aggregate()
        self._broadcast_task(
            task_name=TASK_NAME_SAVE_GLOBAL_VALIDATION_REPORT,
            data=validation_report,
            result_cb=None,  # No callback needed for save validation report
            fl_ctx=fl_ctx,
            abort_signal=abort_signal
        )
        
        if not self._check_validation_results(validation_report):
            self._graceful_shutdown(fl_ctx)
            return

        # Step 4: Broadcast perform regression task
        self._broadcast_task(
            task_name=TASK_NAME_PERFORM_REGRESSION,
            data=Shareable(),
            result_cb=self._accept_site_regression_result,
            fl_ctx=fl_ctx,
            abort_signal=abort_signal
        )

        # Step 5: Aggregate regression results
        aggregate_result = self._aggregate_regression_results()

        # Step 6: Broadcast save regression results task
        self._broadcast_task(
            task_name=TASK_NAME_SAVE_GLOBAL_REGRESSION_RESULTS,
            data=aggregate_result,
            result_cb=self._accept_site_regression_result,
            fl_ctx=fl_ctx,
            abort_signal=abort_signal
        )

    def _broadcast_task(self, task_name: str, data: Shareable, result_cb: callable, fl_ctx: FLContext, abort_signal: Signal) -> None:
        """General method to broadcast a task."""
        task = Task(
            name=task_name,
            data=data,
            props={},
            timeout=self._task_timeout,
            result_received_cb=result_cb,
        )

        self.broadcast_and_wait(
            task=task,
            min_responses=self._min_clients,
            wait_time_after_min_received=self._wait_time_after_min_received,
            fl_ctx=fl_ctx,
            abort_signal=abort_signal,
        )

    def _load_and_set_computation_parameters(self, fl_ctx: FLContext) -> None:
        """Load computation parameters from file and set them in the FL context."""
        parameters_file_path = get_parameters_file_path(fl_ctx)
        computation_parameters = self._load_computation_parameters(parameters_file_path)
        fl_ctx.set_prop(
            key="COMPUTATION_PARAMETERS",
            value=computation_parameters,
            private=False,
            sticky=True
        )

    def _load_computation_parameters(self, parameters_file_path: str) -> dict:
        """Load computation parameters from the specified file."""
        with open(parameters_file_path, 'r') as f:
            return json.load(f)

    def _accept_site_validation_result(self, client_task: ClientTask, fl_ctx: FLContext) -> bool:
        """Accept the validation result from a site."""
        return self.validation_aggregator.accept(client_task.result, fl_ctx)

    def _check_validation_results(self, validation_report: Shareable) -> bool:
        """Check if all sites passed validation based on the aggregated report."""
        if not validation_report.get("is_valid"):
            logging.error(f"Validation failed: {validation_report.get('error_message', 'Unknown error')}")
            return False
        return True

    def _accept_site_regression_result(self, client_task: ClientTask, fl_ctx: FLContext) -> bool:
        """Accept the regression result from a site."""
        return self.regression_aggregator.accept(client_task.result, fl_ctx)

    def _aggregate_regression_results(self) -> Shareable:
        """Aggregate the regression results from all sites."""
        return self.regression_aggregator.aggregate()

    def _graceful_shutdown(self, fl_ctx: FLContext) -> None:
        """Perform any necessary cleanup and terminate the workflow gracefully."""
        logging.info("Terminating workflow due to validation failure.")
        # Add any additional cleanup or logging if needed

    def process_result_of_unknown_task(self, task: Task, fl_ctx: FLContext) -> None:
        pass