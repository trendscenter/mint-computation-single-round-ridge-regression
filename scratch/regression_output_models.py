from dataclasses import dataclass
from typing import List, Dict

@dataclass
class SiteResult:
    coefficients: List[float]
    p_values: List[float]
    r_squared: float
    adjusted_r_squared: float

@dataclass
class CombinedResult:
    pooled_coefficients: List[float]
    pooled_p_values: List[float]
    overall_r_squared: float
    overall_adjusted_r_squared: float
    site_specific_results: Dict[str, SiteResult]

@dataclass
class RegressionOutput:
    site_results: Dict[str, SiteResult]
    combined_result: CombinedResult
