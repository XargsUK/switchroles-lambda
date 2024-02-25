import os
import json
from library import storage, aws, utility
from library.conf_gen import ConfigGenerator


ou_colors = {}
ou_overrides = {
    "ou-fmth-o9vy8tjo": "",
}
json_data = json.dumps(ou_overrides)

def main_handler(event, context):
    config_gen = ConfigGenerator()

    s3_bucket = os.environ['S3_BUCKET']
    assume_role_name = os.environ['ASSUME_ROLE']
    role_names = os.environ['ROLE_NAMES'].split(',')
    session_name = os.environ['SESSION_NAME']
    payer_account_ids = os.environ['PAYER_ACCOUNT_IDS'].split(',')
    ou_overrides = json.loads(os.environ['OU_OVERRIDES']) 

    # Local testing
    running_locally = os.environ.get('RUNNING_LOCALLY', 'true').lower() == 'true'
    print(f"Running locally: {running_locally}")

    # Initialise dictionaries to hold aggregated configurations for each role
    awscli_configs = {}
    awscli_prefixed_configs = {}
    browser_plugin_configs = {}

    ou_overrides = utility.parse_ou_overrides()

    # Initialise account_ou_mapping before the loop
    account_ou_mapping = {}

    for payer_account_id in payer_account_ids:
        assume_role_arn = f"arn:aws:iam::{payer_account_id}:role/{assume_role_name}"
        credentials = aws.assume_role(assume_role_arn, session_name + payer_account_id)
        if not credentials:
            print(f"Failed to assume role {assume_role_arn}")
            continue

        accounts = aws.list_payer_accounts(credentials)
        if not accounts:
            print(f"Failed to list accounts for payer account {payer_account_id}.")
            continue

        # Get OUs for this payer account and update the mapping
        new_ou_mapping = aws.get_organizational_units(credentials, ou_overrides)
        if new_ou_mapping:
            account_ou_mapping.update(new_ou_mapping)

        for role_name in role_names:
            # Generate configurations for each role
            print(f"Before calling generate_awscli_config: {type(accounts)}")
            new_awscli_config = config_gen.generate_awscli_config(accounts, role_name)
            new_awscli_prefixed_config = config_gen.generate_awscli_config(accounts, role_name, include_profile_prefix=True)
            new_browser_plugin_config = config_gen.generate_browser_plugin_config(accounts, account_ou_mapping, role_name)

            # Append new configurations to existing ones
            awscli_configs[role_name] = awscli_configs.get(role_name, "") + new_awscli_config
            awscli_prefixed_configs[role_name] = awscli_prefixed_configs.get(role_name, "") + new_awscli_prefixed_config
            browser_plugin_configs[role_name] = browser_plugin_configs.get(role_name, "") + new_browser_plugin_config

    # Decide where to write configurations after generating all of them
    if running_locally:
        # Write configurations to local directory for each role
        for role_name in role_names:
            if role_name in awscli_configs:  # Check if configuration exists
                storage.write_to_local('.', role_name, awscli_configs[role_name], "awscli-config")
            if role_name in awscli_prefixed_configs:
                storage.write_to_local('.', role_name, awscli_prefixed_configs[role_name], "awscli-config-prefixed")
            if role_name in browser_plugin_configs:
                storage.write_to_local('.', role_name, browser_plugin_configs[role_name], "browser-plugin-config")
    else:
        # Write the generated configurations to S3
        for role_name in role_names:
            if role_name in awscli_configs:  # Similar check as above
                storage.write_to_s3(s3_bucket, role_name, awscli_configs[role_name], "awscli-config")
            if role_name in awscli_prefixed_configs:
                storage.write_to_s3(s3_bucket, role_name, awscli_prefixed_configs[role_name], "awscli-config-prefixed")
            if role_name in browser_plugin_configs:
                storage.write_to_s3(s3_bucket, role_name, browser_plugin_configs[role_name], "browser-plugin-config")

    print("Configuration files for all roles and payer accounts successfully processed.")
    # Export OU information after processing all roles and payer accounts
    utility.export_ou_information(account_ou_mapping, running_locally, s3_bucket, '.')
    print("OU information has been exported.")

if __name__ == '__main__':
    mock_event = {"Update": "True"}
    mock_context = {}
    main_handler(mock_event, mock_context)
