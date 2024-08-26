from typing import Dict, Any
from nvflare.apis.shareable import Shareable
from nvflare.apis.fl_context import FLContext
from nvflare.app_common.abstract.aggregator import Aggregator
from nvflare.apis.fl_constant import ReservedKey
from .calculate_global_values import calculate_global_values

class SrrAggregator(Aggregator):
    def __init__(self):
        super().__init__()
        self.site_results: Dict[str, Dict[str, Any]] = {}  # Store results as a dictionary

    def accept(self, site_result: Shareable, fl_ctx: FLContext) -> bool:
        """
        Accepts a result from a site and stores it for aggregation.
        """
        site_name = site_result.get_peer_prop(
            key=ReservedKey.IDENTITY_NAME, default=None)
        
        self.site_results[site_name] = site_result["result"]
        return True

    def aggregate(self) -> Shareable:
        """
        Aggregates the results from all sites.
        """
        outgoing_shareable = Shareable()
        outgoing_shareable["result"] = calculate_global_values(self.site_results)
        return outgoing_shareable
