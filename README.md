# ERC4626

[![Ape Framework](https://img.shields.io/badge/Built%20with-Ape%20Framework-brightgreen.svg)](https://apeworx.io)
[![Ape Academy](https://img.shields.io/badge/Ape%20Academy-ERC20%20template-yellow.svg)](https://github.com/ApeAcademy/ERC20)

<!-- Your Description Goes Here -->

# Silverback Yield Bot

This project uses the Silverback framework to run a bot that interacts with a SQLite database. This guide will help you set up your environment and run the bot.

## Prerequisites

- Python 3.8 or higher
- `pip` (Python package installer)
- [Silverback](https://github.com/ApeWorX/silverback) framework installed

## Setup Instructions

### 1. Create the Data Directory

You need a directory to store the SQLite database. Follow these steps to create it:

```bash
sudo mkdir /data
sudo chown $USER:$USER /data  # Replace $USER with your username if necessary
```

### 2. Set Up Environment Variables

Create a .env file in your project directory to define environment variables with `touch .env`

Add variables like these to the file:

```bash
WEB3_ALCHEMY_PROJECT_ID=
ERC4626_VAULT_ADDRESS=
ETHERSCAN_API_KEY=
DATABASE_URL=sqlite:////data/ilovesilverback.db
SILVERBACK_BROKER_KWARGS='{"queue_name": "taskiq", "url": "redis://redis:6379"}'
```

### 3. Install Dependencies

Ensure you have all necessary dependencies installed. You can typically do this with: `pip install -r requirements.txt`

### 4. Run the Bot

Once the setup is complete, you can run your bot using the Silverback CLI. Use the following command: `silverback run bots.silverback_yield:app`

### 5. Verify Database Creation

The SQLite database file should automatically be created in the /data/ directory when the bot is run for the first time. You can verify its existence by checking the contents of the directory `ls /data`

### 3. Troubleshooting

If you encounter permission issues, double-check the ownership and permissions of the /data directory.
Ensure your .env file is properly formatted and located in the root of your project.