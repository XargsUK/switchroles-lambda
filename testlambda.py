import boto3
import os
from moto import mock_aws
from unittest.mock import patch
from lambda_new import main_handler  
import shutil


@mock_aws
def test_main_function():
    """
    Test the main function of the lambda function script.
    """
    # Set up the mocked AWS environment
    aws_credentials()
    mock_organizations()
    mock_sts()

    # Mock environment variables
    # os.environ['S3_BUCKET'] = 'org-account-switcher-bucket'
    # os.environ['ASSUME_ROLE'] = 'AccountSwitcherLambdaRole'
    # os.environ['ROLE_NAMES'] = 'MyOrg-Administrator,MyOrg-ReadOnly,MyOrg-Finance'
    # os.environ['SESSION_NAME'] = 'testSession'
    # os.environ['PAYER_ACCOUNT_IDS'] = '123456789012,234567890123'  
    # os.environ['RUNNING_LOCALLY'] = 'true'  

    # Create a mock S3 resource and bucket
    s3 = boto3.resource('s3', region_name='us-east-1')
    s3.create_bucket(Bucket=os.environ['S3_BUCKET'])

    # Create a mock STS client
    sts = boto3.client('sts', region_name='us-east-1')
    # Create a mock Organizations client
    org = boto3.client('organizations', region_name='us-east-1')
    # Create a mock organization 
    org.create_organization(FeatureSet='ALL')

    # Define OUs and accounts structure
    ou_structure = [
        {"Name": "OU1", "Accounts": ["AccountA", "AccountB"]},
        {"Name": "OU2", "Accounts": ["AccountC"]},
    ]

    # Create OUs and accounts
    root_id = org.list_roots()['Roots'][0]['Id']  # Get the root ID dynamically
    for ou in ou_structure:
        ou_response = org.create_organizational_unit(
            ParentId=root_id,
            Name=ou["Name"]
        )
        ou_id = ou_response['OrganizationalUnit']['Id']
        for account_name in ou["Accounts"]:
            account_response = org.create_account(
                AccountName=account_name,
                Email=f"{account_name.lower()}@example.com"
            )
            # Mock account creation and moving account to the OU logic would go here

    # Call the main function of the lambda script
    event = {"Update": "True"}
    context = {}
    main_handler(event, context)  # Ensure this matches your lambda function's name

    # Check if the expected files were created and uploaded to the mock S3 bucket or local directory
    check_expected_files(s3)

    # Cleanup after test if necessary
    # cleanup_temp_files()


def mock_organizations():
    org_client = boto3.client('organizations', region_name='us-east-1')
    # Create an organization
    org_client.create_organization(FeatureSet='ALL')
    # Get the root ID
    root_id = org_client.list_roots()['Roots'][0]['Id']
    
    # Define the OUs and accounts structure
    ou_structure = {
        "OU1": ["AccountA", "AccountB"],
        "OU2": ["AccountC"],
        # Add more OUs and accounts as needed
    }
    
    # Create OUs and accounts
    for ou_name, accounts in ou_structure.items():
        # Create an OU
        ou_id = org_client.create_organizational_unit(ParentId=root_id, Name=ou_name)['OrganizationalUnit']['Id']
        for account_name in accounts:
            # Create an account
            account_email = f"{account_name.lower()}@example.com"
            account_id = org_client.create_account(AccountName=account_name, Email=account_email)['CreateAccountStatus']['AccountId']
            # Wait for account creation to complete (in real scenarios, you would check the status)
            # Move the account to the OU
            org_client.move_account(AccountId=account_id, SourceParentId=root_id, DestinationParentId=ou_id)


def mock_sts():
    sts_client = boto3.client('sts', region_name='us-east-1')
    # You can add any specific mocking behavior for STS here if needed

def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

def check_expected_files(s3):
    # Adjusted to match the simplified path structure
    expected_roles = os.environ['ROLE_NAMES'].split(',')
    for role in expected_roles:
        sanitized_role_name = role.replace("/", "-")
        expected_files = [
            f"{sanitized_role_name}-browser-plugin-config.txt",
            f"{sanitized_role_name}-awscli-config.txt",
            f"{sanitized_role_name}-awscli-config-prefixed.txt",
        ]
        for expected_file in expected_files:
            local_path = os.path.join('.', 'configs', expected_file)
            assert os.path.exists(local_path), f"File {local_path} was not created locally as expected."


def cleanup_temp_files():
    """
    Removes output files and directories created by the test in the local filesystem.
    """
    # Define the path to the configs directory where files are stored
    configs_path = os.path.join('.', 'configs')
    
    # Check if the configs directory exists and remove it if it does
    if os.path.exists(configs_path):
        shutil.rmtree(configs_path)
        print("Cleaned up temporary files and directories.")
    else:
        print("No temporary files found to clean up.")

if __name__ == "__main__":
    try:
        test_main_function()
        print("Test completed successfully.")
    finally:
        print("Cleaning up temporary files.")
        # cleanup_temp_files()


