from aws_cdk import (
    # Duration,
    Stack,
    aws_iam as iam,
    aws_apigateway as gateway,
    aws_s3 as s3,
    aws_ec2 as ec2,
    aws_ecr as ecr,
    aws_ecs as ecs,
    # aws_sqs as sqs,
    aws_elasticloadbalancingv2 as lbv2,
    CfnOutput
)

import json


def create_repository(scope, application_name, repo_name):
    ecr.Repository(scope,
                   f'{application_name}-{repo_name}-repo',
                   repository_name=f'{application_name}-{repo_name}-repo'
                   )


def create_cluster(scope, application_name, vpc):
    cluster = ecs.Cluster(scope,
                          f"{application_name}-cluster",
                          cluster_name=f"{application_name}-cluster",
                          vpc=vpc,
                          container_insights=True
                          )
    return cluster


def get_vpc(scope):
    vpc = ec2.Vpc.from_lookup(scope, "a", is_default=True)
    return vpc


def create_load_balancer(scope, application_name, vpc, external=False):
    security_group = ec2.SecurityGroup(
        scope,
        f"{application_name}-lb-sg",
        security_group_name=f"{application_name}-lb-sg",
        vpc=vpc
    )

    CfnOutput(scope, "sg_id", value=security_group.security_group_id, export_name="sgid")

    if external:
        security_group.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(443))
        # f"{application_name}-sg",

    load_balancer = lbv2.ApplicationLoadBalancer(scope,
                                                 id=f"{application_name}-loadbalancer",
                                                 load_balancer_name=f"{application_name}-loadbalancer",
                                                 security_group=security_group,
                                                 vpc=vpc,
                                                 internet_facing=True,
                                                 )

    certificate = lbv2.ListenerCertificate.from_arn(
        "arn:aws:acm:us-west-2:710339184759:certificate/0fb75035-7202-4657-8a84-ab8a2c339584")

    listener = load_balancer.add_listener(
        f"dako-{application_name}-listener",
        # default_target_groups=[target_group],
        port=443,
        certificates=[certificate],
        open=False
    )

    listener.add_action(
        'default-action',
        action=lbv2.ListenerAction.fixed_response(
            status_code=200,
            message_body=json.dumps({'message': 'Success'}),
            content_type='application/json'
        )
    )

    load_balancer.add_redirect(
        source_protocol=lbv2.ApplicationProtocol.HTTP,
        source_port=80,
        target_protocol=lbv2.ApplicationProtocol.HTTPS,
        target_port=443
    )
    CfnOutput(scope,
              f"{application_name}-listener-arn",
              value=listener.listener_arn,
              export_name=f"listenerarn"
              )
    #           )
    return load_balancer
