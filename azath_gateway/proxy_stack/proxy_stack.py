from aws_cdk import (
    # Duration,
    Stack,
    aws_iam as iam,
    aws_apigateway as gateway,
    aws_s3 as s3
    # aws_sqs as sqs,
)
from resources.apiGateway.policy_statements import getPolicyDocument
from aws_cdk.aws_apigateway import RestApi, StageOptions, EndpointType, MethodResponse
from resources.apiGateway.gateway import getOrigins
from constructs import Construct


class ProxyStack(Stack):

    def create_bucket(self, bucket_name):
        bucket = s3.Bucket(self, bucket_name, bucket_name=bucket_name)
        return bucket

    def create_role(self, rolename, bucket: s3.IBucket):
        s3_read_policy = iam.ManagedPolicy.from_managed_policy_arn(self, id="s3-role",managed_policy_arn='arn:aws:iam::aws:policy/AmazonS3FullAccess')

        role = iam.Role(
            self,
            rolename,
            role_name=rolename,
            assumed_by=iam.ServicePrincipal('apigateway.amazonaws.com'),
            managed_policies=[s3_read_policy]
        )

        role.add_to_policy(
            iam.PolicyStatement(
                resources=[bucket.bucket_arn],
                actions=["s3:*"]
            )
        )

        role.assume_role_policy.add_statements(
            iam.PolicyStatement(
                actions=["sts:AssumeRole"],
                effect=iam.Effect.ALLOW,
                principals=[
                    iam.ServicePrincipal('s3.amazonaws.com'),
                    iam.ServicePrincipal('apigateway.amazonaws.com')
                ]
            )
        )

        return role

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        env = 'development'
        name = 'dakobed-proxy'
        appname = f'{env}-{name}'
        policy = getPolicyDocument()
        bucket_name = "dako-s3-assets"
        bucket = self.create_bucket(bucket_name)
        role = self.create_role('AzathProxyRole', bucket)
        s3_integration = gateway.AwsIntegration(
            service="s3",
            integration_http_method="GET",
            path=bucket_name + "/{folder}/{key}",
            proxy=False,
            options=gateway.IntegrationOptions(
                credentials_role=role,
                integration_responses=[
                    {'statusCode': "200", "responseParmaters": {"method.response.header.Content-Type": True}}],
                request_parameters={
                    "integration.request.path.folder": "method.request.path.folder",
                    "integration.request.path.key": "method.request.path.key",
                }
            )
            # options=gateway.IntegrationOptions(credentials_role=role, integration_responses=[{'status_code':200}])
        )

        api = gateway.RestApi(self, "dako-api", rest_api_name="dako-api", binary_media_types=["/*"])
        api.root.add_method("ANY", gateway.MockIntegration(
            integration_responses=[gateway.IntegrationResponse(status_code="200")
                                   ],
            passthrough_behavior=gateway.PassthroughBehavior.NEVER,
            request_templates={
                "application/json": "{ 'statusCode': 200 }"
            }
        ),
                            method_responses=[MethodResponse(status_code="200")
                                              ],

                            )
        # method = gateway.Method(
        #     self,
        #     "gateway-model",
        #     http_method="GET",
        #     integration=s3_integration,
        #     options=gateway.MethodOptions(
        #         method_responses=[
        #             {
        #                 "statusCode": "200",
        #                 "method.response.header.Content-Type": True
        #             }
        #         ],
        #         request_parameters={
        #             "method.response.path.folder": True,
        #             "method.request.path.key": True,
        #             "method.request.header.Content-Type": True,
        #         }
        #     ))

        api.root.add_resource("assets") \
            .add_resource("{folder}") \
            .add_resource("{key}") \
            .add_method(http_method="GET",
                        integration=s3_integration,
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
            # # "GET",
            # # s3_integration,
            # gateway.MethodOptions(
            #     method_responses=[
            #         {
            #             "statusCode": "200",
            #             "method.response.header.Content-Type": True
            #         }
            #     ],
            #     request_parameters={
            #         "method.response.path.folder": True,
            #         "method.request.path.key": True,
            #         "method.request.header.Content-Type": True,
            #     }
            # ))
