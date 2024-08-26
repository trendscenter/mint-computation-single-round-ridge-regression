import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
import statsmodels.api as sm
import os

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
            "Coefficients": coefficients,
            "t-Statistics": t_stats,
            "P-Values": p_values,
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
            "Coefficients": coefficients,
            "t-Statistics": t_stats,
            "P-Values": p_values,
            "R-Squared": r_squared,
            "Degrees of Freedom": degrees_of_freedom,
            "Sum of Squared Errors": sse
        }

    return global_results

def print_results(site_results, global_results):
    print("Results")

    for dependent_var in global_results.keys():
        print(f"\n{dependent_var}")
        
        # Print Globals
        print("Globals")
        print("const\tMDD\tAge\tSex\tICV")
        globals_stats = global_results[dependent_var]
        print(f"Coefficient\t{globals_stats['Coefficients'][0]}\t{globals_stats['Coefficients'][1]}\t{globals_stats['Coefficients'][2]}\t{globals_stats['Coefficients'][3]}\t{globals_stats['Coefficients'][4]}")
        print(f"t Stat\t{globals_stats['t-Statistics'][0]}\t{globals_stats['t-Statistics'][1]}\t{globals_stats['t-Statistics'][2]}\t{globals_stats['t-Statistics'][3]}\t{globals_stats['t-Statistics'][4]}")
        print(f"P-value\t{globals_stats['P-Values'][0]}\t{globals_stats['P-Values'][1]}\t{globals_stats['P-Values'][2]}\t{globals_stats['P-Values'][3]}\t{globals_stats['P-Values'][4]}")
        print(f"R Squared\t{globals_stats['R-Squared']}")
        print(f"Degrees of Freedom\t{globals_stats['Degrees of Freedom']}")

        # Print per site results
        for site, site_stats in site_results.items():
            print(f"\n{site}")
            print("const\tMDD\tAge\tSex\tICV")
            site_dependent_stats = site_stats[dependent_var]
            print(f"Coefficient\t{site_dependent_stats['Coefficients'][0]}\t{site_dependent_stats['Coefficients'][1]}\t{site_dependent_stats['Coefficients'][2]}\t{site_dependent_stats['Coefficients'][3]}\t{site_dependent_stats['Coefficients'][4]}")
            print(f"t Stat\t{site_dependent_stats['t-Statistics'][0]}\t{site_dependent_stats['t-Statistics'][1]}\t{site_dependent_stats['t-Statistics'][2]}\t{site_dependent_stats['t-Statistics'][3]}\t{site_dependent_stats['t-Statistics'][4]}")
            print(f"P-value\t{site_dependent_stats['P-Values'][0]}\t{site_dependent_stats['P-Values'][1]}\t{site_dependent_stats['P-Values'][2]}\t{site_dependent_stats['P-Values'][3]}\t{site_dependent_stats['P-Values'][4]}")
            print(f"Sum Square of Errors\t{site_dependent_stats['Sum of Squared Errors']}")
            print(f"R Squared\t{site_dependent_stats['R-Squared']}")

# Example usage for multiple sites
sites = ['site1', 'site2']
site_results = {}

for site in sites:
    covariates_path = os.path.join(f'./test_data/{site}/covariates.csv')
    data_path = os.path.join(f'./test_data/{site}/data.csv')
    site_results[site] = perform_ridge_regression(covariates_path, data_path)

# Calculate global values
global_results = calculate_global_values(site_results)

# Print all results in the requested format
print_results(site_results, global_results)
