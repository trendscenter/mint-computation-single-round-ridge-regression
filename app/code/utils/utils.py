import os
import logging
from nvflare.apis.fl_constant import FLContextKey
from nvflare.apis.fl_context import FLContext

def get_data_directory_path(fl_ctx: FLContext) -> str:
    """Determine and return the data directory path based on the available paths."""
    site_name = fl_ctx.get_prop(FLContextKey.CLIENT_NAME)

    # Identify possible paths
    env_path = os.getenv("DATA_DIR")
    simulator_path = os.path.abspath(os.path.join(os.getcwd(), f"../../../test_data/{site_name}"))
    poc_path = os.path.abspath(os.path.join(os.getcwd(), f"../../../../test_data/{site_name}"))

    # List paths in order of preference
    paths = [env_path, simulator_path, poc_path]

    # Check for the first valid path
    for path in paths:
        if path and os.path.exists(path):
            logging.info(f"Data directory path: {path}")
            return path

    raise FileNotFoundError("Data directory path could not be determined.")

def get_output_directory_path(fl_ctx: FLContext) -> str:
    """Determine and return the output directory path based on the available paths."""
    job_id = fl_ctx.get_job_id()
    site_name = fl_ctx.get_prop(FLContextKey.CLIENT_NAME)

    # Identify possible paths
    env_path = os.getenv("OUTPUT_DIR")
    simulator_path = os.path.abspath(os.path.join(os.getcwd(), f"../../../test_output/{job_id}/{site_name}"))
    poc_path = os.path.abspath(os.path.join(os.getcwd(), f"../../../../test_output/{job_id}/{site_name}"))

    # List paths in order of preference
    paths = [env_path, simulator_path, poc_path]

    # Check for the first valid path and create it if necessary
    for path in paths:
        if path:
            os.makedirs(path, exist_ok=True)
            logging.info(f"Output directory path: {path}")
            return path

    raise FileNotFoundError("Output directory path could not be determined.")

def get_parameters_file_path(fl_ctx: FLContext) -> str:
    """Determine and return the parameters file path based on the available paths."""

    # Identify possible paths
    env_path = os.getenv("PARAMETERS_FILE_PATH")
    simulator_path = os.path.abspath(os.path.join(os.getcwd(), "../test_data/server/parameters.json"))
    poc_path = os.path.abspath(os.path.join(os.getcwd(), "../../../../test_data/server/parameters.json"))

    # List paths in order of preference
    paths = [env_path, simulator_path, poc_path]

    # Check for the first valid path
    for path in paths:
        if path and os.path.exists(path):
            logging.info(f"Parameters file path: {path}")
            return path

    raise FileNotFoundError("Parameters file path could not be determined.")
