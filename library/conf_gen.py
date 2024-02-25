import random

class ConfigGenerator:
    def __init__(self):
        self.ou_colors = {}


    def generate_awscli_config(self, accounts, role_name, include_profile_prefix=False):
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

    def generate_browser_plugin_config(self, accounts, account_ou_mapping, role_name):
        """
        Generates configuration content for a browser plugin based on accounts, their OUs, and a specified role,
        with adjusted formatting for OU names.

        Parameters:
        - accounts (list[dict]): A list of dictionaries, each representing an AWS account with at least 'Id' and 'Name'.
        - account_ou_mapping (dict): A mapping of account IDs to their organizational unit names and IDs.
        - role_name (str): The role name for which to generate configurations.

        Returns:
        - str: The generated browser plugin configuration content with corrected formatting.
        """
        config_lines = []

        # Sort accounts by OU Name 
        accounts = sorted(accounts, key=lambda account: account_ou_mapping.get(account['Id'], {'OUName': 'Unknown'})['OUName'])

        for account in accounts:
            account_id = account['Id']
            account_name = account['Name'].replace(' ', '_')
            ou_info = account_ou_mapping.get(account_id, {'OUName': 'Unknown', 'OUId': 'N/A'})
            ou_name = ou_info['OUName'].lstrip(' /')

            # Instead of using a prefix, use the OU name for color mapping
            if ou_name in self.ou_colors:
                color = self.ou_colors[ou_name]
            else:
                # Generate a random color and assign it to this OU
                color = "".join([random.choice("0123456789ABCDEF") for _ in range(6)])
                self.ou_colors[ou_name] = color

            config_lines.append(f"[{ou_name} / {account_name}]")
            config_lines.append(f"aws_account_id = {account_id}")
            config_lines.append(f"role_name = {role_name}")
            config_lines.append(f"color = {color}")  # Include the color in the config
            config_lines.append("")  # Add a newline for readability

        return "\n".join(config_lines)