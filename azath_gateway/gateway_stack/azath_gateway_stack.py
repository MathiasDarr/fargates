from aws_cdk import (
    # Duration,
    Stack,
    aws_iam as iam,
    aws_apigateway as gateway
    # aws_sqs as sqs,
)
from resources.apiGateway.policy_statements import getPolicyDocument
from aws_cdk.aws_apigateway import RestApi, StageOptions, EndpointType, MethodResponse
from resources.apiGateway.gateway import getOrigins
from constructs import Construct

from aws_cdk.aws_iam import PolicyStatement, Effect, AnyPrincipal, PolicyDocument





class AzathGatewayStack(Stack):

    def create_role(self, rolename):
        s3_read_policy = iam.ManagedPolicy.from_managed_policy_arn(self, id=rolename,managed_policy_arn='arn:aws:iam::aws:policy/AmazonS3FullAccess')

        role = iam.Role(
            self,
            "s3-dakobed-role",
            role_name="Azath",
            assumed_by=iam.ServicePrincipal('apigateway.amazonaws.com'),
            managed_policies=[s3_read_policy]
        )
        return role


    def getPolicyDocument(self):
        mainPolicy = PolicyStatement(effect=Effect.ALLOW, actions=["execute:Invoke"], principals=[AnyPrincipal()])
        return PolicyDocument(statements=[mainPolicy])

    #
    #     role.assume_role_policy.add_statements(iam.PolicyStatement(
    #         actions=["sts:AssumeRole"],
    #         effect=iam.Effect.ALLOW,
    #         principals=[
    #             iam.ServicePrincipal("s3.amazonaws.com"),
    #             iam.ServicePrincipal("apigateway.amazonaws.com")]
    #     ))
    #
    #
    #     return role
    # def _role(self):
    #     iam.Role(
    #         self,
    #         f"",
    #         role_name="lambda",
    #         assumed_by=iam.ServicePrincipal(api)
    #     )
    def getS3Integration(self):
        bucket = ''
        env = 'development'
        name = 'dakobed-api'
        appname = f'{env}-{name}'
        role = self.create_role(appname)
        return gateway.AwsIntegration(
            service="s3",
            path=f"{bucket}/index.html",
            proxy=False,
            options=gateway.IntegrationOptions(credentials_role=role)
            # options=gateway.IntegrationOptions(credentials_role=role, integration_responses=[{'status_code':200}])
        )
    def getS3ProxyIntegration(self):
        bucket_name = ''
        return gateway.HttpIntegration(

            f'https://{bucket_name}.s3-us-west-2.amazonaws.com/index.html?' + "?{proxy}",
            http_method="ANY",
            options=gateway.IntegrationOptions(
                request_parameters={"integration.request.path.proxy": "method.request.path.proxy"},
                cache_key_parameters=["method.request.path.proxy"]
            ),
            proxy=True
        )
    def getRestAPI(self, api_name, policy):

        api = RestApi(
            self,
            f'{api_name}-api',
            rest_api_name=f'{api_name}-api',
            description="API created with CDK",
            policy=policy,
            deploy=True,
            deploy_options=StageOptions(stage_name="main", variables={}),
            retain_deployments=True,
            endpoint_types=[EndpointType.REGIONAL]
        )

        return api



    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        env = 'development'
        name = 'dakobed-api'
        appname = f'{env}-{name}'
        policy = getPolicyDocument()
        api_name = "DakobedAPI"
        integration = self.getS3Integration()
        api = self.getRestAPI(appname, policy)

        api = RestApi(
            self,
            f'{api_name}-api',
            rest_api_name=f'{api_name}-api',
            description="API created with CDK",
            policy=policy,
            deploy=True,
            deploy_options=StageOptions(stage_name="main", variables={}),
            retain_deployments=True,
            endpoint_types=[EndpointType.REGIONAL]
        )


        # method_paramaters = {
        #     'methodResponses': [
        #         {
        #             "statusCode": 200,
        #             'responseModels': {
        #                 "text/html": gateway.Model.EMPTY_MODEL
        #             }
        #         }
        #     ]
        # }
        # method = api.root.add_method("GET", integration)
        # s3ProxyIntegration = self.getS3ProxyIntegration()
        #
        api.root.add_resource("{proxy+}").add_method("GET", s3ProxyIntegration,request_parameters={"method.request.path.proxy": True}, method_responses=[
            {
                "statusCode":"200",
                "requestParameters:": {
                    "method.response.header.Content-Type": True
                }
            }
        ])


        method.add_method_response(
            status_code="200",
            response_models={"text/html": gateway.Model.EMPTY_MODEL}
        )
        #
