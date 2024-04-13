from aws_cdk import (
    aws_apigateway as gateway,
)


def create_mock_integration(root: gateway.IResource):
    root.add_method("ANY",
                    gateway.MockIntegration(integration_responses=[{"statusCode": 200}],
                                            passthrough_behavior=gateway.PassthroughBehavior.NEVER,
                                            request_templates={
                                                "application/json": ""
                                            }

                                            ),


                    )

    integration = gateway.MockIntegration()
from aws_cdk.aws_apigateway import IntegrationResponse, MethodResponse, IntegrationResponse, MethodResponse
import path as path
import aws_cdk.aws_lambda as lambda_
from aws_cdk import App, Stack
from aws_cdk.aws_apigateway import MockIntegration, PassthroughBehavior, RestApi, RequestAuthorizer, IdentitySource

# Against the RestApi endpoint from the stack output, run
# `curl -s -o /dev/null -w "%{http_code}" <url>` should return 401
# `curl -s -o /dev/null -w "%{http_code}" -H 'Authorization: deny' <url>?allow=yes` should return 403
# `curl -s -o /dev/null -w "%{http_code}" -H 'Authorization: allow' <url>?allow=yes` should return 200

app = App()
stack = Stack(app, "RequestAuthorizerInteg")

restapi.root.add_method("ANY", MockIntegration(
    integration_responses=[IntegrationResponse(status_code="200")
    ],
    passthrough_behavior=PassthroughBehavior.NEVER,
    request_templates={
        "application/json": "{ "statusCode": 200 }"
    }
),
    method_responses=[MethodResponse(status_code="200")
    ],
    authorizer=authorizer
)

restapi.root.resource_for_path("auth").add_method("ANY", MockIntegration(
    integration_responses=[IntegrationResponse(status_code="200")
    ],
    passthrough_behavior=PassthroughBehavior.NEVER,
    request_templates={
        "application/json": "{ "statusCode": 200 }"
    }
),
    method_responses=[MethodResponse(status_code="200")
    ],
    authorizer=second_authorizer
)