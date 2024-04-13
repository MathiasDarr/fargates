#!/usr/bin/env python3
import os

import aws_cdk as cdk

from azath_gateway.gateway_ecs.infrastructure import InfrastructureStack
from azath_gateway.gateway_ecs.service import ServiceStack
from azath_gateway.load_balanced_stack.lb_stack import LBStack
account = os.getenv('AWS_ACCOUNT')
region = "us-west-2"

env = cdk.Environment()
if account and region:
    env = cdk.Environment(account=account, region=region)
app = cdk.App()
#
# AzathGatewayStack(app,
#                    "AzathGatewayStack",
#                   env=env
#      )


# DemidrekStack(app,
#         "DemidrekStack",
#         env=env)

# ProxyStack(app, "ProxyStack")
#LBStack(app, "LBStack", env=env)

#StaticStack(app, "StaticStack", env=env)
# ApiStack(app, "ApiStack", env=env)
LBStack(app, "LoadBalancerStack", env=env)

# InfrastructureStack(app, "ServiceDiscoveryStack", env=env)
# ServiceStack(app, "DassemServiceStack", env=env)
app.synth()
