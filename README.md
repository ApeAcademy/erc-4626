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

### 1. Set Up Environment Variables

Create a .env file in your project directory to define environment variables with `touch .env`

Add variables like these to the file:

```bash
WEB3_ALCHEMY_PROJECT_ID=
ERC4626_VAULT_ADDRESS=
```

### 2. Install Dependencies

Ensure you have all necessary dependencies installed. You can typically do this with: `pip install -r requirements.txt`

Ensure you have all necessary dependencies installed. You can typically do this with: 
`ape plugins install . -U`

Ensure that your `ape-config.yaml` default network is mainnet and alchemy.

### 3. Run the Bot

Once the setup is complete, you can run your bot using the Silverback CLI. Use the following command: `silverback run bots.silverback_yield:bot`

### Troubleshooting

* Ensure your .env file is properly formatted and located in the root of your project.

* FileNotFoundError: The bots directory '/path/to/silverback/bots' does not exist. You should have a `bots/` folder in the root of your project.