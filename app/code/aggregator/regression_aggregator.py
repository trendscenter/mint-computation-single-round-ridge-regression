from typing import List, Dict, Any
from nvflare.apis.shareable import Shareable
from nvflare.apis.fl_context import FLContext
from nvflare.app_common.abstract.aggregator import Aggregator
from nvflare.apis.fl_constant import ReservedKey

class RegressionAggregator(Aggregator):
    def __init__(self):
        super().__init__()
        self.site_results: List[Dict[str, Any]] = []

    def accept(self, site_result: Shareable, fl_ctx: FLContext) -> bool:
        """
        Accepts a result from a site and stores it for aggregation.
        """
        self.site_results.append(site_result)
        return True

    def aggregate(self) -> Shareable:
        """
        Aggregates the results from all sites.
        """
        if not self.site_results:
            raise ValueError("No site results to aggregate")

        # Example: Averaging coefficients, p-values, etc.
        num_sites = len(self.site_results)
        combined_result = Shareable()
        
        # Aggregating coefficients, p-values, etc.
        combined_result["coefficients"] = self._average_across_sites("coefficients")
        combined_result["p_values"] = self._average_across_sites("p_values")
        combined_result["r_squared"] = self._average_across_sites("r_squared")
        combined_result["adjusted_r_squared"] = self._average_across_sites("adjusted_r_squared")

        return combined_result

    def _average_across_sites(self, key: str) -> List[float]:
        """
        Helper function to average a list of numerical results across sites.
        """
        num_sites = len(self.site_results)
        aggregated = [0] * len(self.site_results[0][key])
        
        for result in self.site_results:
            for i, value in enumerate(result[key]):
                aggregated[i] += value

        return [x / num_sites for x in aggregated]
