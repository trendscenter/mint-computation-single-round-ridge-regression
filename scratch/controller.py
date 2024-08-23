TASK_NAME_PERFORM_REGRESSION = "perform_regression"
TASK_NAME_SAVE_RESULTS = "save_results"

class RidgeRegressionController(Controller):
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

        # Step 1: Broadcast and perform regression task
        self._broadcast_perform_regression_task(fl_ctx, abort_signal)

        # Step 2: Aggregate results
        aggregate_result = self._aggregate_results()

        # Step 3: Broadcast and save results task
        self._broadcast_save_results_task(aggregate_result, fl_ctx, abort_signal)

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
