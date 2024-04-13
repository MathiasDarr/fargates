
from aws_cdk import (
    # Duration,
    Stack,
    aws_iam as iam,
    aws_apigateway as gateway,
    aws_s3 as s3,
    aws_ec2 as ec2,
    # aws_sqs as sqs,
aws_elasticloadbalancingv2 as lbv2,
)
def create_cluster(application_name):
    pass

def create_load_balancer(application_name, external):
    security_group = ec2.SecurityGroup.from_security_group_id(self,
                                                              f"{application_name}-sg",
                                                              f"{application_name}-sg",
                                                              al
                                                              )