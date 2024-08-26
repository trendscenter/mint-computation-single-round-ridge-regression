import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
import statsmodels.api as sm
from typing import List, Dict, Any

def perform_ridge_regression(covariates_path: str, data_path: str, covariates_headers: List[str], data_headers: List[str]) -> Dict[str, Dict[str, Any]]:
    # Load data
    covariates = pd.read_csv(covariates_path)
    data = pd.read_csv(data_path)

    # Filter data using the specified headers
    covariates = covariates[covariates_headers]
    data = data[data_headers]

    # Standardize covariates
    scaler = StandardScaler()
    X = scaler.fit_transform(covariates)
    X = sm.add_constant(X)  # Add intercept

    # Initialize results storage
    results = {}

    # Include intercept in the headers for labeling
    covariate_labels = ['Intercept'] + covariates_headers

    # Loop through each dependent variable in data.csv
    for dependent_var in data.columns:
        y = data[dependent_var]

        # Fit Ridge regression model
        ridge_model = Ridge(alpha=1.0)
        ridge_model.fit(X, y)
        coefficients = ridge_model.coef_

        # Fit OLS model for statistical metrics
        ols_model = sm.OLS(y, X).fit()

        # Extract statistics
        t_stats = ols_model.tvalues
        p_values = ols_model.pvalues
        r_squared = ols_model.rsquared
        degrees_of_freedom = ols_model.df_resid
        sse = np.sum((y - ridge_model.predict(X)) ** 2)

        # Store results with proper labeling of variables
        results[dependent_var] = {
            "Variables": covariate_labels,
            "Coefficients": coefficients.tolist(),
            "t-Statistics": t_stats.tolist(),
            "P-Values": p_values.tolist(),
            "R-Squared": r_squared,
            "Degrees of Freedom": degrees_of_freedom,
            "Sum of Squared Errors": sse
        }

    return results
