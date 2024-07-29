from nvflare.apis.executor import Executor
from nvflare.apis.fl_constant import FLContextKey
from nvflare.apis.shareable import Shareable
from nvflare.apis.fl_context import FLContext
from nvflare.apis.signal import Signal
import pandas as pd
import numpy as np
from sklearn.linear_model import Ridge
import os
import json


class RidgeRegressionExecutor(Executor):
    def __init__(self):
        super().__init__()
        self.model = None
        self.parameters = None

    def execute(self, task_name: str, shareable: Shareable, fl_ctx: FLContext, abort_signal: Signal) -> Shareable:
        if task_name == "train_local_model":
            return self._train_local_model(fl_ctx)
        elif task_name == "set_global_model":
            return self._set_global_model(shareable)
        return Shareable()

    def _train_local_model(self, fl_ctx: FLContext) -> Shareable:
        data_dir = self._get_data_dir_path(fl_ctx)
        if not data_dir:
            raise FileNotFoundError(
                "Data directory path could not be determined.")

        self.parameters = fl_ctx.get_prop("COMPUTATION_PARAMETERS", {})
        X, y = self._load_data(data_dir)
        self.model = Ridge(alpha=self.parameters.get('Lambda', 1.0))
        self.model.fit(X, y)

        shareable = Shareable()
        shareable["weights"] = self.model.coef_.tolist()
        return shareable

    def _set_global_model(self, shareable: Shareable) -> Shareable:
        global_weights = shareable.get("global_model", {}).get("weights")
        if global_weights is not None:
            if self.model is None:
                self.model = Ridge()
            self.model.coef_ = np.array(global_weights)

            # Save global model to file
            fl_ctx = shareable.get_fl_context()
            self._save_global_model_to_file(global_weights, fl_ctx)
        return Shareable()

    def _load_data(self, data_dir):
        covariates_file = os.path.join(data_dir, "covariates.csv")
        data_file = os.path.join(data_dir, "data.csv")

        if not os.path.exists(covariates_file) or not os.path.exists(data_file):
            raise FileNotFoundError("Required data files are missing.")

        covariates_df = pd.read_csv(covariates_file)
        data_df = pd.read_csv(data_file)

        X = covariates_df[self.parameters.get('X_headers', [])]
        y = data_df[self.parameters.get('y_headers', [])]
        return X, y

    def _get_data_dir_path(self, fl_ctx: FLContext) -> str:
        site_name = fl_ctx.get_prop(FLContextKey.CLIENT_NAME)
        production_path = os.getenv("DATA_DIR")
        simulator_path = os.path.abspath(os.path.join(
            os.getcwd(), "../../../test_data", site_name))
        poc_path = os.path.abspath(os.path.join(
            os.getcwd(), "../../../../test_data", site_name))

        if production_path:
            return production_path
        if os.path.exists(simulator_path):
            return simulator_path
        if os.path.exists(poc_path):
            return poc_path

        raise FileNotFoundError("Data directory path could not be determined.")

    def _get_results_dir_path(self, fl_ctx: FLContext) -> str:
        job_id = fl_ctx.get_job_id()
        site_name = fl_ctx.get_prop(FLContextKey.CLIENT_NAME)

        production_path = os.getenv("RESULTS_DIR")
        simulator_base_path = os.path.abspath(
            os.path.join(os.getcwd(), "../../../test_results"))
        poc_base_path = os.path.abspath(os.path.join(
            os.getcwd(), "../../../../test_results"))
        simulator_path = os.path.join(simulator_base_path, job_id, site_name)
        poc_path = os.path.join(poc_base_path, job_id, site_name)

        if production_path:
            return production_path
        if os.path.exists(simulator_base_path):
            os.makedirs(simulator_path, exist_ok=True)
            return simulator_path
        if os.path.exists(poc_base_path):
            os.makedirs(poc_path, exist_ok=True)
            return poc_path

        raise FileNotFoundError(
            "Results directory path could not be determined.")

    def _save_global_model_to_file(self, global_weights: list, fl_ctx: FLContext):
        results_dir = self._get_results_dir_path(fl_ctx)
        os.makedirs(results_dir, exist_ok=True)
        file_path = os.path.join(results_dir, "global_model.json")

        print(f"Saving global model to: {file_path}")
        with open(file_path, "w") as f:
            json.dump({"weights": global_weights}, f)
