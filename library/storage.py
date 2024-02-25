
import boto3
import os

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
    
def write_ou_info_to_local(directory, ou_info_content):
    """
    Writes OU information to a local file in the specified directory.

    Parameters:
    - directory (str): The name of the local directory where the file will be stored.
    - ou_info_content (str): The OU information content to write to the file.

    Returns:
    - bool: True if the write operation was successful, False otherwise.
    """
    print("Attempting to write OU information locally.")

    # Define the file path
    file_path = os.path.join(directory, 'configs', 'ous.txt')
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    try:
        with open(file_path, 'w') as file:
            file.write(ou_info_content)
        print(f"Successfully wrote OU information to {file_path}")
        return True
    except Exception as e:
        print(f"Error writing OU information to local directory: {e}")
        return False
    
def write_ou_info_to_s3(bucket_name, ou_info_content):
    """
    Writes OU information content to an S3 bucket.

    Parameters:
    - bucket_name (str): The name of the S3 bucket where the content will be stored.
    - ou_info_content (str): The OU information content to write.

    Returns:
    - bool: True if the operation was successful, False otherwise.
    """
    file_path = "ous/ous.txt"  # Defining a specific path for OU information

    s3_client = boto3.client('s3')

    try:
        s3_client.put_object(Bucket=bucket_name, Key=file_path, Body=ou_info_content)
        print(f"Successfully uploaded OU information to S3 bucket {bucket_name} at {file_path}.")
        return True
    except Exception as e:
        print(f"Error uploading OU information to S3: {e}")
        return False
    
def write_configs(role_names, configs, running_locally, s3_bucket):
    for role_name in role_names:
        if running_locally:
            write_to_local('.', role_name, configs[role_name]['awscli'], "awscli-config")
            write_to_local('.', role_name, configs[role_name]['awscli_prefixed'], "awscli-config-prefixed")
            write_to_local('.', role_name, configs[role_name]['browser_plugin'], "browser-plugin-config")
        else:
            write_to_s3(s3_bucket, role_name, configs[role_name]['awscli'], "awscli-config")
            write_to_s3(s3_bucket, role_name, configs[role_name]['awscli_prefixed'], "awscli-config-prefixed")
            write_to_s3(s3_bucket, role_name, configs[role_name]['browser_plugin'], "browser-plugin-config")
