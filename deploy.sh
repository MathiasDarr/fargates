#!/bin/bash
export AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
echo ${AWS_ACCOUNT}
cdk synth --require-approval never
cdk deploy --require-approval never --all


