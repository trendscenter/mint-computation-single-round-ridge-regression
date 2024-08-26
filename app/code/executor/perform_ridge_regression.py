import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
import statsmodels.api as sm

def perform_ridge_regression(covariates_path, data_path):
    # Load data
    covariates = pd.read_csv(covariates_path)
    data = pd.read_csv(data_path)

    # Standardize covariates
    scaler = StandardScaler()
    X = scaler.fit_transform(covariates)
    X = sm.add_constant(X)  # Add intercept

    # Initialize results storage
    results = {}

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

        # Store only the necessary derived results, without raw input/target data
        results[dependent_var] = {
            "Coefficients": coefficients.tolist(),
            "t-Statistics": t_stats.tolist(),
            "P-Values": p_values.tolist(),
            "R-Squared": r_squared,
            "Degrees of Freedom": degrees_of_freedom,
            "Sum of Squared Errors": sse
        }

    return results
