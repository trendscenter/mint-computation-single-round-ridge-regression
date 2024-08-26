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
        html_content += "<tr><th>Metric</th>"
        for variable in values["Variables"]:
            html_content += f"<th>{variable}</th>"
        html_content += "</tr>"
        
        # Add rows for Coefficients, t-Statistics, and P-Values
        html_content += "<tr><td>Coefficient</td>"
        for coef in values["Coefficients"]:
            html_content += f"<td>{coef:.4f}</td>"
        html_content += "</tr>"

        html_content += "<tr><td>t Stat</td>"
        for t_stat in values["t-Statistics"]:
            html_content += f"<td>{t_stat:.4f}</td>"
        html_content += "</tr>"

        html_content += "<tr><td>P-value</td>"
        for p_val in values["P-Values"]:
            html_content += f"<td>{p_val:.4e}</td>"
        html_content += "</tr>"
        
        # Add rows for R-Squared, Degrees of Freedom, Sum of Squared Errors
        html_content += f"""
        <tr>
            <td>R-Squared</td>
            <td colspan="{len(values['Variables'])}">{values['R-Squared']:.4f}</td>
        </tr>
        <tr>
            <td>Degrees of Freedom</td>
            <td colspan="{len(values['Variables'])}">{values['Degrees of Freedom']:.0f}</td>
        </tr>
        <tr>
            <td>Sum of Squared Errors</td>
            <td colspan="{len(values['Variables'])}">{values['Sum of Squared Errors']:.2f}</td>
        </tr>
        """
        
        html_content += "</table>\n"

    # HTML footer
    html_content += """
    </body>
    </html>
    """

    return html_content
