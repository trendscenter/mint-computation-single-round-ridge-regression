from typing import List, Dict, Any
from nvflare.apis.shareable import Shareable
from nvflare.apis.fl_context import FLContext
from nvflare.app_common.abstract.aggregator import Aggregator
from nvflare.apis.fl_constant import ReservedKey

class ValidationAggregator(Aggregator):
    def __init__(self):
        super().__init__()
        self.site_results: List[Dict[str, Any]] = []

    def accept(self, site_result: Shareable, fl_ctx: FLContext) -> bool:
        """
        Accepts a validation result from a site and stores it for aggregation.
        """
        print("\n\n")
        print("ValidationAggregator: Accepting site result")
        print(site_result)
        print("\n\n")
        self.site_results.append(site_result)
        return True

    def aggregate(self) -> Shareable:
        """
        Aggregates the validation results from all sites.
        """
        if not self.site_results:
            raise ValueError("No validation results to aggregate")

        combined_result = Shareable()

        # Aggregate validation statuses
        is_valid = all(site_result.get("is_valid", False) for site_result in self.site_results)
        combined_result["is_valid"] = is_valid

        # If not all are valid, collect error messages
        if not is_valid:
            combined_result["error_messages"] = self._collect_error_messages()

        return combined_result

    def _collect_error_messages(self) -> List[str]:
        """
        Helper function to collect error messages from all sites that failed validation.
        """
        error_messages = []
        for result in self.site_results:
            if not result.get("is_valid", False):
                error_message = result.get("error_message", "Unknown validation error")
                error_messages.append(error_message)
        return error_messages
