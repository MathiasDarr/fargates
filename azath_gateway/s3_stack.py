from aws_cdk import (
    # Duration,
    Stack,
    aws_iam as iam,
    aws_apigateway as gateway,
    RemovalPolicy,
    aws_s3 as s3,
    # aws_sqs as sqs,
    aws_logs as logs,
    aws_s3_deployment
)
from resources.apiGateway.policy_statements import getPolicyDocument
from aws_cdk.aws_apigateway import RestApi, StageOptions, EndpointType, MethodResponse
from resources.apiGateway.gateway import getOrigins
from constructs import Construct


class S3Stack(Stack):

    def create_bucket(self, bucket_name):
        bucket = s3.Bucket(self,
                           bucket_name,
                           bucket_name=bucket_name,
                           removal_policy=RemovalPolicy.DESTROY
                           )
        return bucket

    def create_role(self, rolename:str, bucket: s3.IBucket=None):
        s3_read_policy = iam.ManagedPolicy.from_managed_policy_arn(self, id="s3-role",managed_policy_arn='arn:aws:iam::aws:policy/AmazonS3FullAccess')

        role = iam.Role(
            self,"S3-demidrek",
            role_name=rolename,
            assumed_by=iam.ServicePrincipal('apigateway.amazonaws.com'),
            managed_policies=[s3_read_policy]
        )
        return role

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        bucket_name = "demidrek-site"
        bucket = s3.Bucket(self,
                           bucket_name,
                           bucket_name=bucket_name,
                           removal_policy=RemovalPolicy.DESTROY,
                           website_index_document='index.html',
                           public_read_access=False
                           )


        log_group = logs.LogGroup(self, "demidrek-ap-logs")

        api = gateway.RestApi(
            self,
            "demidrek-api",
            rest_api_name="demidrek-api",
            description="API",
            deploy=True,
            deploy_options=gateway.StageOptions(
                access_log_destination=gateway.LogGroupLogDestination(log_group),
                access_log_format=gateway.AccessLogFormat.clf()
            ),
            binary_media_types=["*/*"]

        )
        role = self.create_role("demidrek-role")

        # root_integration = gateway.AwsIntegration(
        #     service="s3",
        #     integration_http_method="GET",
        #     path=bucket_name + "/index.html",
        # )


        proxy_integration = gateway.AwsIntegration(
            service="s3",
            integration_http_method="GET",
            path=bucket_name+"/{folder}/{key}",
            proxy=False,
            options=gateway.IntegrationOptions(
                credentials_role=role,
                integration_responses=[
                    gateway.IntegrationResponse(
                        status_code="200",
                        # response_parameters={"method.response.header.Content-Type": "integration.response.header.Content-Type"}
                    response_parameters = {
             "integration.response.header.Content-Type": "method.response.header.Content-Type"}
                    )
                ],
                request_parameters={
                    "integration.request.path.folder": "method.request.path.folder",
                    "integration.request.path.key": "method.request.path.key",
                }
            ),
        )
        #
        # root_method = api.root.add_method("GET",
        #                                   root_integration
        #                                   )

        aws_s3_deployment.BucketDeployment(self,
                                           "demidrek-deployment",
                                           destination_bucket=bucket,
                                           sources=[aws_s3_deployment.Source.asset('./dist')])
        api.root.add_resource("{folder}") \
            .add_resource("{key}") \
            .add_method(http_method="GET",
                        integration=proxy_integration,
                        method_responses=[
                            {
                                "statusCode": "200",
                                "method.response.header.Content-Type": "text/html;"
                            }
                        ],
                        request_parameters={
                            "method.request.path.folder": True,
                            "method.request.path.key": True,
                            "method.request.header.Content-Type": True,
                        }
                    )