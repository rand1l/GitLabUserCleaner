# GitLab User Cleaner

GitLab User Cleaner is a Python tool that automates the removal of blocked and banned users from GitLab groups and projects using the GitLab API. It efficiently scans all users, detects inactive accounts, and removes them from all associated groups and projects.

## Features

- **Automated user cleanup** – Removes blocked and banned users from GitLab.
- **Asynchronous processing** – Uses `aiohttp` for efficient API requests.
- **Environment-based configuration** – Secure and flexible setup using environment variables.
- **Docker support** – Run the script easily in a containerized environment.

## Installation

```bash
pip install aiohttp
