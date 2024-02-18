import boto3
import os
from moto import mock_aws
from unittest.mock import patch
from lambda_function import main  

@mock_aws
def test_main_function():
    """
    Test the main function of the lambda_function script.
    """
    # Set up the mocked AWS environment
    aws_credentials()

    # Create a mock S3 resource and bucket
    s3 = boto3.resource('s3', region_name='us-east-1')
    s3.create_bucket(Bucket='org-account-switcher-bucket')

    # Create accounts-not-yet-onboarded.dat 
    object_key = "accounts-not-yet-onboarded.dat"
    s3.Object('org-account-switcher-bucket', object_key).put(Body="")

    # Create a mock STS client
    sts = boto3.client('sts')
    # Create a mock Organizations client
    org = boto3.client('organizations')
    # Create a mock organization 
    org.create_organization(FeatureSet='ALL')

    # Define OUs and accounts structure
    ou_structure = [
        {"Name": "OU1", "Accounts": ["AccountA", "AccountB"]},
        {"Name": "OU2", "Accounts": ["AccountC"]},
    ]

    # Create OUs and accounts
    for ou in ou_structure:
        ou_response = org.create_organizational_unit(
            ParentId='r-root',  # Assuming 'r-root' is the root id of the organization
            Name=ou["Name"]
        )
        ou_id = ou_response['OrganizationalUnit']['Id']
        for account_name in ou["Accounts"]:
            # Assume create_account simulates account creation. In real use, account creation is asynchronous and more complex.
            org.create_account(
                AccountName=account_name,
                Email=f"{account_name.lower()}@example.com"
            )
            # Here you might want to simulate moving the account to the OU, but moto's mock for move_account might be limited


    # Call the main function of the lambda script
    event = {"Update": "True"}
    context = {}
    main(event, context)

    # Check if the expected files were created and uploaded to the mock S3 bucket
    check_expected_files(s3)

    # Cleanup after test
    # cleanup_temp_files()

def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

def check_expected_files(s3):
    # Output files based on the roles in lambda_function.py
    expected_roles = [
        "OrganizationAccountAccessRole",
        "MyOrg-ReadOnly",
        "MyOrg-Finance",
        "MyOrg-Administrator",
    ]
    for role in expected_roles:
        expected_files = [
            f"{role}/browser-plugin-config.txt",
            f"{role}/awscli-config.txt",
            f"{role}/awscli-config-prefixed.txt",
        ]
        for expected_file in expected_files:
            # Check if the file was uploaded to the mock S3 bucket
            bucket = s3.Bucket('org-account-switcher-bucket')
            files_in_bucket = list(bucket.objects.filter(Prefix=role))
            assert any(f.key == expected_file for f in files_in_bucket), f"File {expected_file} was not uploaded to S3 as expected."

def cleanup_temp_files():
    # Remove output files created by the test
    expected_roles = [
        "OrganizationAccountAccessRole",
        "MyOrg/ReadOnly",
        "MyOrg/Finance",
        "MyOrg/Administrator",
    ]
    for role in expected_roles:
        safe_role_name = role.replace("/", "-")
        expected_files = [
            f"{safe_role_name}_browser-plugin-config.txt",
            f"{safe_role_name}_awscli-config.txt",
            f"{safe_role_name}_awscli-config-prefixed.txt",
        ]
        for expected_file in expected_files:
            file_path = f"/tmp/{expected_file}"
            if os.path.exists(file_path):
                os.remove(file_path)

if __name__ == "__main__":
    test_main_function()
    print("Test completed successfully.")
