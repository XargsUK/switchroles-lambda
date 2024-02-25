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

> - [ Overview](#-overview)
> - [ Features](#-features)
> - [ Repository Structure](#-repository-structure)
> - [ Modules](#-modules)
> - [ Getting Started](#-getting-started)
>   - [ Installation](#-installation)
>   - [Running switchroles-lambda](#-running-switchroles-lambda)
> - [ Contributing](#-contributing)
> - [ License](#-license)

---

##  Overview

The switchroles-lambda project leverages AWS Lambda to streamline the generation of AWS configurations for accounts in Organizations. It provides a flexible and scalable solution for managing AWS resources across multiple accounts and regions. It is designed with [AWS Extend Switch Roles](https://chromewebstore.google.com/detail/aws-extend-switch-roles/jpmkfafbacpgapdghgdpembnojdlgkdl) and [AESR S3 Config Sender](https://github.com/XargsUK/aesr-s3-config-sender/) in mind. 

---

##  Features

|    |   Feature         | Description |
|----|-------------------|---------------------------------------------------------------|
| ⚙️  | **Architecture**  | The project follows a modular architecture utilizing AWS Lambda for serverless deployment.  |
| 🧪 | **Testing**       | Testing frameworks include Moto for mock AWS services and responses for HTTP testing. |
| ⚡️  | **Performance**   | The project demonstrates efficient resource utilization, optimizing execution speed and minimizing runtime overhead.  |
| 📦 | **Dependencies**  | Key libraries and dependencies include Werkzeug, boto3, cryptography, and pydantic for enhanced functionality and data validation. These dependencies are crucial for seamless integration and execution. |


---

##  Repository Structure

```sh
└── switchroles-lambda/
    ├── LICENSE
    ├── lambda_handler.py
    ├── requirements.txt
    └── testlambda.py
```

---

##  Getting Started

***Requirements***

Ensure you have the following dependencies installed on your system:

* **Python**: `version 3.10.12`

###  Installation

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

###  Running `switchroles-lambda`

This python script can be run locally or deployed as an AWS Lambda function. 

| Name              | Description                                                    | Example                                             |
|-------------------|----------------------------------------------------------------|-----------------------------------------------------|
| s3_bucket         | Name of the S3 bucket to export to.                            | `awsconfigs-bucket`                                 |
| assume_role_name  | Name of role used to assume into Management Accounts           | `AccountSwitcherLambdaRole`                         |
| role_names        | Role names to generate configs for                             | `OrganizationAccountAccessRole,ManagedOrg/ReadOnly` |
| session_name      | Session name when assuming the role in the management acccount | `RoleSwitcherLambdav2`                              |
| payer_account_ids | List of AWS account IDs                                        | `0123456789012,1234567890123`                       |
| running_locally   | Set true for Local execution, false for Lambda.                | `true`                                              |

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


##  Contributing

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

##  License

This project is protected under the [MIT](https://choosealicense.com/licenses/mit/) License. 

---

