from aws_cdk import (
    # Duration,
    Stack,
    CfnOutput,
    aws_iam as iam,
    aws_s3 as s3,
    aws_ec2 as _ec2,
    aws_route53 as route53,
    aws_servicediscovery,
    aws_apigatewayv2 as gateway,
    aws_certificatemanager as acm

)


from constructs import Construct
class InfrastructureStack(Stack):

    def create_bucket(self, bucket_name):
        bucket = s3.Bucket(self, bucket_name, bucket_name=bucket_name)
        return bucket

    def create_security_group(self, security_group_name, vpc):
        security_group = _ec2.SecurityGroup(
            self,
            security_group_name,
            security_group_name=security_group_name,
            vpc=vpc
        )
        security_group.add_ingress_rule(
            peer=_ec2.Peer.any_ipv4(),
            connection=_ec2.Port.tcp(8080),
            description="ALB Ingress"
        )
        return security_group



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
        # name = f'dakobed-dassem-{env}'
        vpc = _ec2.Vpc.from_lookup(self, "vpc-0be4b47e24b58c7e5", is_default=True)
        vpc_link_security_group = _ec2.SecurityGroup(
            self,
            "vpc_link_security_group",
            security_group_name="vpc_link_security_group",
            vpc=vpc
        )


        namespace = aws_servicediscovery.PrivateDnsNamespace(
            self,
            id="dassem-namespace",
            name="dassem-namespace",
            vpc=vpc
        )

        subnets_configuration = [
            {
                "SID": "subnet-0171d9d00744c70e5",
                "ZONE": "us-west-2a"
            },
            {
                "SID": "subnet-0ab00436026abcaa1",
                "ZONE": "us-west-2b"
            },

        ]
        subnets = []
        for subnet_config in subnets_configuration:
            subnet = _ec2.Subnet.from_subnet_attributes(
                self,
                f"subnetid-{env}-{subnet_config['ZONE']}",
                availability_zone=subnet_config.get("availability_zone"),
                subnet_id=subnet_config.get("SID")
            )

            routetable_id = subnet.route_table

            subnets.append(subnet)


        # vpc_link = gateway.VpcLink(self,
        #                 "dassem-vpc-link",
        #                 vpc_link_name="dassem-vpc-link",
        #
        #                 )

        vpc_link = gateway.CfnVpcLink(self, "dassem-vpc-link",
                           name="dassem-vpc-link",
                           subnet_ids=["subnet-0171d9d00744c70e5", "subnet-0ab00436026abcaa1"],
                            security_group_ids=[vpc_link_security_group.security_group_id]

                           )
        #
        # cfn_vPCGateway_attachment = _ec2.CfnVPCGatewayAttachment(self, "MyCfnVPCGatewayAttachment",
        #                                                         vpc_id=vpc.vpc_id,
        #                                                         internet_gateway_id="igw-05dcfe201895b98ed",
        #                                                         )

        routetable_id = "rtb-0f3a5442cc186980b"



        cfn_route = _ec2.CfnRoute(self, "MyCfnRoute",
                                 route_table_id=routetable_id,
                                 gateway_id="igw-05dcfe201895b98ed",
                                destination_cidr_block="0.0.0.0/0"

                                  )




        hosted_zone = route53.HostedZone.from_lookup(self,"hosted_zone", domain_name="dakobedbard.com")
        # CfnOutput()
        # CfnOutput()
        # CfnOutput()
        certifcate = acm.Certificate.from_certificate_arn(self, "dassem_certificate", certificate_arn="arn:aws:acm:us-west-2:710339184759:certificate/0fb75035-7202-4657-8a84-ab8a2c339584")
        CfnOutput(self, "hosted_zone_id", export_name="HostedZoneID", value=hosted_zone.hosted_zone_id)
        CfnOutput(self, "certifcate_arn", export_name="CertificateARN", value=certifcate.certificate_arn)
        CfnOutput(self, "namespace_arn", export_name="CloudNamespaceARN", value=namespace.namespace_arn)
        CfnOutput(self, "namespace_name", export_name="CloudNamespaceName", value=namespace.namespace_name)
        CfnOutput(self, "namespace_id", export_name="CloudNamespaceID", value=namespace.namespace_id)