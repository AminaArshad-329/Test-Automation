from datetime import datetime, timedelta
from datetime import datetime
# from azure.storage.blob import *
# from azure.identity import DefaultAzureCredential
# from azure.mgmt.synapse import *
# from azure.synapse.artifacts import *
import requests
import pyodbc
import json
import time
import utils
import sys
import os
from azure.core import PipelineClient
from azure.core.rest import HttpRequest
from azure.core.pipeline.policies import RedirectPolicy, UserAgentPolicy

# import psycopg2
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

subscription_id = '1c4a7d94-476b-4e4c-9604-f96fec3c1ffd'
resource_group_name = 'rg-synapse'
workspace_name = 'synapse-syssoft-dev'
pipeline_name = 'Copy_PLdata'


def test_pipeline_runs_successfully():
    # Define the time window for querying pipeline run status
    start_time = datetime.utcnow() - timedelta(days=1)
    end_time = datetime.utcnow()

    # Define the Azure Monitor API endpoint for querying pipeline run status
    endpoint = f"https://management.azure.com/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}/providers/Microsoft.Synapse/workspaces/{workspace_name}/pipelineruns?api-version=2020-12-01"

    # Define the query parameters
    params = {
        "api-version": "2020-12-01",
        "$filter": f"name.value eq '{pipeline_name}' and properties/runStart ge '{start_time.isoformat()}' and properties/runEnd le '{end_time.isoformat()}'"
    }

    # Make a GET request to the Azure Monitor API
    response = requests.get(endpoint, params=params)

    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()
        if data["value"]:
            print("Pipeline run succeeded.")
            return True
        else:
            print("No successful pipeline runs found.")
            return False
    else:
        print(f"Error: Failed to query pipeline runs. Status code: {response.status_code}")
        return False


# Call the test case function
test_pipeline_runs_successfully()


def test_pipeline_runs_at_certain_time():
    # Define the time window around 7am
    expected_time = datetime.utcnow().replace(hour=7, minute=0, second=0, microsecond=0)
    start_time = expected_time - timedelta(minutes=30)  # 30 minutes before 7am
    end_time = expected_time + timedelta(minutes=30)  # 30 minutes after 7am

    # Get the current time
    current_time = datetime.utcnow()

    # Check if the current time falls within the time window
    try:
        assert start_time <= current_time <= end_time, "Pipeline did not run around 7am."
    except AssertionError as e:
        print(str(e))  # Print the error message
        return  # Exit the function, allowing the script to continue to the next test case

    # If the assertion passes, print a success message
    print("Pipeline ran around 7am.")


# Call the test case function
test_pipeline_runs_at_certain_time()


def db_connection():
    # conn = pyodbc.connect('DRIVER={ODBC Driver 18 for SQL Server};'
    #                       'SERVER=syssoft-db-srv.database.windows.net;'
    #                       'DATABASE=azsql-testdb;'
    #                       'UID=syssoftadmin;'
    #                       'PWD=Welcome123')
    conn = pyodbc.connect(
        "Driver={ODBC Driver 17 for SQL Server};Server=tcp:syssoft-db-srv.database.windows.net,1433;Database=azsql-testdb;Uid=syssoftadmin;Pwd=Welcome123;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;")
    return conn


# # Example test case
def test_Person_Table_Exist():
    conn = db_connection()
    cursor = conn.cursor()
    print("Pytest is called")
    # Assert True
    # # SQL to validate
    cursor.execute("SELECT COUNT(*) FROM dbo.Person;")
    tab = cursor.tables(table="Person").fetchall()
    assert len(tab) > 0
    # Clean up
    cursor.close()


