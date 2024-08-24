import json
from nvflare.apis.impl.controller import Controller, Task, ClientTask
from nvflare.apis.fl_context import FLContext
from nvflare.apis.signal import Signal
from nvflare.apis.shareable import Shareable
from utils.utils import get_parameters_file_path

TASK_NAME_VALIDATE_RUN_INPUT = "validate_run_input"
TASK_NAME_PERFORM_REGRESSION = "perform_regression"
TASK_NAME_SAVE_RESULTS = "save_results"

class SrrController(Controller):
    def __init__(
        self,
        aggregator_id="aggregator",
        min_clients: int = 2,
        wait_time_after_min_received: int = 10,
        task_timeout: int = 0,
    ):
        super().__init__()
        self.aggregator_id = aggregator_id
        self.aggregator = None
        self._task_timeout = task_timeout
        self._min_clients = min_clients
        self._wait_time_after_min_received = wait_time_after_min_received

    def start_controller(self, fl_ctx: FLContext) -> None:
        self.aggregator = self._engine.get_component(self.aggregator_id)

    def stop_controller(self, fl_ctx: FLContext) -> None:
        pass

    def control_flow(self, abort_signal: Signal, fl_ctx: FLContext) -> None:
        fl_ctx.set_prop(key="CURRENT_ROUND", value=0)
        
        # Step 1: Load and set computation parameters
        self._load_and_set_computation_parameters(fl_ctx)

        # Step 2: Broadcast and validate run input
        validation_results = self._broadcast_validate_run_input_task(fl_ctx, abort_signal)
        self._check_validation_results(validation_results)

        # Step 3: Broadcast and perform regression task
        self._broadcast_perform_regression_task(fl_ctx, abort_signal)

        # Step 4: Aggregate results
        aggregate_result = self._aggregate_results()

        # Step 5: Broadcast and save results task
        self._broadcast_save_results_task(aggregate_result, fl_ctx, abort_signal)

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
        # Assuming JSON format for the parameters file, you might adjust this based on the actual format
        with open(parameters_file_path, 'r') as f:
            return json.load(f)

    def _broadcast_validate_run_input_task(self, fl_ctx: FLContext, abort_signal: Signal) -> list:
        task = Task(
            name=TASK_NAME_VALIDATE_RUN_INPUT,
            data=Shareable(),
            props={},
            timeout=self._task_timeout,
            result_received_cb=self._accept_site_result,
        )
        
        validation_results = self.broadcast_and_wait(
            task=task,
            min_responses=self._min_clients,
            wait_time_after_min_received=self._wait_time_after_min_received,
            fl_ctx=fl_ctx,
            abort_signal=abort_signal,
        )
        
        return validation_results

    def _check_validation_results(self, validation_results: list) -> None:
        for result in validation_results:
            if not result["is_valid"]:
                raise ValueError(f"Validation failed for one or more sites. Missing columns: {result['missing_columns']}")

    def _broadcast_perform_regression_task(self, fl_ctx: FLContext, abort_signal: Signal) -> None:
        task = Task(
            name=TASK_NAME_PERFORM_REGRESSION,
            data=Shareable(),
            props={},
            timeout=self._task_timeout,
            result_received_cb=self._accept_site_result,
        )
        
        self.broadcast_and_wait(
            task=task,
            min_responses=self._min_clients,
            wait_time_after_min_received=self._wait_time_after_min_received,
            fl_ctx=fl_ctx,
            abort_signal=abort_signal,
            result_received_cb=self._accept_site_result,
        )

    def _aggregate_results(self) -> Shareable:
        return self.aggregator.aggregate()

    def _broadcast_save_results_task(self, aggregate_result: Shareable, fl_ctx: FLContext, abort_signal: Signal) -> None:
        task = Task(
            name=TASK_NAME_SAVE_RESULTS,
            data=aggregate_result,
            props={},
            timeout=self._task_timeout,
            result_received_cb=self._accept_site_result
        )
        
        self.broadcast_and_wait(
            task=task,
            min_responses=self._min_clients,
            wait_time_after_min_received=self._wait_time_after_min_received,
            fl_ctx=fl_ctx,
            abort_signal=abort_signal,
        )

    def _accept_site_result(self, client_task: ClientTask, fl_ctx: FLContext) -> bool:
        return self.aggregator.accept(client_task.result, fl_ctx)
    
    def process_result_of_unknown_task(self, task: Task, fl_ctx: FLContext) -> None:
        pass
