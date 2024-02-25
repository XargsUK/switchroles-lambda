import json
import os
from . import storage

def parse_ou_overrides():
    """
    Parse the OU_OVERRIDES environment variable and return the parsed JSON.

    Returns:
        list: A list of OU overrides parsed from the environment variable.
    """
    ou_overrides_str = os.environ.get('OU_OVERRIDES', '[]')  
    try:
        return json.loads(ou_overrides_str)
    except json.JSONDecodeError:
        print("Error decoding OU_OVERRIDES JSON. Ensure it's properly formatted.")
        return []
    
def export_ou_information(ou_mapping, running_locally, s3_bucket=None, directory='.'):
    """
    Exports the OU information either to a local file or to an S3 bucket based on the running environment.

    Parameters:
    - ou_mapping (dict): The mapping of OU IDs to their information.
    - running_locally (bool): Flag indicating whether to run locally or not.
    - s3_bucket (str, optional): The name of the S3 bucket to use when not running locally.
    - directory (str, optional): The local directory to use when running locally.
    """
    # Generate OU information content
    ou_info_content = ""
    for account_id, account_details in ou_mapping.items():
        ou_info_content += f"{account_id}: {account_details['OUName']} ({account_details['OUId']})\n"
    if running_locally:
        storage.write_ou_info_to_local(directory, ou_info_content)
    else:
        storage.write_ou_info_to_s3(s3_bucket, ou_info_content)