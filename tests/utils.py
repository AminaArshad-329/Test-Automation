from azure.identity import ClientSecretCredential
from azure.synapse.artifacts import PipelineRunFilterParameters, PipelineRunQueryOrderBy, PipelineRunQueryFilter
from azure.synapse.artifacts import DataFactoryManagementClient
from datetime import datetime, timedelta
import os
import time

def get_synapse_client():
    azure_credentials = ClientSecretCredential(
        client_id=os.environ.get('client_id'),
        client_secret=os.environ.get('client_secret'),
        tenant_id=os.environ.get('tenant_id')
    ) 
    synapse_client = DataFactoryManagementClient(
        azure_credentials,
        os.environ.get('subscription_id')
    )
    return synapse_client

def run_synapse_pipeline(pipeline_name, parameters): 
    synapse_client = get_synapse_client()
    rg_name = os.environ.get('rg_name')
    factory_name = os.environ.get('factory_name')

    run_response = synapse_client.pipelines.create_run(
        rg_name,
        factory_name,
        pipeline_name,
        parameters=parameters
    )
    print(f"**Pipeline name: {pipeline_name}, Run id: {run_response.run_id}")

    return poll_for_completed_status(
        pipeline_name=pipeline_name,
        run_id=run_response.run_id,
        synapse_client=synapse_client
    ).status
   
def poll_for_completed_status(pipeline_name, run_id, synapse_client):
    rg_name = os.environ.get('rg_name')
    factory_name = os.environ.get('factory_name')
    
    print("[*] gathering data for pipeline '{0}' please wait ...".format(pipeline_name))
    run_in_progress = True
    test_start_time = time.process_time()
    
    while run_in_progress:
        pipeline_run = synapse_client.pipeline_runs.get(
            rg_name,
            factory_name,
            run_id
        )
        print("[*] [{0} minutes] [Pipeline '{1}' run status]: '{2}'".format(
            round(time.process_time()-test_start_time, 3),
            pipeline_name,
            pipeline_run.status
        ))
        if pipeline_run.status not in ['InProgress', 'Queued']:  
            run_in_progress = False
            print('Pipeline final run status: {0}'.format(pipeline_run.status))
            return pipeline_run
        time.sleep(2)

def get_most_recent_pipeline_run_details(pipeline_name):
    synapse_client = get_synapse_client()
    rg_name = os.environ.get('rg_name')
    factory_name = os.environ.get('factory_name')
    
    filters = [PipelineRunQueryFilter(
        operand='PipelineName',
        operator='Equals',
        values=[pipeline_name]
    )]
    order_by = [PipelineRunQueryOrderBy(
        order_by='RunStart',
        order = 'DESC'
    )]
    filter_params = PipelineRunFilterParameters(
        last_updated_after=datetime.now() - timedelta(minutes=1),
        last_updated_before=datetime.now() + timedelta(minutes=1),
        filters=filters,
        order_by=order_by
    )
    pipeline_runs = synapse_client.pipeline_runs.query_by_factory(
        resource_group_name=rg_name,
        factory_name=factory_name,
        filter_parameters=filter_params
    )

    if len(pipeline_runs.value) == 0:
        return None
    
    most_recent_pipeline_run = pipeline_runs.value[0]
    print(pipeline_runs.value[0])
    
    return poll_for_completed_status(
        pipeline_name=pipeline_name,
        run_id=most_recent_pipeline_run.run_id,
        synapse_client=synapse_client
    )
