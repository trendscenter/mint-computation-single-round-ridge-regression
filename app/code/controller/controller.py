import json
from nvflare.apis.impl.controller import Controller, Task, ClientTask
from nvflare.apis.fl_context import FLContext
from nvflare.apis.signal import Signal
from nvflare.apis.shareable import Shareable
from utils.utils import get_parameters_file_path

# Task names
TASK_NAME_PERFORM_REGRESSION = "perform_regression"
TASK_NAME_SAVE_GLOBAL_REGRESSION_RESULTS = "save_global_regression_results"

class SrrController(Controller):
    def __init__(
        self,
        regression_aggregator_id="regression_aggregator",
        min_clients: int = 2,
        wait_time_after_min_received: int = 10,
        task_timeout: int = 0,
    ):
        super().__init__()
        self.regression_aggregator_id = regression_aggregator_id
        self.regression_aggregator = None
        self._task_timeout = task_timeout
        self._min_clients = min_clients
        self._wait_time_after_min_received = wait_time_after_min_received

    def start_controller(self, fl_ctx: FLContext) -> None:
        self.regression_aggregator = self._engine.get_component(self.regression_aggregator_id)

    def stop_controller(self, fl_ctx: FLContext) -> None:
        pass

    def control_flow(self, abort_signal: Signal, fl_ctx: FLContext) -> None:
        self._load_and_set_computation_parameters(fl_ctx)

        self._broadcast_task(
            task_name=TASK_NAME_PERFORM_REGRESSION,
            data=Shareable(),
            result_cb=self._accept_site_regression_result,
            fl_ctx=fl_ctx,
            abort_signal=abort_signal
        )

        aggregate_result = self.regression_aggregator.aggregate()

        self._broadcast_task(
            task_name=TASK_NAME_SAVE_GLOBAL_REGRESSION_RESULTS,
            data=aggregate_result,
            result_cb=None,
            fl_ctx=fl_ctx,
            abort_signal=abort_signal
        )

    def _broadcast_task(self, task_name: str, data: Shareable, result_cb: callable, fl_ctx: FLContext, abort_signal: Signal) -> None:
        self.broadcast_and_wait(
            task=Task(
                name=task_name,
                data=data,
                props={},
                timeout=self._task_timeout,
                result_received_cb=result_cb,
            ),
            min_responses=self._min_clients,
            wait_time_after_min_received=self._wait_time_after_min_received,
            fl_ctx=fl_ctx,
            abort_signal=abort_signal,
        )

    def _load_and_set_computation_parameters(self, fl_ctx: FLContext) -> None:
        with open(get_parameters_file_path(fl_ctx), 'r') as f:
            fl_ctx.set_prop(
                key="COMPUTATION_PARAMETERS",
                value=json.load(f),
                private=False,
                sticky=True
            )

    def _accept_site_regression_result(self, client_task: ClientTask, fl_ctx: FLContext) -> bool:
        return self.regression_aggregator.accept(client_task.result, fl_ctx)

    def process_result_of_unknown_task(self, task: Task, fl_ctx: FLContext) -> None:
        pass
