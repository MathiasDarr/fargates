from aws_cdk import (
    Stack,
    CfnOutput
)
from constructs import Construct

from azath_gateway.utils import create_load_balancer, get_vpc, create_repository, create_cluster

class StaticStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        env = 'development'
        application_name = 'dakobed'

        vpc = get_vpc(self)
        # create_repository(self, application_name, "api")
        create_cluster(self,application_name, vpc)
        load_balancer = create_load_balancer(self, application_name, vpc=vpc, external=True)
        CfnOutput(self, 'load_balancer_arn', value=load_balancer.load_balancer_arn, export_name="loadbalancerarn")
        CfnOutput(self, 'load_balancer_dns', value=load_balancer.load_balancer_dns_name, export_name="lbdns")
