class AverageExecutor(Executor):
    def execute(
        self,
        task_name: str,
        shareable: Shareable,
        fl_ctx: FLContext,
        abort_signal: Signal,
    ) -> Shareable:
        if task_name == "perform_regression":
            return self._perform_regression(shareable, fl_ctx, abort_signal)
        elif task_name == "save_results":
            self._save_results(shareable, fl_ctx, abort_signal)
        else:
            raise ValueError(f"Unknown task name: {task_name}")

    def _perform_regression(
        self,
        shareable: Shareable,
        fl_ctx: FLContext,
        abort_signal: Signal,
    ) -> Shareable:
        # Implement the regression logic here
        site_result = Shareable()  # Replace with actual regression result
        # Populate site_result with relevant data
        return site_result

    def _save_results(
        self,
        shareable: Shareable,
        fl_ctx: FLContext,
        abort_signal: Signal,
    ) -> None:
        # Implement logic to save the results locally
        # Extract necessary data from the shareable and save it
        pass
