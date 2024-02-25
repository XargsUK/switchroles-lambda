import json
from library import util, aws, storage
from library.conf_gen import ConfigGenerator


ou_colors = {}
ou_overrides = {
    "ou-fmth-o9vy8tjo": "",
}

def main_handler(event, context):
    config_gen = ConfigGenerator()
    config = util.load_environment_config()
    print(f"Running locally: {config['running_locally']}")

    account_ou_mapping = {}
    configs = {role_name: {'awscli': '', 'awscli_prefixed': '', 'browser_plugin': ''} for role_name in config['role_names']}

    for payer_account_id in config['payer_account_ids']:
        accounts = aws.process_accounts_for_payer(payer_account_id, config, account_ou_mapping, config_gen)
        if not accounts:
            continue
        for role_name in config['role_names']:
            role_configs = config_gen.generate_configs_for_role(role_name, accounts, account_ou_mapping, config_gen)
            for key, value in role_configs.items():
                configs[role_name][key] += value

    storage.write_configs(config['role_names'], configs, config['running_locally'], config['s3_bucket'])
    print("Configuration files for all roles and payer accounts successfully processed.")
    util.export_ou_information(account_ou_mapping, config['running_locally'], config['s3_bucket'], '.')
    print("OU information has been exported.")


if __name__ == '__main__':
    mock_event = {"Update": "True"}
    mock_context = {}
    main_handler(mock_event, mock_context)
