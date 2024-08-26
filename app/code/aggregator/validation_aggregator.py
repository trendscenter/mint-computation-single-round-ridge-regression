from typing import List, Dict, Any
from nvflare.apis.shareable import Shareable
from nvflare.apis.fl_context import FLContext
from nvflare.app_common.abstract.aggregator import Aggregator
from nvflare.apis.fl_constant import ReservedKey

class ValidationAggregator(Aggregator):
    def __init__(self):
        super().__init__()
        self.site_results: Dict[str, Dict[str, Any]] = {}

    def accept(self, site_result: Shareable, fl_ctx: FLContext) -> bool:
        """
        Accepts a validation result from a site and stores it for aggregation.
        """
        print("\n\n")
        print("ValidationAggregator: Accepting site result")
        print(site_result)
        print("\n\n")
        
        site_name = site_result.get_peer_prop(
            key=ReservedKey.IDENTITY_NAME, default=None)
        
        # Store the site result in a dictionary where the key is the site_name
        self.site_results[site_name] = {
            "is_valid": site_result.get("is_valid", False),
            "error_message": site_result.get("error_message")
        }
        
        return True

    def aggregate(self) -> Shareable:
        """
        Aggregates the validation results from all sites into a Shareable object where
        each site name is a key. Also includes an overall is_valid status.
        """
        if not self.site_results:
            raise ValueError("No validation results to aggregate")

 
        # Determine overall validation status
        
      
        validation_report = {}
        is_valid = all(result["is_valid"] for result in self.site_results.values())
        validation_report["is_valid"] = is_valid

        for site_name, result in self.site_results.items():
            validation_report[site_name] = {
                "is_valid": result["is_valid"],
                "error_message": result["error_message"],
            }
        
        output = Shareable()
        output["validation_report"] = validation_report    
        
        return output
