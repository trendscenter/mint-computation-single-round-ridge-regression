import numpy as np
from sklearn.linear_model import Ridge
import statsmodels.api as sm

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