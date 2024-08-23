 def _run_site_task(self, task_name: str, site: str, shareable: dict) -> Union[SiteResult, None]:
      """
        Run the specified task on a site.
        """
       if task_name == "perform_regression":
            data_loader = SiteDataLoader()
            regressor = LocalRegressor()
            data = data_loader.load_site_data(site)
            site_result = regressor.fit_model(data)
            return site_result
        elif task_name == "save_results":
            output_generator = OutputGenerator()
            output_generator.save_output(
                shareable, f'{site}/local_regression_results.json')
            return None
        else:
            raise ValueError(f"Unknown task name: {task_name}")
