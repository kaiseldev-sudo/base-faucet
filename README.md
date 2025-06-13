# Base Sepolia Faucet Claimer

A web-based tool for automatically claiming ETH from the Base Sepolia faucet. This tool provides a user-friendly interface to manage multiple wallet addresses and automatically claims ETH every 24 hours.

## Features

- Web interface for easy management
- Support for multiple wallet addresses
- Real-time progress updates
- Automatic claiming every 24 hours
- Transaction tracking with Base Sepolia explorer links
- Error handling and rate limit management

## Prerequisites

- Python 3.8 or higher
- CDP API credentials (API Key ID and Secret)

## Installation

1. Clone the repository:
```bash
git clone <your-repository-url>
cd faucet
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root with your CDP API credentials:
```
CDP_API_KEY_ID="your_api_key_id_here"
CDP_API_KEY_SECRET="your_api_key_secret_here"
```

## Usage

1. Start the application:
```bash
python index.py
```

2. Open your web browser and navigate to:
```
http://localhost:5000
```

3. In the web interface:
   - Enter your wallet address (must be a valid Ethereum address)
   - Set your target ETH amount (between 0.0001 and 1 ETH)
   - Click "Start Claiming"

4. Monitor the progress in the real-time log window

## Important Notes

- The wallet address must be a valid Ethereum address (starting with 0x)
- Target amount must be between 0.0001 and 1 ETH
- The faucet has daily limits per address and API key
- You can run multiple claiming sessions for different wallets simultaneously

## Security

- Never commit your `.env` file to version control
- Keep your CDP API credentials secure
- The application runs locally on your machine

## License

[Your chosen license]

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 