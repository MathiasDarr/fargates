from aws_cdk.aws_iam import PolicyStatement, Effect, AnyPrincipal, PolicyDocument


def getPolicyDocument():
    mainPolicy = PolicyStatement(effect=Effect.ALLOW, actions=["execute:Invoke"], principals=[AnyPrincipal()])
    return PolicyDocument(statements=[mainPolicy])
