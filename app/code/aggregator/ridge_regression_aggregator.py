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

        if current_round is None:
            print("Warning: CURRENT_ROUND is None.")
            return False
        if contributor_name is None:
            print("Warning: contributor_name is None.")
            return False

        print(f"Received weights from {contributor_name} for round {current_round}.")

        if current_round not in self.stored_weights:
            self.stored_weights[current_round] = {}

        weights = shareable.get("weights", None)
        if weights is None:
            print(f"Warning: No weights found in the shareable from {contributor_name} for round {current_round}.")
            return False

        self.stored_weights[current_round][contributor_name] = weights
        print(f"Accepted weights from {contributor_name} for round {current_round}. Stored weights: {self.stored_weights}")
        return True

    def aggregate(self, fl_ctx: FLContext) -> Shareable:
        current_round = fl_ctx.get_prop("CURRENT_ROUND", default=None)
        if current_round is None:
            print("Error: CURRENT_ROUND is None during aggregation.")
            return Shareable()

        if current_round not in self.stored_weights:
            print(f"Error: No stored weights found for round {current_round}. Cannot aggregate.")
            return Shareable()

        round_weights = self.stored_weights[current_round]
        if not round_weights:
            print(f"Error: round_weights is empty for round {current_round}.")
            return Shareable()

        all_weights = np.array(list(round_weights.values()))

        if all_weights.size == 0:
            print(f"Error: all_weights array is empty for round {current_round}.")
            return Shareable()

        aggregated_weights = np.mean(all_weights, axis=0)
        result_shareable = Shareable()
        result_shareable["global_model"] = {"weights": aggregated_weights.tolist()}
        print(f"Aggregated global model for round {current_round}. Aggregated weights: {aggregated_weights}")
        return result_shareable
