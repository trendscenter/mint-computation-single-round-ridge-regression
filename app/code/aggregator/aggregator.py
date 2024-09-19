from typing import Dict, Any
from nvflare.apis.shareable import Shareable
from nvflare.apis.fl_context import FLContext
from nvflare.app_common.abstract.aggregator import Aggregator
from nvflare.apis.fl_constant import ReservedKey
from .calculate_global_values import calculate_global_values

class SrrAggregator(Aggregator):
    """
    SrrAggregator handles the aggregation of results from multiple client sites.
    It stores individual site results and computes a global result based on the aggregation logic.

    This class can be customized if specific aggregation logic is needed.
    """

    def __init__(self):
        """
        Initializes the SrrAggregator with a dictionary to store results from multiple sites.
        """
        super().__init__()
        self.site_results: Dict[str, Dict[str, Any]] = {}  # Store results as a dictionary

    def accept(self, site_result: Shareable, fl_ctx: FLContext) -> bool:
        """
        Accepts a result from a site and stores it for later aggregation.

        This method is called when a client site sends a result. Developers can override this 
        if they need to handle or validate the results differently before storing them.

        :param site_result: The result received from the client site.
        :param fl_ctx: The federated learning context for this run.
        :return: Boolean indicating if the result was successfully accepted.
        """
        site_name = site_result.get_peer_prop(
            key=ReservedKey.IDENTITY_NAME, default=None)
        
        # Store the result for the site using its identity name as the key
        self.site_results[site_name] = site_result["result"]
        return True

    def aggregate(self, fl_ctx: FLContext) -> Shareable:
        """
        Aggregates the results from all accepted client sites and produces a global result.

        This is where the global aggregation logic happens. Developers can override this
        if they need to change how the results from each site are combined.

        :param fl_ctx: The federated learning context for this run.
        :return: A Shareable object containing the aggregated global result.
        """
        # Retrieve the computation parameters (e.g., covariates) for the aggregation
        covariates_headers = fl_ctx.get_prop("COMPUTATION_PARAMETERS")["Covariates"]

        # Create a new Shareable to store the aggregated result
        outgoing_shareable = Shareable()
        outgoing_shareable["result"] = calculate_global_values(self.site_results, covariates_headers)
        return outgoing_shareable
