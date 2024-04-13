from aws_cdk import (
    # Duration,
    Stack,
    CfnOutput,
    aws_iam as iam,
    aws_apigateway as gateway,
    aws_s3 as s3,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_logs as logs,
    aws_ecr as ecr,
    aws_elasticloadbalancingv2 as lbv2,
    RemovalPolicy,
    Fn
)


from constructs import Construct

from azath_gateway.utils import get_vpc

class ApiStack(Stack):
    def create_fargate_service(self, cluster, security_group):
        image = ecs.ContainerImage.from_ecr_repository(
            repository=ecr.Repository.from_repository_name(
                self, f"repository", repository_name="trane-ui",
            ),
            tag='latest'
        )
        task_definition = ecs.FargateTaskDefinition(
            self,
            id=f"api-task-dev",
            family="api-task",

        )
        log_group = logs.LogGroup(self, f"api-logs", retention=logs.RetentionDays.ONE_DAY, removal_policy=RemovalPolicy.DESTROY)

        task_definition.add_container(
            "api_container",
            image=image,

            logging=ecs.LogDriver.aws_logs(stream_prefix=f"dako-api-logs", log_group=log_group),
            port_mappings=[ecs.PortMapping(container_port=5173, host_port=5173)]
        )

        service = ecs.FargateService(self,
                           f"dako-fargate-service-dev",
                           cluster=cluster,
                           desired_count=1,
                           task_definition=task_definition,
                           service_name=f"dako_service",
                           security_groups=[security_group],
                        assign_public_ip=True
                           )
        return service

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        application_name = 'dakobed'

        vpc = get_vpc(self)

        cluster_security_group = ec2.SecurityGroup(
            self,
            f"{application_name}-api-sg",
            security_group_name=f"{application_name}-api-sg",
            vpc=vpc
        )
        load_balancer_arn = "arn:aws:elasticloadbalancing:us-west-2:710339184759:loadbalancer/app/dakobed-loadbalancer/995f124ca3811bcb"
        load_balancer = lbv2.ApplicationLoadBalancer.from_lookup(self, "load_balancer_arn", load_balancer_arn=load_balancer_arn)

        # load_balancer = lbv2.ApplicationLoadBalancer.from_application_load_balancer_attributes(self,"lb_from_att",load_balancer_dns_name=load_balancer_dns)
        load_balancer_sg = ec2.SecurityGroup.from_security_group_id(self, f"sg-from-lb", "sg-07dec17536a6d167b")

        cluster_security_group.add_ingress_rule(
            peer=load_balancer_sg,
            connection=ec2.Port.tcp(5173),
            description="ALB Ingress")

        cluster = ecs.Cluster.from_cluster_attributes(self,
                                                      f'{application_name}-cluster',
                                                      cluster_name=f'{application_name}-cluster',
                                                      vpc=vpc,
                                                      security_groups=[cluster_security_group]
                                                      )

        service = self.create_fargate_service(cluster, cluster_security_group)

        listener_arn = Fn.import_value(shared_value_to_import='listenerarn')
        # listener = lbv2.ApplicationListener.
        listener = lbv2.ApplicationListener.from_application_listener_attributes(self,
                                                                      f'{application_name}-listener',
                                                                        listener_arn=listener_arn,
                                                                        security_group=load_balancer_sg
                                                                      )
        target_group = lbv2.ApplicationTargetGroup(
            self,
            f"{application_name}-Targetgroup",
            port=5173,
            protocol=lbv2.ApplicationProtocol.HTTP,
            target_group_name=f"{application_name}-Targetgroup",
            target_type=lbv2.TargetType.IP,
            targets=[service],
            vpc=vpc,
        )

        lbv2.ApplicationListenerRule(self,
                                     "target-rule",
                                     listener=listener,
                                     priority=1,
                                     conditions=[
                                         # lbv2.ListenerCondition.host_headers(["dakobedbard.com"])
                                         lbv2.ListenerCondition.path_patterns(["*"])
                                     ],
                                     target_groups=[target_group]
                                     )

        from aws_cdk import aws_route53 as route53
        import aws_cdk.aws_route53_targets as targets
        hosted_zone = route53.HostedZone.from_lookup(self,"hosted_zone", domain_name="dakobedbard.com")
        # hosted_zone

        route53.ARecord(self,
                        "AliasRecord",
                        zone=hosted_zone,
                        target=route53.RecordTarget.from_alias(alias_target=targets.LoadBalancerTarget(load_balancer))
                        )
        #
        # CfnOutput(self, "load_balancer_dns", value=load_balancer.load_balancer_dns_name)
