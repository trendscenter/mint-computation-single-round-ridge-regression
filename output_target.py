from typing import Dict, List, Union

# Define the output structure for site-specific results
SiteResult = Dict[str, Union[float, List[float]]]
# SiteResult Example:
# {
#   "coefficients": [0.12, -0.34, 0.56],  # List of coefficients for predictors
#   "p_values": [0.01, 0.05, 0.2],  # List of p-values for predictors
#   "r_squared": 0.85,  # R-squared value
#   "adjusted_r_squared": 0.83,  # Adjusted R-squared value
#   "residuals": [1.2, -0.8, 0.6, ...],  # List of residuals
# }

# Define the output structure for the combined results
CombinedResult = Dict[str, Union[float, List[float], Dict[str, List[float]]]]
# CombinedResult Example:
# {
#   "pooled_coefficients": [0.15, -0.29, 0.52],  # Combined coefficients
#   "pooled_p_values": [0.02, 0.04, 0.1],  # Combined p-values
#   "overall_r_squared": 0.87,  # Combined R-squared
#   "overall_adjusted_r_squared": 0.85,  # Combined Adjusted R-squared
#   "site_specific_results": {  # Nested dictionary with site-specific results
#       "site1": SiteResult,
#       "site2": SiteResult,
#       ...
#   }
# }

# The final output type combining both site-specific and combined results
RegressionOutput = Dict[str, Union[SiteResult, CombinedResult]]
# RegressionOutput Example:
# {
#   "site_results": {
#       "site1": SiteResult,
#       "site2": SiteResult,
#       ...
#   },
#   "combined_result": CombinedResult
# }
