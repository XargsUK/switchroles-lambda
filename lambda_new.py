import boto3
import os

def main_handler(event, context):
    # Configuration from environment variables
    s3_bucket = os.environ['S3_BUCKET']
    assume_role_name = os.environ['ASSUME_ROLE']
    role_names = os.environ['ROLE_NAMES'].split(',')
    session_name = os.environ['SESSION_NAME']
    payer_account_ids = os.environ['PAYER_ACCOUNT_IDS'].split(',')

    # Local testing
    running_locally = os.environ.get('RUNNING_LOCALLY', 'true').lower() == 'true'
    print(f"Running locally: {running_locally}")

    # Initialize dictionaries to hold aggregated configurations for each role
    awscli_configs = {}
    awscli_prefixed_configs = {}
    browser_plugin_configs = {}

    for payer_account_id in payer_account_ids:
        assume_role_arn = f"arn:aws:iam::{payer_account_id}:role/{assume_role_name}"
        credentials = assume_role(assume_role_arn, session_name + payer_account_id)
        if not credentials:
            print(f"Failed to assume role {assume_role_arn}")
            continue

        accounts = list_payer_accounts(credentials)
        if not accounts:
            print(f"Failed to list accounts for payer account {payer_account_id}.")
            continue

        account_ou_mapping = get_organizational_units(credentials)
        if not account_ou_mapping:
            print(f"Failed to get organizational units for payer account {payer_account_id}.")
            continue

        for role_name in role_names:
            # Generate configurations for each role
            new_awscli_config = generate_awscli_config(accounts, role_name)
            new_awscli_prefixed_config = generate_awscli_config(accounts, role_name, include_profile_prefix=True)
            new_browser_plugin_config = generate_browser_plugin_config(accounts, account_ou_mapping, role_name)

            # Append new configurations to existing ones
            awscli_configs[role_name] = awscli_configs.get(role_name, "") + new_awscli_config
            awscli_prefixed_configs[role_name] = awscli_prefixed_configs.get(role_name, "") + new_awscli_prefixed_config
            browser_plugin_configs[role_name] = browser_plugin_configs.get(role_name, "") + new_browser_plugin_config

    # Decide where to write configurations after generating all of them
    if running_locally:
        # Write configurations to local directory for each role
        for role_name in role_names:
            if role_name in awscli_configs:  # Check if configuration exists
                write_to_local('.', role_name, awscli_configs[role_name], "awscli-config")
            if role_name in awscli_prefixed_configs:
                write_to_local('.', role_name, awscli_prefixed_configs[role_name], "awscli-config-prefixed")
            if role_name in browser_plugin_configs:
                write_to_local('.', role_name, browser_plugin_configs[role_name], "browser-plugin-config")
    else:
        # Write the generated configurations to S3
        for role_name in role_names:
            if role_name in awscli_configs:  # Similar check as above
                write_to_s3(s3_bucket, role_name, awscli_configs[role_name], "awscli-config")
            if role_name in awscli_prefixed_configs:
                write_to_s3(s3_bucket, role_name, awscli_prefixed_configs[role_name], "awscli-config-prefixed")
            if role_name in browser_plugin_configs:
                write_to_s3(s3_bucket, role_name, browser_plugin_configs[role_name], "browser-plugin-config")

    print("Configuration files for all roles and payer accounts successfully processed.")

def assume_role(role_arn, session_name):
    """
    Assumes an AWS IAM role and returns temporary security credentials.

    Parameters:
    - role_arn (str): The ARN of the role to assume.
    - session_name (str): An identifier for the assumed role session.

    Returns:
    - dict: Temporary security credentials (AccessKeyId, SecretAccessKey, SessionToken)
    """
    # Create a STS client
    sts_client = boto3.client('sts')

    try:
        # Assume the specified role
        assumed_role = sts_client.assume_role(
            RoleArn=role_arn,
            RoleSessionName=session_name
        )

        # Extract and return the credentials
        credentials = assumed_role['Credentials']
        return {
            'AccessKeyId': credentials['AccessKeyId'],
            'SecretAccessKey': credentials['SecretAccessKey'],
            'SessionToken': credentials['SessionToken']
        }
    except Exception as e:
        print(f"Error assuming role: {e}")
        return None

def list_payer_accounts(credentials):
    """
    Lists all AWS accounts under the payer account.

    Parameters:
    - credentials (dict): Temporary security credentials with AccessKeyId, SecretAccessKey, and SessionToken.

    Returns:
    - list[dict]: A list of dictionaries, each representing an AWS account with its details (Id, Name, Email, etc.).
    """
    # Create an Organizations client using the temporary credentials
    org_client = boto3.client(
        'organizations',
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken'],
    )

    accounts = []
    paginator = org_client.get_paginator('list_accounts')

    try:
        for page in paginator.paginate():
            for account in page['Accounts']:
                accounts.append({
                    'Id': account['Id'],
                    'Name': account['Name'],
                    'Email': account['Email'],
                    'Status': account['Status']
                })
    except Exception as e:
        print(f"Error listing accounts: {e}")
        return None

    return accounts

def get_organizational_units(credentials):
    """
    Retrieves the organizational units (OUs) for each account in the AWS Organization.

    Parameters:
    - credentials (dict): Temporary security credentials with AccessKeyId, SecretAccessKey, and SessionToken.

    Returns:
    - dict: A mapping of account IDs to their organizational unit names and IDs.
    """
    org_client = boto3.client(
        'organizations',
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken'],
    )

    # Initialize a dictionary to hold account ID to OU mapping
    account_ou_mapping = {}

    try:
        # List all roots
        roots = org_client.list_roots()['Roots']
        for root in roots:
            # Recursively list and process OUs under each root
            process_ous(org_client, root['Id'], account_ou_mapping, parent_name='/')
    except Exception as e:
        print(f"Error retrieving organizational units: {e}")
        return None

    return account_ou_mapping

def process_ous(org_client, parent_id, account_ou_mapping, parent_name):
    """
    Recursively processes OUs under a given parent (root or OU) to find account mappings.

    Parameters:
    - org_client: The Organizations client.
    - parent_id (str): The ID of the parent (root or OU) under which to list OUs.
    - account_ou_mapping (dict): The mapping of account IDs to OUs being built.
    - parent_name (str): The hierarchical name of the parent for building OU paths.
    """
    # List organizational units for a parent ID
    paginator = org_client.get_paginator('list_organizational_units_for_parent')
    for page in paginator.paginate(ParentId=parent_id):
        for ou in page['OrganizationalUnits']:
            # Build the OU path
            ou_path = parent_name + ou['Name']
            # List accounts for the current OU
            accounts_page = org_client.list_accounts_for_parent(ParentId=ou['Id'])
            for account in accounts_page['Accounts']:
                # Map account ID to OU path and OU ID
                account_ou_mapping[account['Id']] = {'OUName': ou_path, 'OUId': ou['Id']}
            
            # Recursively process any child OUs
            process_ous(org_client, ou['Id'], account_ou_mapping, ou_path + '/')

def generate_awscli_config(accounts, role_name, include_profile_prefix=False):
    """
    Generates AWS CLI configuration content for a list of accounts and a specified role.

    Parameters:
    - accounts (list[dict]): A list of dictionaries, each representing an AWS account with at least 'Id' and 'Name'.
    - role_name (str): The role name to generate configurations for.
    - include_profile_prefix (bool): Whether to include the 'profile ' prefix in profile names.

    Returns:
    - str: The generated AWS CLI configuration content.
    """
    config_lines = []

    for account in accounts:
        account_id = account['Id']
        account_name = account['Name'].replace(' ', '_')  # Replace spaces with underscores for compatibility
        profile_name = f"{account_name}"
        if include_profile_prefix:
            profile_name = "profile " + profile_name

        role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"
        config_lines.append(f"[{profile_name}]")
        config_lines.append(f"role_arn = {role_arn}")
        config_lines.append("source_profile = default")
        config_lines.append("")  # Add a newline for readability

    return "\n".join(config_lines)



def generate_browser_plugin_config(accounts, account_ou_mapping, role_name):
    """
    Generates configuration content for a browser plugin based on accounts, their OUs, and a specified role.

    Parameters:
    - accounts (list[dict]): A list of dictionaries, each representing an AWS account with at least 'Id' and 'Name'.
    - account_ou_mapping (dict): A mapping of account IDs to their organizational unit names and IDs.
    - role_name (str): The role name for which to generate configurations.

    Returns:
    - str: The generated browser plugin configuration content.
    """
    config_lines = []

    for account in accounts:
        account_id = account['Id']
        account_name = account['Name'].replace(' ', '_')  # Ensure compatibility
        ou_info = account_ou_mapping.get(account_id, {'OUName': 'Unknown', 'OUId': 'N/A'})
        ou_name = ou_info['OUName'].replace(' ', '_')  # Ensure compatibility

        # Include the role name as a configuration entry, not in the section header
        config_lines.append(f"[{ou_name} / {account_name}]")
        config_lines.append(f"aws_account_id = {account_id}")
        config_lines.append(f"role_name = {role_name}")
        config_lines.append("")  # Add a newline for readability

    return "\n".join(config_lines)



def write_to_s3(bucket_name, role_name, config_content, config_type):
    """
    Writes generated configuration content to an S3 bucket under a path based on the role name.

    Parameters:
    - bucket_name (str): The name of the S3 bucket where the config will be stored.
    - role_name (str): The name of the role, which will be used to determine the storage path.
    - config_content (str): The configuration content to write to the file.
    - config_type (str): The type of configuration (e.g., "awscli", "browser-plugin") to specify the file name.

    Returns:
    - bool: True if the write operation was successful, False otherwise.
    """
    print(f"Attempting to write to S3 for {role_name} with type {config_type}")
    # Sanitise role_name to use as part of the file path
    sanitized_role_name = role_name.split('/')[-1]  # Get the last part of the role name if it includes paths
    file_path = f"{sanitized_role_name}/{config_type}.txt"

    # Create an S3 client
    s3_client = boto3.client('s3')

    try:
        # Write the config content to the specified S3 path
        s3_client.put_object(Bucket=bucket_name, Key=file_path, Body=config_content)
        print(f"Successfully wrote {config_type} config to {bucket_name}/{file_path}")
        return True
    except Exception as e:
        print(f"Error writing to S3: {e}")
        return False

def write_to_local(directory, role_name, config_content, config_type):
    """
    Writes generated configuration content to a local directory based on the role name,
    simplified for debugging to write directly into the 'configs' directory.

    Parameters:
    - directory (str): The name of the local directory where the config will be stored.
    - role_name (str): The name of the role, which will be used to determine the storage path.
    - config_content (str): The configuration content to write to the file.
    - config_type (str): The type of configuration (e.g., "awscli", "browser-plugin") to specify the file name.

    Returns:
    - bool: True if the write operation was successful, False otherwise.
    """
    print(f"Attempting to write locally for {role_name} with type {config_type}")

    # For debugging: Write all files directly to the 'configs' directory
    configs_dir = os.path.join(directory, 'configs')
    os.makedirs(configs_dir, exist_ok=True)

    # Simplify file naming to avoid subdirectory creation
    sanitized_role_name = role_name.replace("/", "-")
    file_name = f"{sanitized_role_name}-{config_type}.txt"
    file_path = os.path.join(configs_dir, file_name)
    print(f"Writing file to: {file_path}")

    try:
        print(f"Config content length for {role_name} ({config_type}): {len(config_content)}")
        with open(file_path, 'w') as file:
            file.write(config_content)
        print(f"Successfully wrote {config_type} config to {file_path}")
        return True
    except Exception as e:
        print(f"Error writing to local directory: {e}")
        return False


if __name__ == '__main__':
    mock_event = {"Update": "True"}
    mock_context = {}
    main_handler(mock_event, mock_context)
