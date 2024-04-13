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
    # aws_sqs as sqs,
    aws_route53 as route53

)



from resources.apiGateway.policy_statements import getPolicyDocument
from aws_cdk.aws_apigateway import RestApi, StageOptions, EndpointType, MethodResponse
from resources.apiGateway.gateway import getOrigins

from constructs import Construct


def get_vpc(scope):
    vpc = ec2.Vpc.from_lookup(scope, "vpc-0be4b47e24b58c7e5", is_default=True)
    return vpc

class LBStack(Stack):

    def create_bucket(self, bucket_name):
        bucket = s3.Bucket(self, bucket_name, bucket_name=bucket_name)
        return bucket

    def create_security_group(self,security_group_name, vpc):
        return ec2.SecurityGroup(
            self,
            security_group_name,
            security_group_name=security_group_name,
            vpc=vpc
        )

    def create_cluster(self, application_name, vpc):
        cluster = ecs.Cluster(self,
                              f"{application_name}-cluster",
                              cluster_name=f"{application_name}-cluster",
                              vpc=vpc,
                              container_insights=True
                              )
        return cluster

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

    def create_load_balancer(self, application_name, vpc, external=False):
        security_group = ec2.SecurityGroup(self,
                                           f"{application_name}-sg",
                                           vpc=vpc
                                           )
        if external:
            security_group.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(443))
            # f"{application_name}-sg",
        load_balancer = lbv2.ApplicationLoadBalancer(self,
                                                     id=f"{application_name}-loadbalancer",
                                                     load_balancer_name=f"{application_name}-loadbalancer",
                                                     security_group=security_group,
                                                     vpc=vpc,
                                                     internet_facing=True,
                                                     )
        return load_balancer

    def create_role(self, rolename, bucket: s3.IBucket):
        s3_read_policy = iam.ManagedPolicy.from_managed_policy_arn(self, id="s3-role",
                                                                   managed_policy_arn='arn:aws:iam::aws:policy/AmazonS3FullAccess')
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
        return role

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        env = 'development'
        name = f'dakobed-{env}'
        vpc = get_vpc(self)
        print(vpc)

        self.container_port = 5173

        self.load_balancer_security_group = ec2.SecurityGroup(
            self,
            f"{name}-lb-sg",
            security_group_name=f"{name}-lb-sg",
            vpc=vpc
        )

        self.load_balancer_security_group.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(self.container_port),
            description="ALB Ingress"
        )

        self.service_sg = self.create_security_group(f"{name}-", vpc)
        self.service_sg.add_ingress_rule(
            peer=self.load_balancer_security_group,
            connection=ec2.Port.tcp(self.container_port),
            description="ALB Ingress"
        )
        cluster = self.create_cluster(application_name=name, vpc=vpc)
        service = self.create_fargate_service(cluster, self.service_sg)
        certificate = lbv2.ListenerCertificate.from_arn("arn:aws:acm:us-west-2:710339184759:certificate/0fb75035-7202-4657-8a84-ab8a2c339584")

        load_balancer = self.create_load_balancer(name, vpc=vpc, external=True)
        target_group = lbv2.ApplicationTargetGroup(
            self,
            f"{name}-Targetgroup",
            port=self.container_port,
            protocol=lbv2.ApplicationProtocol.HTTP,
            target_group_name=f"{name}-Targetgroup",
            target_type=lbv2.TargetType.IP,
            targets=[service],
            vpc=vpc
        )
        load_balancer.add_listener(
            f"dako-{name}-listener",
            default_target_groups=[target_group],
            port=443,
            certificates=[certificate],
            open=False
        )
        load_balancer.add_redirect(
            source_protocol=lbv2.ApplicationProtocol.HTTP,
            source_port=80,
            target_protocol=lbv2.ApplicationProtocol.HTTPS,
            target_port=443
        )

        hosted_zone = route53.HostedZone.from_lookup(self,"hosted_zone", domain_name="dakobedbard.com")
        # hosted_zone
        import aws_cdk.aws_route53_targets as targets
        # route53.ARecord(self,
        #                 "AliasRecord",
        #                 zone=hosted_zone,
        #                 target=route53.RecordTarget.from_alias(alias_target=targets.LoadBalancerTarget(load_balancer))
        #                 )
        #
        # CfnOutput(self, "load_balancer_dns", value=load_balancer.load_balancer_dns_name)
