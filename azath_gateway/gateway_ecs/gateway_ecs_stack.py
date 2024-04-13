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
    aws_route53 as route53,
    aws_servicediscovery,
    Duration

)

from aws_cdk.aws_ec2 import Subnet


from constructs import Construct
class ServiceDiscoveryStack(Stack):

    def create_bucket(self, bucket_name):
        bucket = s3.Bucket(self, bucket_name, bucket_name=bucket_name)
        return bucket
    def create_security_group(self,security_group_name, vpc):
        security_group = ec2.SecurityGroup(
            self,
            security_group_name,
            security_group_name=security_group_name,
            vpc=vpc
        )
        security_group.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(8080),
            description="ALB Ingress"
        )
        return security_group

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
                self, f"repository", repository_name="dassem-api",
            ),
            tag='latest'
        )
        task_definition = ecs.FargateTaskDefinition(
            self,
            id=f"api-task-dev",
            family="dassem-api-task",
        )

        log_group = logs.LogGroup(self, f"api-logs", retention=logs.RetentionDays.ONE_DAY, removal_policy=RemovalPolicy.DESTROY)

        task_definition.add_container(
            "api_container",
            image=image,

            logging=ecs.LogDriver.aws_logs(stream_prefix=f"dako-api-logs", log_group=log_group),
            port_mappings=[ecs.PortMapping(container_port=5173, host_port=5173)]
        )


        service = ecs.FargateService(self,
                           f"dassem-fargate-service-dev",
                           cluster=cluster,
                           desired_count=1,
                           task_definition=task_definition,
                           service_name=f"dassem_service",
                           security_groups=[security_group],
                            assign_public_ip=True,
                            cloud_map_options=ecs.CloudMapOptions(
                                name="api-service",
                                container_port=8080,
                                cloud_map_namespace=self.dassem_namespace,
                                dns_record_type=aws_servicediscovery.DnsRecordType.A
                            )
                           )
        return service


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
        name = f'dakobed-dassem-{env}'
        # vpc = ec2.Vpc.from_lookup(self, "vpc-0be4b47e24b58c7e5", is_default=True)

        vpc = ec2.Vpc(self, 'vpc', cidr="10.1.0.0/16")


        ecs_service_sg = self.create_security_group(f"{name}-", vpc)

        vpc_link_security_group = ec2.SecurityGroup(
            self,
            "vpc_link_security_group",
            security_group_name="vpc_link_security_group",
            vpc=vpc
        )



        # self.service_sg.add_ingress_rule(
        #     peer=self.load_balancer_security_group,
        #     connection=ec2.Port.tcp(self.container_port),
        #     description="ALB Ingress"
        # )
        cluster = self.create_cluster(application_name=name, vpc=vpc)
        
        vpc_link = gateway.VpcLink(self,
                        "dassem-vpc-link",
                        vpc_link_name="dassem-vpc-link",
                        )

        # cfn_internet_gateway = ec2.CfnInternetGateway(self, "MyCfnInternetGateway")

        self.dassem_namespace = aws_servicediscovery.PrivateDnsNamespace(
            self,
            id="dassem-namespace",
            name="dassem-namespace",
            vpc=vpc
        )

        subnets = [
            {
                "SID":"subnet-0171d9d00744c70e5",
                "ZONE": "us-west-2a"
            },
            {
                "SID": "subnet-0ab00436026abcaa1",
                "ZONE": "us-west-2b"
            },

        ]
        subnets = []
        for subnet in subnets:
            subnets.append(
                Subnet.from_subnet_attributes(
                    self,
                    f"subnetid-{env}-{subnet['ZONE']}",
                    availability_zone=subnet.get("availability_zone"),
                    subnet_id=subnet.get("SID")
                )
            )



        # cfn_route_table = ec2.CfnRouteTable(self, "MyCfnRouteTable",
        #                                     vpc_id=vpc.id
        #                                     )
        # cfn_vPCGateway_attachment = ec2.CfnVPCGatewayAttachment(self, "MyCfnVPCGatewayAttachment",
        #                                                         vpc_id="vpcId",
        #
        #                                                         # the properties below are optional
        #                                                         internet_gateway_id="internetGatewayId",
        #                                                         vpn_gateway_id="vpnGatewayId"
        #                                                         )
        #
        # subneta = ec2.Subnet(vpc)

        # the properties below are optional

        #                                     )
        #
        # cfn_route = ec2.CfnRoute(self, "MyCfnRoute",
        #                          route_table_id="routeTableId",
        #
        #                          # the properties below are optional
        #                          carrier_gateway_id="carrierGatewayId",
        #                          core_network_arn="coreNetworkArn",
        #                          destination_cidr_block="destinationCidrBlock",
        #                          destination_ipv6_cidr_block="destinationIpv6CidrBlock",
        #                          destination_prefix_list_id="destinationPrefixListId",
        #                          egress_only_internet_gateway_id="egressOnlyInternetGatewayId",
        #                          gateway_id="gatewayId",
        #                          instance_id="instanceId",
        #                          local_gateway_id="localGatewayId",
        #                          nat_gateway_id="natGatewayId",
        #                          network_interface_id="networkInterfaceId",
        #                          transit_gateway_id="transitGatewayId",
        #                          vpc_endpoint_id="vpcEndpointId",
        #                          vpc_peering_connection_id="vpcPeeringConnectionId"
        #                          )

        #
        # self.dassem_namespace.create_service(
        #     "dassem_service",
        #     name="dassem_service",
        #     dns_record_type=aws_servicediscovery.DnsRecordType.A,
        #     dns_ttl=Duration.seconds(30),
        #     # health_check=aws_servicediscovery.HealthCheckConfig(
        #     #     type=aws_servicediscovery.HealthCheckType.HTTPS,
        #     #     resource_path="/healthcheck",
        #     #     failure_threshold=2
        #     # )
        # )

        import aws_cdk.aws_elasticloadbalancingv2 as elbv2
        # integration = gateway.AwsIntegration()

        # gateway.Integration(
        #     integration_http_method="a",
        #
        # )
        # integration = gateway.HttpIntegration(
        #     proxy=False,
        #
        #     options=gateway.IntegrationOptions(
        #         connection_type=gateway.ConnectionType.VPC_LINK,
        #
        #         integration_responses=[
        #             {'statusCode': "200", "responseParmaters": {"method.response.header.Content-Type": True}}],
        #         request_parameters={
        #             "integration.request.path.folder": "method.request.path.folder",
        #             "integration.request.path.key": "method.request.path.key",
        #         }
        #     )
        #     # options=gateway.IntegrationOptions(credentials_role=role, integration_responses=[{'status_code':200}])
        # )
        # # cloudmap_service = aws_servicediscovery.Service(namespace=self.dassem_namespace, Duration(30))
        # service = self.create_fargate_service(cluster, ecs_service_sg)
        # service.
        #


#
# class ServiceDiscoveryStacke(Stack):
#     def create_security_group(self,security_group_name, vpc):
#         return ec2.SecurityGroup(
#             self,
#             security_group_name,
#             security_group_name=security_group_name,
#             vpc=vpc
#         )
#
#     def create_cluster(self, application_name, vpc):
#         cluster = ecs.Cluster(self,
#                               f"{application_name}-cluster",
#                               cluster_name=f"{application_name}-cluster",
#                               vpc=vpc,
#                               container_insights=True
#                               )
#         return cluster
#
#     def create_fargate_service(self, cluster, security_group):
#         image = ecs.ContainerImage.from_ecr_repository(
#             repository=ecr.Repository.from_repository_name(
#                 self, f"repository", repository_name="dassem-api",
#             ),
#             tag='latest'
#         )
#         task_definition = ecs.FargateTaskDefinition(
#             self,
#             id=f"api-task-dev",
#             family="api-task",
#
#         )
#         log_group = logs.LogGroup(self, f"api-logs", retention=logs.RetentionDays.ONE_DAY, removal_policy=RemovalPolicy.DESTROY)
#
#         task_definition.add_container(
#             "api_container",
#             image=image,
#
#             logging=ecs.LogDriver.aws_logs(stream_prefix=f"demidrek-api-logs", log_group=log_group),
#             port_mappings=[ecs.PortMapping(container_port=5173, host_port=5173)]
#         )
#
#
#         service = ecs.FargateService(self,
#                            f"demidrek-fargate-service-dev",
#                            cluster=cluster,
#                            desired_count=1,
#                            task_definition=task_definition,
#                            service_name=f"demidrek_service",
#                            security_groups=[security_group],
#                             assign_public_ip=True
#                            )
#         return service
#     def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
#         super().__init__(scope, construct_id, **kwargs)
#         env = 'development'
#         name = f'dakobed-dassem-{env}'
#         vpc = ec2.Vpc.from_lookup(scope, "vpc-0be4b47e24b58c7e5", is_default=True)
#
#         ecs_service_sg = self.create_security_group(f"{name}-", vpc)
#         # self.service_sg.add_ingress_rule(
#         #     peer=self.load_balancer_security_group,
#         #     connection=ec2.Port.tcp(self.container_port),
#         #     description="ALB Ingress"
#         # )
#         cluster = self.create_cluster(application_name=name, vpc=vpc)
#         service = self.create_fargate_service(cluster, ecs_service_sg)
#
