import boto3, time, urllib
from botocore.exceptions import ClientError
import os
import json

# Load environment variables, if not set, load testing values

payer_accounts_json = os.getenv('PAYER_ACCOUNTS_JSON', '{"012345678901": "", "123456789012": "ACC1"}')
payer_accounts = json.loads(payer_accounts_json)

role_names_json = os.getenv('ROLE_NAMES_JSON', '["OrganizationAccountAccessRole", "MyOrg/ReadOnly", "MyOrg/Finance", "MyOrg/Administrator"]')
roles = json.loads(role_names_json)

s3_bucket_name = os.getenv('S3_BUCKET_NAME', 'org-account-switcher-bucket')
role_session_name = os.getenv('ROLE_SESSION_NAME', 'RoleSwitcherLambda')
cached_ou_names_json = os.getenv('CACHED_OU_NAMES_JSON', '{"ou-xxxx-xxxxxxx1": "OU 1", "ou-xxxx-xxxxxxx2": "OU 2", "ou-xxxx-xxxxxxx3": "OU 3", "ou-xxxx-xxxxxxx4": "OU 4"}')
cached_ou_names = json.loads(cached_ou_names_json)

assume_role_name = os.getenv('ASSUME_ROLE_NAME', 'AccountSwitcherLambdaRole')
file_path_prefix = os.getenv('FILE_PATH_PREFIX', '/tmp/')
manual_accounts_file_name = os.getenv('MANUAL_ACCOUNTS_FILE_NAME', 'accounts-not-yet-onboarded.dat')

def main(event, context):

    if event["Update"] == "True":

        payers = {
            "012345678901": "",
            "123456789012": "ACC1",
        }

        failed_payers = []
        accounts = {}

        for accountid, payer in payers.items():
            print("ID: " + accountid + " - Prefix: " + payer)
            client = False
            if accountid == "012345678901":
                # This is the local account
                client = boto3.client("organizations")
            else:
                try:
                    session = assume_role(accountid, "AccountSwitcherLambdaRole")
                    client = session.client("organizations")
                except ClientError as e:
                    print("Error Processing Payer {}".format(accountid))
                    failed_payers.append({accountid: repr(e)})
            try:
                if client == False:
                    continue
                payer_accounts = get_accounts(client, payer)
                accounts.update(payer_accounts)
            except ClientError as e:
                print("Error Processing Payer {}".format(accountid))
                failed_payers.append({accountid: repr(e)})

        roles = [
            "OrganizationAccountAccessRole",
            "MyOrg/ReadOnly",
            "MyOrg/Finance",
            "MyOrg/Administrator",
        ]

        for role in roles:
            create_config(role, accounts)

        if len(failed_payers) > 0:
            print("---------------------------------------------------------------")
            print("Failed Accounts")
            print("---------------------------------------------------------------")
            for p in failed_payers:
                print("{}: \n\t{}".format(list(p.keys())[0], p[list(p.keys())[0]]))
                print("---------------------------------------------------------------")

        return {"Success": True}


def assume_role(aws_account_number, role_name):
    """
    Assumes the provided role in each account and returns a GuardDuty client
    :param aws_account_number: AWS Account Number
    :param role_name: Role to assume in target account
    :param aws_region: AWS Region for the Client call, not required for IAM calls
    :return: GuardDuty client in the specified AWS Account and Region
    """

    # Beginning the assume role process for account
    sts_client = boto3.client("sts")

    # Get the current partition
    partition = sts_client.get_caller_identity()["Arn"].split(":")[1]

    response = sts_client.assume_role(
        RoleArn="arn:{}:iam::{}:role/{}".format(
            partition, aws_account_number, role_name
        ),
        RoleSessionName="RoleSwitcherLambda",
    )

    # Storing STS credentials
    session = boto3.Session(
        aws_access_key_id=response["Credentials"]["AccessKeyId"],
        aws_secret_access_key=response["Credentials"]["SecretAccessKey"],
        aws_session_token=response["Credentials"]["SessionToken"],
    )

    print("Assumed session for {}.".format(aws_account_number))

    return session


def get_accounts(client, prefix):
    accounts = {}

    paginator = client.get_paginator("list_accounts")
    response_iterator = paginator.paginate()

    cached_ou_names = {
        "ou-xxxx-xxxxxxx1": "OU 1",
        "ou-xxxx-xxxxxxx2": "OU 2",
        "ou-xxxx-xxxxxxx3": "OU 3",
        "ou-xxxx-xxxxxxx4": "OU 4",
    }

    for response in response_iterator:
        for acc in response["Accounts"]:
            if acc["Status"] == "ACTIVE":
                # Get a list of OUs for the account
                ous = list()
                itt = acc["Id"]
                for _ in range(10):
                    parent = client.list_parents(ChildId=itt, MaxResults=2)
                    length = sum(len(urllib.parse.quote(i)) for i in ous)
                    if length >= 63:
                        # Stop wasting time on API calls if we're over the limit of chars
                        break
                    if parent["Parents"][0]["Type"] == "ROOT":
                        break
                    elif parent["Parents"][0]["Id"] in cached_ou_names:
                        if cached_ou_names[parent["Parents"][0]["Id"]] == "Customers":
                            # Don't need "Customers" in the tree
                            break
                        # Skip a couple of API calls - Look at cached OU list
                        ous.insert(0, cached_ou_names[parent["Parents"][0]["Id"]])
                        break

                    else:
                        ouName = client.describe_organizational_unit(
                            OrganizationalUnitId=parent["Parents"][0]["Id"]
                        )
                        ous.insert(0, ouName["OrganizationalUnit"]["Name"])
                        itt = parent["Parents"][0]["Id"]
                        if len(ous) > 2:
                            # Give time for rate limits to cool off
                            time.sleep(0.1)
                if prefix != "":
                    ous.insert(0, prefix)
                acc["ous"] = ous
                accounts[acc["Id"]] = acc
    return accounts


def write_config(file, accountName, ID, role):
    file.write("[" + accountName + "]\n")
    file.write("aws_account_id = " + ID + "\n")
    file.write("role_name = " + role + "\n")
    if "-raw" in accountName:
        file.write("color = f7f300\n")
    elif "-prd" in accountName:
        file.write("color = f25800\n")
    elif "-uat" in accountName:
        file.write("color = 429321\n")
    elif "-stg" in accountName:
        file.write("color = 429321\n")
    elif "-ops" in accountName:
        file.write("color = 215693\n")
    elif "-operation" in accountName:
        file.write("color = 215693\n")
    elif "-dev" in accountName:
        file.write("color = 940633\n")
    else:
        file.write("color = dbdbdb\n")

    file.write("\n")
    return


def create_config(role, accounts, prefix=""):
    safeRoleName = role.replace("/", "-")

    accountIDs = list(accounts.keys())

    s3 = boto3.resource("s3")
    manualAccountsObj = s3.Object(
        "org-account-switcher-bucket", "accounts-not-yet-onboarded.dat"
    )
    manualAccounts = manualAccountsObj.get()["Body"].read().decode("utf-8").splitlines()

    # Create role for account switcher
    file = open("/tmp/" + safeRoleName + "_browser-plugin-config.txt", "w")

    # Process accounts from the .dat file
    for line in manualAccounts:
        accountName = "Manual / " + line.split(" ")[1]
        ID = line.split(" ")[0]
        write_config(file, accountName, ID, role)

    # Process accounts from the Org
    for ID in accountIDs:
        if accounts[ID].get("Status") == "ACTIVE":
            n = accounts[ID].get("Name").replace(" ", "_")
            accountName = ""
            for ou in accounts[ID]["ous"]:
                accountName += ou + " / "

                # Strip long account names (using percent encoding)
                if len(urllib.parse.quote(accountName + n, safe="")) >= 63:
                    length = 62 - len(urllib.parse.quote(n, safe=""))
                    accountName = accountName[:length]
                    length = (
                        62
                        - len(urllib.parse.quote(n, safe=""))
                        - (3 * accountName.count(" "))
                    )
                    accountName = accountName[:length]
                    length = (
                        62
                        - 12
                        - len(urllib.parse.quote(n, safe=""))
                        - (3 * accountName.count("/"))
                    )  # 12 is the encoded length of "... / "
                    accountName = accountName[:length] + "... / "
                    break

            accountName += n
            write_config(file, accountName, ID, role)

    file.close()

    file = open("/tmp/" + safeRoleName + "_awscli-config.txt", "w")

    for line in manualAccounts:
        accountName = line.split(" ")[1]
        ID = line.split(" ")[0]
        file.write("[" + accountName + "]\n")
        file.write("role_arn = arn:aws:iam::" + ID + ":role/" + role + "\n")
        file.write("source_profile = default\n")
        file.write("\n")

    for ID in accountIDs:
        if accounts[ID].get("Status") == "ACTIVE":
            accountName = accounts[ID].get("Name").replace(" ", "_")
            file.write("[" + accountName + "]\n")
            file.write("role_arn = arn:aws:iam::" + ID + ":role/" + role + "\n")
            file.write("source_profile = default\n")
            file.write("\n")

    file.close()

    file = open("/tmp/" + safeRoleName + "_awscli-config-prefixed.txt", "w")

    for line in manualAccounts:
        accountName = line.split(" ")[1]
        ID = line.split(" ")[0]
        file.write("[profile " + accountName + "]\n")
        file.write("role_arn = arn:aws:iam::" + ID + ":role/" + role + "\n")
        file.write("source_profile = default\n")
        file.write("\n")

    for ID in accountIDs:
        if accounts[ID].get("Status") == "ACTIVE":
            accountName = accounts[ID].get("Name").replace(" ", "_")
            file.write("[profile " + accountName + "]\n")
            file.write("role_arn = arn:aws:iam::" + ID + ":role/" + role + "\n")
            file.write("source_profile = default\n")
            file.write("\n")

    file.close()

    s3.Object(
        "org-account-switcher-bucket", safeRoleName + "/browser-plugin-config.txt"
    ).upload_file("/tmp/" + safeRoleName + "_browser-plugin-config.txt")
    s3.Object(
        "org-account-switcher-bucket", safeRoleName + "/awscli-config.txt"
    ).upload_file("/tmp/" + safeRoleName + "_awscli-config.txt")
    s3.Object(
        "org-account-switcher-bucket", safeRoleName + "/awscli-config-prefixed.txt"
    ).upload_file("/tmp/" + safeRoleName + "_awscli-config-prefixed.txt")

    return True
