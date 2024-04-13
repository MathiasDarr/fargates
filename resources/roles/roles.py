import aws_cdk.aws_iam as iam
def create_role(self, rolename):
    s3_read_policy = iam.ManagedPolicy.from_managed_policy_arn(self, id=rolename,
                                                               managed_policy_arn='arn:aws:iam::aws:policy/AmazonS3FullAccess')
    role = iam.Role(
        self,
        "s3-dakobed-role",
        role_name="Azath",
        assumed_by=iam.ServicePrincipal('apigateway.amazonaws.com'),
        managed_policies=[s3_read_policy]
    )
    return role


