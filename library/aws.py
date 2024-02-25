import boto3

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

def get_organizational_units(credentials, ou_overrides):
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
            process_ous(org_client, root['Id'], account_ou_mapping, parent_name='/', ou_overrides=ou_overrides)
    except Exception as e:
        print(f"Error retrieving organizational units: {e}")
        return None

    return account_ou_mapping

def process_ous(org_client, parent_id, account_ou_mapping, parent_name, ou_overrides):
    paginator = org_client.get_paginator('list_organizational_units_for_parent')
    for page in paginator.paginate(ParentId=parent_id):
        for ou in page['OrganizationalUnits']:
            # Retrieve the override for the current OU, defaulting to the OU's name if not found
            ou_override = ou_overrides.get(ou['Id'], ou['Name']) 

            # If there's a parent name, append this OU's name with a separator
            if parent_name:
                new_parent_name = f"{parent_name} / {ou_override}"
            else:
                new_parent_name = ou_override

            # Process accounts for the current OU
            accounts_page = org_client.list_accounts_for_parent(ParentId=ou['Id'])
            for account in accounts_page['Accounts']:
                account_id = account['Id']
                clean_parent_name = new_parent_name.strip()

                # Ensure the account mapping exists
                if account_id not in account_ou_mapping:
                    account_ou_mapping[account_id] = {} 

                # Update the mapping for this account
                account_ou_mapping[account_id]['OUName'] = clean_parent_name
                account_ou_mapping[account_id]['OUId'] = ou['Id']

            # Recursively process any child OUs
            process_ous(org_client, ou['Id'], account_ou_mapping, new_parent_name, ou_overrides)

def process_accounts_for_payer(payer_account_id, config, account_ou_mapping, config_gen):
    assume_role_arn = f"arn:aws:iam::{payer_account_id}:role/{config['assume_role_name']}"
    credentials = assume_role(assume_role_arn, config['session_name'] + payer_account_id)
    if not credentials:
        print(f"Failed to assume role {assume_role_arn}")
        return

    accounts = list_payer_accounts(credentials)
    if not accounts:
        print(f"Failed to list accounts for payer account {payer_account_id}.")
        return

    new_ou_mapping = get_organizational_units(credentials, config['ou_overrides'])
    if new_ou_mapping:
        account_ou_mapping.update(new_ou_mapping)

    return accounts
