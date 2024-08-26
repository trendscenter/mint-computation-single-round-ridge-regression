import json

def json_to_html_results(json_data, table_name="Regression Results"):
    # HTML header
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{table_name}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
            }}
            th, td {{
                border: 1px solid #dddddd;
                text-align: left;
                padding: 8px;
            }}
            th {{
                background-color: #f2f2f2;
            }}
            h2 {{
                text-align: center;
            }}
        </style>
    </head>
    <body>
    <h1>{table_name}</h1>
    """

    # Process each entry in the JSON
    for key, values in json_data.items():
        html_content += f"<h2>{key}</h2>\n"
        html_content += "<table>\n"
        
        # Table headers
        html_content += """
        <tr>
            <th>Metric</th>
            <th>Coefficient</th>
            <th>t-Statistic</th>
            <th>P-Value</th>
        </tr>
        """
        
        # Add rows for Coefficients, t-Statistics, and P-Values
        for i in range(len(values["Coefficients"])):
            html_content += f"""
            <tr>
                <td>Variable {i + 1}</td>
                <td>{values['Coefficients'][i]:.4f}</td>
                <td>{values['t-Statistics'][i]:.4f}</td>
                <td>{values['P-Values'][i]:.4e}</td>
            </tr>
            """
        
        # Add rows for R-Squared, Degrees of Freedom, Sum of Squared Errors
        html_content += f"""
        <tr>
            <td>R-Squared</td>
            <td colspan="3">{values['R-Squared']:.4f}</td>
        </tr>
        <tr>
            <td>Degrees of Freedom</td>
            <td colspan="3">{values['Degrees of Freedom']:.0f}</td>
        </tr>
        <tr>
            <td>Sum of Squared Errors</td>
            <td colspan="3">{values['Sum of Squared Errors']:.2f}</td>
        </tr>
        """
        
        html_content += "</table>\n"

    # HTML footer
    html_content += """
    </body>
    </html>
    """

    return html_content
