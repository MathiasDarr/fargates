from aws_cdk.aws_apigateway import AwsIntegration, ContentHandling, HttpIntegration, IResource, MockIntegration, PassthroughBehavior
import aws_cdk.aws_apigateway as gateway

def createMockIntegration(root: IResource):
    root.add_method("ANY", MockIntegration(
        integration_responses=[{'status_code':200}],
        passthrough_behavior=PassthroughBehavior.NEVER,
        request_templates={
            "application/json": '{ "statusCode": 200 }'
        },
    ),
    method_responses=[{"statusCode":200}]
    )

def getS3Integration(applicationName, bucket, role):
    return AwsIntegration(
        integration_http_method="GET",
        proxy=False,
        service="s3",
        path=f'{bucket}/html',
        options=gateway.IntegrationOptions(credentials_role=role)
    )
