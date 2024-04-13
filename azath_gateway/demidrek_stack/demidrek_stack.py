from aws_cdk import (
    aws_ecr as ecr,
    Stack,
    aws_iam as iam,
    aws_s3 as s3,
    aws_apigateway as gateway,
    RemovalPolicy,
    aws_logs as logs,
    aws_s3_deployment
)

from constructs import Construct


class DemidrekStack(Stack):

    def create_bucket(self, bucket_name):
        bucket = s3.Bucket(self,
                           bucket_name,
                           bucket_name=bucket_name,
                           block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
                           removal_policy=RemovalPolicy.DESTROY,
                           )
        return bucket


    def create_role(self, envname, application_name, bucket: s3.Bucket):
        role = iam.Role(
            self,
            f"{application_name}-s3-{envname}-role",
            role_name="DemidrekRole",
            assumed_by=iam.ServicePrincipal('apigateway.amazonaws.com'),

        )

        role.add_to_policy(
            iam.PolicyStatement(resources=[bucket.bucket_arn, bucket.bucket_arn + "/*"], actions=["s3:*"])
        )

        return role

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        # envname = config.get('environment_name')
        application_name = 'demidrek-heyward'
        envname = 'development'
        # log_group = logs.LogGroup(self, "ferc-api-logs-gateway")

        api = gateway.RestApi(
            self,
            f'{application_name}-{envname}-api-cdk',
            rest_api_name=f'{application_name}-api-cdk',
            description="API",
            deploy=True,
            # deploy_options=gateway.StageOptions(
            #     access_log_destination=gateway.LogGroupLogDestination(log_group),
            #     access_log_format=gateway.AccessLogFormat.clf()
            # ),
            binary_media_types=["*"]
        )
        bucket_name = f'{application_name}-{envname}-static-site-bucket'
        bucket = self.create_bucket(bucket_name)

        role = self.create_role(envname, application_name,bucket)
        s3_integration = gateway.AwsIntegration(
            service="s3",
            integration_http_method="GET",
            # path=bucket_name+"/{folder}/{key}",
            path = bucket_name + "/index.html",
            proxy=False,

            options=gateway.IntegrationOptions(
                credentials_role=role,
                integration_responses=[
                    gateway.IntegrationResponse(
                        status_code="200",
                        response_parameters=
                        {
                            "method.response.header.Content-Type":"integration.response.header.Content-Type"
                        }
                    )
                ]
            )
        )

        proxy_integration = gateway.AwsIntegration(
            service="s3",
            path=bucket_name + "/{proxy}",
            integration_http_method = "GET",
            proxy = False,
            options = gateway.IntegrationOptions(
                credentials_role=role,
                integration_responses=[
                    gateway.IntegrationResponse(
                        status_code="200",
                        response_parameters=
                        {
                            "method.response.header.Content-Type": "integration.response.header.Content-Type"
                        }

                    ),
                ],
                request_parameters={
                    "integration.request.path.proxy": "method.request.path.proxy",

                }
        )
        )

        root_method = api.root.add_method(
            "GET",
            s3_integration,
            request_parameters={
                "method.request.header.Content-Type": True
            },
            method_responses=[
                gateway.MethodResponse(status_code="200", response_parameters={"method.response.header.Content-Type": True})
            ]
        )

        api.root.add_resource('{proxy+}')\
            .add_method("GET",
                        proxy_integration,
                        request_parameters={
                            "method.request.header.Content-Type": True,
                            "method.request.path.proxy": True,
                        },
                        method_responses=[
                            gateway.MethodResponse(status_code="200",
                                                   response_parameters={"method.response.header.Content-Type": True})
                        ])
        aws_s3_deployment.BucketDeployment(self,
                                           "demidrek-deployment",
                                           destination_bucket=bucket,
                                           sources=[aws_s3_deployment.Source.asset('./dist')])