from nvflare.apis.shareable import Shareable
from nvflare.apis.fl_context import FLContext
from nvflare.app_common.abstract.aggregator import Aggregator
from nvflare.apis.fl_constant import ReservedKey
import numpy as np

class RidgeRegressionAggregator(Aggregator):
    def __init__(self):
        super().__init__()
        self.stored_weights = {}

    def accept(self, shareable: Shareable, fl_ctx: FLContext) -> bool:
        current_round = fl_ctx.get_prop("CURRENT_ROUND", default=None)
        contributor_name = shareable.get_peer_prop(ReservedKey.IDENTITY_NAME, default=None)

        if current_round is None or contributor_name is None:
            print("Warning: Invalid round or contributor information.")
            return False

        if current_round not in self.stored_weights:
            self.stored_weights[current_round] = {}

        weights = shareable.get("weights", None)
        if weights is None:
            print(f"Warning: Received no weights from {contributor_name} for round {current_round}.")
            return False

        self.stored_weights[current_round][contributor_name] = weights
        print(f"Accepted weights from {contributor_name} for round {current_round}.")
        return True

    def aggregate(self, fl_ctx: FLContext) -> Shareable:
        current_round = fl_ctx.get_prop("CURRENT_ROUND")
        if current_round not in self.stored_weights:
            print("Error: No data available for aggregation.")
            return Shareable()

        round_weights = self.stored_weights[current_round]
        all_weights = np.array(list(round_weights.values()))

        if all_weights.size == 0:
            print("Error: No valid weights to aggregate.")
            return Shareable()

        aggregated_weights = np.mean(all_weights, axis=0)
        result_shareable = Shareable()
        result_shareable["global_model"] = {"weights": aggregated_weights.tolist()}
        print(f"Aggregated global model for round {current_round}.")
        return result_shareable
