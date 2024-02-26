<p align="center">
  <img src="https://raw.githubusercontent.com/PKief/vscode-material-icon-theme/ec559a9f6bfd399b82bb44393651661b08aaf7ba/icons/folder-aws-open.svg" width="100" />
</p>
<p align="center">
    <h1 align="center">Switch Roles Lambda</h1>
</p>
<p align="center">
    <em>Automatically generate your AWS account configurations through AWS Organizations </em>
</p>
<p align="center">
	<!-- local repository, no metadata badges. -->
<p>
<p align="center">
	<img src="https://img.shields.io/badge/Python-3776AB.svg?style=flat&logo=Python&logoColor=white" alt="Python">
	<img src="https://img.shields.io/badge/GitHub%20Actions-2088FF.svg?style=flat&logo=GitHub-Actions&logoColor=white" alt="GitHub%20Actions">
</p>
<hr>

##  Quick Links

> - [Overview](#overview)
> - [Getting Started](#getting-started)
>   - [Installation](#installation)
>   - [Running switchroles-lambda](#running-switchroles-lambda)
> - [Contributing](#contributing)
> - [License](#license)

---

## Overview

The switchroles-lambda project leverages AWS Lambda to streamline the generation of AWS configurations for accounts in Organizations. It provides a flexible and scalable solution for managing AWS resources across multiple accounts and regions. It is designed with [AWS Extend Switch Roles](https://chromewebstore.google.com/detail/aws-extend-switch-roles/jpmkfafbacpgapdghgdpembnojdlgkdl) and [AESR S3 Config Sender](https://github.com/XargsUK/aesr-s3-config-sender/) in mind. 


---

## Getting Started

***Requirements***

Ensure you have the following dependencies installed on your system:

* **Python**: `version 3.10.12`
* **boto3**: `version 1.34.43`

### Installation

1. Clone the switchroles-lambda repository:

```sh
git clone git@github.com:XargsUK/switchroles-lambda.git
```

2. Change to the project directory:

```sh
cd switchroles-lambda
```

3. Install the dependencies:

```sh
pip install -r requirements.txt
```

### Running `switchroles-lambda`

This python script can be run locally or deployed as an AWS Lambda function. 

| Name              | Description                                                    | Example                                             |
|-------------------|----------------------------------------------------------------|-----------------------------------------------------|
| S3_BUCKET         | The name of the S3 bucket where the configurations will be stored (if not running locally).                            | `awsconfigs-bucket`                                 |
| ASSUME_ROLE  | The role name to be assumed in each payer account.        | `AccountSwitcherLambdaRole`                         |
| ROLE_NAMES        | Comma-separated role names for which the configurations will be generated.                            | `Admin,Developer,ReadOnly` |
| SESSION_NAME      |  The session name to use when assuming roles. | `RoleSwitcherLambdav2`                              |
| PAYER_ACCOUNT_IDS | Comma-separated AWS payer account IDs.                                        | `123456789012,210987654321`                       |
| OU_OVERRIDES      | JSON string of organizational unit (OU) ID to name mappings for overrides. | `{"ou-xyz1-abcdefgh":"Engineering","ou-xyz2-abcdefgh":"Marketing"}`                            |
| running_locally   | Set true for Local execution, false for Lambda.                | `true`                                              |
| AWS_REGION        | The AWS region to use for the Lambda function.                | `us-west-2`                                         |
| AWS_PROFILE       | The AWS profile to use for the Lambda function.                | `default`                                           |

#### Local Execution

Start by setting your environment variables:

```sh
export running_locally=true
export S3_BUCKET=S3_BUCKET_NAME
...
```

Once you've set your environment variables the following command to run switchroles-lambda:

```sh
python lambda_handler.py
```

## Contributing

Contributions are welcome! Here are several ways you can contribute:

- **[Submit Pull Requests](https://github.com/xargsuk/switchroles-lambda/blob/main/CONTRIBUTING.md)**: Review open PRs, and submit your own PRs.
- **[Report Issues](https://github.com/xargsuk/switchroles-lambda/issues)**: Submit bugs found or log feature requests for the `switchroles-lambda` project.


### Contributing Guidelines

1. **Fork the Repository**: Start by forking the project repository to your local account.
2. **Clone Locally**: Clone the forked repository to your local machine using a git client.
   ```sh
   git clone `repo_url`
   ```
3. **Create a New Branch**: Always work on a new branch, giving it a descriptive name.
   ```sh
   git checkout -b new-feature-x
   ```
4. **Make Your Changes**: Develop and test your changes locally.
5. **Commit Your Changes**: Commit with a clear message describing your updates.
   ```sh
   git commit -m 'Implemented new feature x.'
   ```
6. **Push to GitHub**: Push the changes to your forked repository.
   ```sh
   git push origin new-feature-x
   ```
7. **Submit a Pull Request**: Create a PR against the original project repository. Clearly describe the changes and their motivations.

Once your PR is reviewed and approved, it will be merged into the main branch.

---

## License

This project is protected under the [MIT](https://choosealicense.com/licenses/mit/) License. 

---