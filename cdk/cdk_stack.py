from aws_cdk import (
    CfnOutput,
    Duration,
    Size,
    Stack,
    aws_apigateway as apigw,
    #aws_apigatewayv2 as apigw2,
    #aws_certificatemanager as acm,
    aws_cloudfront as cloudfront,
    aws_iam as iam,
    aws_lambda_python_alpha as _lambda,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
)
from aws_cdk.aws_lambda import Code, Function, Runtime
from constructs import Construct

import os
import sys
import tempfile

cwd = os.path.dirname(os.path.abspath(__file__))
pwd = os.path.dirname(cwd)
natal_chart_path = os.path.join(pwd, 'natal-chart-generation')
sys.path.append(natal_chart_path)
from constants import IMG_DIR, IMG_FILES
import tempfile
import utils

FRONTEND_DOMAIN_NAME = os.getenv('FRONTEND_DOMAIN_NAME')

class NatalChartCdkStack(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        ### SET UP S3 BUCKETS

        # image layers
        img_layer_bucket = s3.Bucket(
            self, "ImageLayerBucket",
            public_read_access=True
        )

        # generated natal charts
        natal_chart_bucket = s3.Bucket(
            self, "NatalChartBucket",
            public_read_access=True
        )

        # resize all images before deploying
        image_loader = utils.LocalImageLoader(os.path.join(natal_chart_path, IMG_DIR), IMG_FILES)
        bg_im_size = image_loader.load_all_images()
        image_loader.resize_all_images()
        with tempfile.TemporaryDirectory() as temp_dir:
            
            for fname,im in image_loader.image_cache.items():
                # make necessary directories if they don't exist
                dir = os.path.split(fname)[0]
                if dir:
                    os.makedirs(os.path.join(temp_dir, dir), exist_ok=True)
                print(im.size)
                im.save(os.path.join(temp_dir, fname))
            
            # Deploy image layer bucket
            s3deploy.BucketDeployment(
                self,
                "ImageLayerDeployment",
                sources=[s3deploy.Source.asset(temp_dir)],
                destination_bucket=img_layer_bucket,
                memory_limit=1024
            )

        # deploy bucket for generated natal charts
        s3deploy.BucketDeployment(
            self,
            "NatalChartBucketDeployment",
            sources=[],
            destination_bucket=natal_chart_bucket,
            memory_limit=1024
        )

        # Create IAM user for CloudFront OAI
        cloudfront_user = iam.User(
            self, "CloudFrontUser"
        )

        # Create CloudFront OAI for the S3 bucket
        oai = cloudfront.OriginAccessIdentity(
            self, "OAI"
        )
        img_layer_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                actions=["s3:GetObject"],
                resources=[img_layer_bucket.arn_for_objects("*")],
                principals=[iam.CanonicalUserPrincipal(oai.cloud_front_origin_access_identity_s3_canonical_user_id)],
            )
        )

        # Grant read access to the IAM user for the CloudFront OAI
        img_layer_bucket.grant_read(cloudfront_user)

        # Create CloudFront distribution for the bucket
        distribution = cloudfront.CloudFrontWebDistribution(
            self, "Distribution",
            origin_configs=[
                cloudfront.SourceConfiguration(
                    s3_origin_source=cloudfront.S3OriginConfig(
                        s3_bucket_source=img_layer_bucket,
                        origin_access_identity=oai
                    ),
                    behaviors=[cloudfront.Behavior(is_default_behavior=True)]
                )
            ]
        )

        # copy main program files into lambda folder
        filenames = [
            "../natal-chart-generation/natal_chart.py",
            "../natal-chart-generation/utils.py",
            "../natal-chart-generation/image_params.py",
            "../natal-chart-generation/constants.py",
            "../natal-chart-generation/ephe",
            "../natal-chart-generation/fonts"
        ]
        for fname in filenames:
            cmd = f"cp -r {fname} lambda/"
            print(f"Executing: {cmd} ...")
            os.system(cmd)

        # Lambda Function
        lambda_fn = _lambda.PythonFunction(
            self, "NatalChartLambdaFunction",
            entry="lambda",
            runtime=Runtime.PYTHON_3_7,
            index="lambda.py",
            handler="handler",
            layers=[
                _lambda.PythonLayerVersion(
                    self, "DependenciesLayer", entry="../natal-chart-generation"
                )
            ],
            environment={
                "CLOUDFRONT_DISTRIBUTION_URL": distribution.distribution_domain_name,
                "IMG_LAYER_BUCKET_NAME": img_layer_bucket.bucket_name,
                "NATAL_CHART_BUCKET_NAME": natal_chart_bucket.bucket_name,
            },
            memory_size=3008,
            ephemeral_storage_size=Size.mebibytes(10240),
            timeout=Duration.seconds(60)
        )

        img_layer_bucket.grant_read(lambda_fn.role)
        natal_chart_bucket.grant_write(lambda_fn.role)

        lambda_fn.role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "cloudfront:GetDistribution",
                    "cloudfront:GetDistributionConfig",
                    "cloudfront:ListDistributions",
                    "cloudfront:ListDistributionsByWebACLId",
                ],
                resources=[
                    "*",
                ],
            )
        )
        lambda_fn.role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "s3:PutObject",
                    "s3:PutObjectAcl", 
                ],
                resources=[f"arn:aws:s3:::{natal_chart_bucket.bucket_name}/*"]
            )
        )

        # TODO: Restrict API access to our frontend domain
        
        # API Gateway
        api = apigw.LambdaRestApi(
            self, 'Endpoint',
            handler=lambda_fn,
            #default_authorizer=api_authorizer
        )
        # Output the API Gateway URL
        CfnOutput(
            self, "ApiGatewayUrl",
            value=api.url,
            description="The URL of the API Gateway",
            export_name="ApiGatewayUrl"
        )
        
