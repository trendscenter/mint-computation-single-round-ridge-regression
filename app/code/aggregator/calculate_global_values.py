import numpy as np

def calculate_global_values(site_results, covariates_headers):
    global_results = {}

    for dependent_var in site_results[next(iter(site_results))].keys():
        # Initialize accumulators for weighted averaging
        weighted_sum_coefficients = None
        weighted_sum_t_stats = None
        weighted_sum_p_values = None
        weighted_sum_r_squared = 0.0
        total_degrees_of_freedom = 0
        total_sse = 0.0
        total_subjects = 0

        for site, results in site_results.items():
            stats = results[dependent_var]
            n_subjects = stats["Degrees of Freedom"] + 1  # Degrees of Freedom + 1 to get the original number of subjects

            # Update the total number of subjects
            total_subjects += n_subjects

            # Weighted aggregation of coefficients
            if weighted_sum_coefficients is None:
                weighted_sum_coefficients = np.array(stats["Coefficients"]) * n_subjects
            else:
                weighted_sum_coefficients += np.array(stats["Coefficients"]) * n_subjects

            # Weighted aggregation of t-stats
            if weighted_sum_t_stats is None:
                weighted_sum_t_stats = np.array(stats["t-Statistics"]) * n_subjects
            else:
                weighted_sum_t_stats += np.array(stats["t-Statistics"]) * n_subjects

            # Weighted aggregation of p-values
            if weighted_sum_p_values is None:
                weighted_sum_p_values = np.array(stats["P-Values"]) * n_subjects
            else:
                weighted_sum_p_values += np.array(stats["P-Values"]) * n_subjects

            # Weighted sum of R-squared
            weighted_sum_r_squared += stats["R-Squared"] * n_subjects

            # Sum degrees of freedom and SSE
            total_degrees_of_freedom += stats["Degrees of Freedom"]
            total_sse += stats["Sum of Squared Errors"]

        # Compute weighted averages
        avg_coefficients = weighted_sum_coefficients / total_subjects
        avg_t_stats = weighted_sum_t_stats / total_subjects
        avg_p_values = weighted_sum_p_values / total_subjects
        avg_r_squared = weighted_sum_r_squared / total_subjects

        # Store the aggregated global results
        global_results[dependent_var] = {
            "Variables": ['Intercept'] + covariates_headers,
            "Coefficients": avg_coefficients.tolist(),
            "t-Statistics": avg_t_stats.tolist(),
            "P-Values": avg_p_values.tolist(),
            "R-Squared": avg_r_squared,
            "Degrees of Freedom": total_degrees_of_freedom,
            "Sum of Squared Errors": total_sse
        }

    return global_results
