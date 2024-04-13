from aws_cdk import (
    # Duration,
    Stack,
    aws_iam as iam,
    aws_apigateway as gateway
    # aws_sqs as sqs,
)
from resources.apiGateway.policy_statements import getPolicyDocument
from aws_cdk.aws_apigateway import RestApi, StageOptions, EndpointType, Model, IResource, MockIntegration, PassthroughBehavior
from resources.apiGateway.gateway import getOrigins
from constructs import Construct


def create_routes(api, application_name):
    hostingBucket = f'{application_name}-client-deployment'
    defaultS3Integration = u
