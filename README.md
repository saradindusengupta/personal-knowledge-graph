# Project Name

Please run `Bootstrap Project` GitHub Action to bootstrap the project which will perform the following task

- It defines the events that trigger the workflow, such as pushes or pull requests, and specifies the jobs and steps to be executed in response.
- The workflow may include actions like checking out code, setting up environments, running tests, building artifacts, or deploying applications.
- Each job runs in a fresh virtual environment and can be configured with specific runners, environment variables, and dependencies.
- Customize this workflow to fit your project's CI/CD requirements.

## Structure of the Repository

This repository uses `setuptool` to create packages and uses `toml` file for package configuration

```text
├── Dockerfile               # The file to build a container using build a or docker container
├── CONTRIBUTING.md          # Onboarding instructions for new contributors
├── docs                     # Documentation site (PyDocs)
├── .github                  # Github metadata for repository
│   ├── release_message.sh   # A script to generate a release message
│   ├── ISSUE_TEMPLATE       # Templates
│   └── workflows            # The CI pipeline for Github Actions
├── .gitignore               # A list of files to ignore when pushing to Github
├── HISTORY.md               # Auto generated list of changes to the project
├── LICENSE                  # The license for the project
├── Makefile                 # A collection of utilities to manage the project
├── MANIFEST.in              # A list of files to include in a package
├── src/{project_name}       # The main python package for the project
│   ├── __init__.py          # This tells Python that this is a package
│   ├── info.py              # Project info [Author, version]
├── data                     # Required data
├── notebooks                # Jupyter Notebooks for the project
├── config                   # Required configuration files
├── README.md                # The main readme for the project
├── requirements.txt         # List of requirements for the project
├── requirements-test.txt    # List of requirements for testing and development
├── pyproject.toml           # The file for installing and packaging the project
└── tests                    # Unit tests for the project (add mote tests files here)
    ├── data                 # Data and fixtures for pytest
    ├── __init__.py          # This tells Python that this is a test package
    ├── conftest.py          # Configuration, hooks and fixtures for pytest
    └── test_base.py         # The base test case for the project
```
