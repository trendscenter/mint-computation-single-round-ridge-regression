# ridge_regression_workflow.py

from nvflare.apis.impl.controller import Controller, Task, ClientTask
from nvflare.apis.fl_context import FLContext
from nvflare.apis.signal import Signal
from nvflare.apis.shareable import Shareable
import os
import json

class RidgeRegressionWorkflow(Controller):
    def __init__(self, **kwargs):
        super().__init__()
        self.aggregator_id = kwargs.get('aggregator_id', 'ridge_aggregator')
        self._min_clients = kwargs.get('min_clients', 2)
        self._num_rounds = kwargs.get('num_rounds', 2)
        self._train_timeout = kwargs.get('train_timeout', 0)
        self._wait_time_after_min_received = kwargs.get('wait_time_after_min_received', 10)
        self._ignore_result_error = kwargs.get('ignore_result_error', False)
        self._task_check_period = kwargs.get('task_check_period', 0.5)
        self._persist_every_n_rounds = kwargs.get('persist_every_n_rounds', 1)
        self._snapshot_every_n_rounds = kwargs.get('snapshot_every_n_rounds', 1)
        self.aggregator = None
        

    def start_controller(self, fl_ctx: FLContext) -> None:
        self.aggregator = self._engine.get_component(self.aggregator_id)
        parameters_file_path = self.get_parameters_file_path()
        computation_parameters = self.load_computation_parameters(parameters_file_path)
        self.validate_parameters(computation_parameters)
        fl_ctx.set_prop(key="COMPUTATION_PARAMETERS", value=computation_parameters, private=False, sticky=True)
        
    def stop_controller(self, fl_ctx: FLContext) -> None:
        pass

    def control_flow(self, abort_signal: Signal, fl_ctx: FLContext) -> None:
        fl_ctx.set_prop(key="CURRENT_ROUND", value=0)
        
        for round_num in range(self._num_rounds):
            if abort_signal.triggered:
                break

            self.log_info(fl_ctx, f"Starting round {round_num}")
            train_task = Task(
                name="train_local_model",
                data=Shareable(),
                props={},
                timeout=self._train_timeout,
                result_received_cb=self._accept_site_result,
            )

            self.broadcast_and_wait(
                task=train_task,
                min_responses=self._min_clients,
                wait_time_after_min_received=self._wait_time_after_min_received,
                fl_ctx=fl_ctx,
                abort_signal=abort_signal,
            )

            self.log_info(fl_ctx, "Start aggregation.")
            aggr_shareable = self.aggregator.aggregate(fl_ctx)
            self.log_info(fl_ctx, "End aggregation.")

            global_model_task = Task(
                name="set_global_model",
                data=aggr_shareable,
                props={},
                timeout=self._train_timeout,
            )

            self.broadcast_and_wait(
                task=global_model_task,
                min_responses=self._min_clients,
                wait_time_after_min_received=self._wait_time_after_min_received,
                fl_ctx=fl_ctx,
                abort_signal=abort_signal,
            )

    def _accept_site_result(self, client_task: ClientTask, fl_ctx: FLContext) -> bool:
        return self.aggregator.accept(client_task.result, fl_ctx)

    def process_result_of_unknown_task(self, task: Task, fl_ctx: FLContext) -> None:
        pass

    def get_parameters_file_path(self) -> str:
        production_path = os.getenv("PARAMETERS_FILE_PATH")
        simulator_path = os.path.abspath(os.path.join(os.getcwd(), "../test_data", "server", "parameters.json"))
        poc_path = os.path.abspath(os.path.join(os.getcwd(), "../../../../test_data", "server", "parameters.json"))

        if production_path:
            return production_path
        if os.path.exists(simulator_path):
            return simulator_path
        elif os.path.exists(poc_path):
            return poc_path
        else:
            raise FileNotFoundError("Parameters file path could not be determined.")

    def load_computation_parameters(self, parameters_file_path: str):
        with open(parameters_file_path, "r") as file:
            return json.load(file)

    def validate_parameters(self, parameters: dict) -> None:
        required_keys = ['y_headers', 'X_headers', 'Lambda']
        for key in required_keys:
            if key not in parameters:
                raise ValueError(f"Validation Error: The key '{key}' is missing in the parameters.")
        if not isinstance(parameters['Lambda'], (int, float)):
            raise ValueError("Validation Error: The value of 'Lambda' must be a number.")
