from aws_cdk.aws_apigateway import RestApi, StageOptions, EndpointType, Model, IResource, MockIntegration, PassthroughBehavior
from resources.apiGateway.gateway import getOrigins
from azath_gateway.gateway_stack.s3 import getS3Integration
def getRestAPI(construct, api_name, policy):
    origins = getOrigins()


    api = RestApi(
        construct,
        api_name,
        rest_api_name=api_name,
        description="API created with CDK",
        policy=policy,
        deploy=True,
        deploy_options=StageOptions(stage_name="main", variables={}),
        retain_deployments=True,
        endpoint_types=[EndpointType.REGIONAL]
    )

    return api
