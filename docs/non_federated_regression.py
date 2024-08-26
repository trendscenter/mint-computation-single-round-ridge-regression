import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
import statsmodels.api as sm
import os
import json

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

        # Store the results, including the input and target data for global calculations
        results[dependent_var] = {
            "Coefficients": coefficients.tolist(),
            "t-Statistics": t_stats.tolist(),
            "P-Values": p_values.tolist(),
            "R-Squared": r_squared,
            "Degrees of Freedom": degrees_of_freedom,
            "Sum of Squared Errors": sse,
            "Input Data": X,
            "Target Data": y
        }

    return results

def calculate_global_values(site_results):
    global_results = {}
    
    for dependent_var in site_results[next(iter(site_results))].keys():
        combined_X = []
        combined_y = []

        for site, results in site_results.items():
            stats = results[dependent_var]

            # Append the input data (X) and target data (y) from each site
            combined_X.append(stats["Input Data"])
            combined_y.extend(stats["Target Data"])

        combined_X = np.vstack(combined_X)
        combined_y = np.array(combined_y)

        if combined_X.shape[0] != combined_y.shape[0]:
            raise ValueError(f"Inconsistent data lengths for {dependent_var}: X shape {combined_X.shape[0]}, y length {combined_y.shape[0]}")

        # Fit Ridge regression model
        ridge_model = Ridge(alpha=1.0)
        ridge_model.fit(combined_X, combined_y)
        coefficients = ridge_model.coef_

        # Fit OLS model for statistical metrics
        ols_model = sm.OLS(combined_y, combined_X).fit()

        # Extract statistics
        t_stats = ols_model.tvalues
        p_values = ols_model.pvalues
        r_squared = ols_model.rsquared
        degrees_of_freedom = ols_model.df_resid
        sse = np.sum((combined_y - ridge_model.predict(combined_X)) ** 2)

        # Store the global results
        global_results[dependent_var] = {
            "Coefficients": coefficients.tolist(),
            "t-Statistics": t_stats.tolist(),
            "P-Values": p_values.tolist(),
            "R-Squared": r_squared,
            "Degrees of Freedom": degrees_of_freedom,
            "Sum of Squared Errors": sse
        }

    return global_results

def save_results_to_json(global_results, site_results):
    # Save global results
    with open('global_results.json', 'w') as f:
        json.dump(global_results, f, indent=4)
    
    # Save local results for each site
    for site_id, results in site_results.items():
        with open(f'{site_id}_results.json', 'w') as f:
            # Remove Input Data and Target Data from results before saving
            clean_results = {k: {key: val for key, val in v.items() if key not in ["Input Data", "Target Data"]} for k, v in results.items()}
            json.dump(clean_results, f, indent=4)

# Example usage for multiple sites
sites = ['site1', 'site2']
site_results = {}

for site in sites:
    covariates_path = os.path.join(f'./test_data/{site}/covariates.csv')
    data_path = os.path.join(f'./test_data/{site}/data.csv')
    site_results[site] = perform_ridge_regression(covariates_path, data_path)

# Calculate global values
global_results = calculate_global_values(site_results)

# Save the results
save_results_to_json(global_results, site_results)
