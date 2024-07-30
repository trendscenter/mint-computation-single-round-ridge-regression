import os
import json
import pickle
import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.linear_model import Ridge
from nvflare.apis.executor import Executor
from nvflare.apis.fl_constant import FLContextKey
from nvflare.apis.shareable import Shareable
from nvflare.apis.fl_context import FLContext
from nvflare.apis.signal import Signal


class RidgeRegressionExecutor(Executor):
    def __init__(self):
        super().__init__()
        self.model_path = "ridge_model.pkl"
        self.parameters_path = "parameters.pkl"
        self.data_path = "training_data.pkl"

    def execute(self, task_name: str, shareable: Shareable, fl_ctx: FLContext, abort_signal: Signal) -> Shareable:
        print(f"Executing task: {task_name}")
        if task_name == "train_local_model":
            return self._task_train_local_model(fl_ctx)
        elif task_name == "set_global_model":
            return self._task_set_global_model(shareable, fl_ctx)
        return Shareable()

    def _task_train_local_model(self, fl_ctx: FLContext) -> Shareable:
        data_dir = self._get_data_dir_path(fl_ctx)

        parameters = fl_ctx.get_peer_context().get_prop("COMPUTATION_PARAMETERS", default=None)
        print(f"Computation parameters: {parameters}")

        X_train, y_train = self._load_data(data_dir, parameters)
        print(f"Loaded data shapes - X: {X_train.shape}, y: {y_train.shape}")

        model = Ridge(alpha=parameters.get('Lambda', 1.0))
        model.fit(X_train, y_train)
        print("Model training completed.")

        self._save_model(model)
        self._save_parameters(parameters)
        self._save_data(X_train, y_train)

        shareable = Shareable()
        shareable["weights"] = model.coef_.tolist()
        return shareable


    def _task_set_global_model(self, shareable: Shareable, fl_ctx) -> Shareable:
        print("Setting global model.")
        global_weights = shareable.get("global_model", {}).get("weights")

        model = self._load_model()
        X_train, y_train = self._load_data_from_file()
        model.coef_ = np.array(global_weights)

        try:
            # Ensuring y_train is a 1-dimensional array for OLS
            if y_train.ndim > 1 and y_train.shape[1] == 1:
                y_train = y_train.flatten()

            X_train = X_train.astype(float)
            y_train = y_train.astype(float)
            X_with_const = sm.add_constant(X_train)
            sm_model = sm.OLS(y_train, X_with_const).fit()

            # Extracting coefficients and statistics
            coefficients = sm_model.params.tolist()
            t_stats = sm_model.tvalues.tolist()
            p_values = sm_model.pvalues.tolist()
            conf_int = sm_model.conf_int().tolist()
            r_squared = sm_model.rsquared
            degrees_of_freedom = int(sm_model.df_resid)

            # Preparing the JSON output
            model_stats = {
                "coefficients": coefficients,
                "t_stats": t_stats,
                "p_values": p_values,
                "confidence_intervals": conf_int,
                "r_squared": r_squared,
                "degrees_of_freedom": degrees_of_freedom
            }

            self._save_global_model_to_file(global_weights, model_stats, fl_ctx)

        except Exception as e:
            print(f"\n\nError in calculating model statistics: {e}\n\n")

        return Shareable()


    def _load_data(self, data_dir, parameters):
        print(f"Loading data from: {data_dir}")
        covariates_file = os.path.join(data_dir, "covariates.csv")
        data_file = os.path.join(data_dir, "data.csv")

        if not os.path.exists(covariates_file) or not os.path.exists(data_file):
            raise FileNotFoundError("Required data files are missing.")

        covariates_df = pd.read_csv(covariates_file)
        data_df = pd.read_csv(data_file)

        print(f"Loaded files: {covariates_file}, {data_file}")

        x_headers = parameters.get('X_headers', [])
        y_headers = parameters.get('y_headers', [])

        if not all(col in covariates_df.columns for col in x_headers):
            raise ValueError("Some specified X_headers do not exist in the covariates dataframe.")
        if not all(col in data_df.columns for col in y_headers):
            raise ValueError("Some specified y_headers do not exist in the data dataframe.")

        def convert_to_int(value):
            if isinstance(value, str):
                if value.lower() == 'true':
                    return 1
                elif value.lower() == 'false':
                    return 0
            return value

        covariates_df = covariates_df.applymap(convert_to_int)

        # Convert to numeric and handle errors
        covariates_df = covariates_df[x_headers].apply(pd.to_numeric, errors='coerce')
        data_df = data_df[y_headers].apply(pd.to_numeric, errors='coerce')

        # Drop rows with NaN values
        covariates_df.dropna(inplace=True)
        data_df.dropna(inplace=True)

        # Ensure consistent sample size between X and y
        if len(covariates_df) != len(data_df):
            raise ValueError("Inconsistent number of samples between covariates and data.")

        X = covariates_df.to_numpy()
        y = data_df.sum(axis=1).to_numpy()  # Summing y values or adjust as needed

        print(f"Extracted data - X: {X[:5]}, y: {y[:5]}")
        print(f"Loaded data shapes - X: {X.shape}, y: {y.shape}")

        return X, y

    
    def _save_data(self, X, y):
        with open(self.data_path, 'wb') as f:
            pickle.dump((X, y), f)

    def _load_data_from_file(self):
        if os.path.exists(self.data_path):
            with open(self.data_path, 'rb') as f:
                return pickle.load(f)
        else:
            raise FileNotFoundError("Training data file not found.")

    def _get_data_dir_path(self, fl_ctx: FLContext) -> str:
        site_name = fl_ctx.get_prop(FLContextKey.CLIENT_NAME)
        production_path = os.getenv("DATA_DIR")
        simulator_path = os.path.abspath(os.path.join(
            os.getcwd(), "../../../test_data", site_name))
        poc_path = os.path.abspath(os.path.join(
            os.getcwd(), "../../../../test_data", site_name))

        print(f"Determining data directory for site: {site_name}")
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

    def _save_global_model_to_file(self, global_weights: list, model_stats: dict, fl_ctx: FLContext):
        results_dir = self._get_results_dir_path(fl_ctx)
        os.makedirs(results_dir, exist_ok=True)
        file_path = os.path.join(results_dir, "global_model.json")

        print(f"Saving global model to: {file_path}")
        with open(file_path, "w") as f:
            json.dump({"weights": global_weights,
                      "model_statistics": model_stats}, f)

    def _save_model(self, model):
        with open(self.model_path, 'wb') as f:
            pickle.dump(model, f)

    def _load_model(self):
        if os.path.exists(self.model_path):
            with open(self.model_path, 'rb') as f:
                return pickle.load(f)
        else:
            raise FileNotFoundError("Model file not found.")

    def _save_parameters(self, parameters):
        with open(self.parameters_path, 'wb') as f:
            pickle.dump(parameters, f)

    def _load_parameters(self):
        if os.path.exists(self.parameters_path):
            with open(self.parameters_path, 'rb') as f:
                return pickle.load(f)
        else:
            raise FileNotFoundError("Parameters file not found.")
