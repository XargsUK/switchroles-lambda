import boto3
import os
from moto import mock_aws
from lambda_function import main  # Adjust if your function's name or path is different

@mock_aws
def setup_mock_aws_environment():
    """
    Set up a mock AWS environment for testing.
    """
    # Create a mock STS client
    sts = boto3.client('sts')
    # Create a mock Organizations client
    org = boto3.client('organizations')
    # Create a mock S3 resource
    s3 = boto3.resource('s3')

    # Create a mock organization (you can customize parameters as needed)
    org.create_organization(FeatureSet='ALL')
    # Create a mock S3 bucket (adjust the bucket name to match your script)
    s3.create_bucket(Bucket='org-account-switcher-bucket')

    # (Optional) Add more setup here, such as creating mock accounts, organizational units, etc.

def test_main_function():
    """
    Test the main function of the lambda_function script.
    """
    setup_mock_aws_environment()
    event = {"Update": "True"}
    context = {}

    main(event, context)

    # Check if a file was created as expected
    expected_file_path = "/tmp/expected_filename.txt"  # Adjust based on your script's output
    assert os.path.exists(expected_file_path), "Expected file was not created."

    # Check if a file was uploaded to the mock S3 bucket
    s3 = boto3.resource('s3')
    bucket = s3.Bucket('org-account-switcher-bucket')
    files_in_bucket = list(bucket.objects.all())
    assert any(f.key == "expected_s3_key.txt" for f in files_in_bucket), "File was not uploaded to S3 as expected."

    # Cleanup after test
    if os.path.exists(expected_file_path):
        os.remove(expected_file_path)

if __name__ == "__main__":
    test_main_function()
    print("Test completed successfully.")
