def regression(fl_ctx, shareable):
    computation_parameters = fl_ctx.get_peer_context().get_prop("COMPUTATION_PARAMETERS")

    input_list = shareable.get('result')
    cache_list = shareable.get('cache')

    X = pd.read_json(cache_list["covariates"], orient='split')
    y = pd.read_json(cache_list["dependents"], orient='split')

    biased_X = sm.add_constant(X.values)

    t = local_stats_to_dict_fsl(X, y)

    avg_beta_vector = input_list['input']["avg_beta_vector"]
    mean_y_global = input_list['input']["mean_y_global"]

    SSE_local, SST_local, varX_matrix_local = [], [], []

    printAndAddToLogs(f"- Crunching SSE_local, SST_local, varX_matrix_local") 

    for index, column in enumerate(y.columns):
        curr_y = y[column]

        X_, y_ = ignore_nans(biased_X, curr_y)

        SSE_local.append(sum_squared_error(X_, y_, avg_beta_vector[index]))
        SST_local.append(
            np.sum(np.square(np.subtract(y_, mean_y_global[index]))))

        varX_matrix_local.append(np.dot(X_.T, X_).tolist())

    output_dict = {
        "SSE_local": SSE_local,
        "SST_local": SST_local,
        "varX_matrix_local": varX_matrix_local,
    }

    cache_dict = {}

    printAndAddToLogs(f"Done crunching. sending back to remote...") 

    result = {"input": output_dict, "cache": cache_dict, "logs": logs}

    return result