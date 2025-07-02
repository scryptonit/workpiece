# 🧠 Web3-Farm: Airdrop Automation on Python

This is a personal Web3 automation farm project that helps you send transactions (like minting NFTs or claiming airdrops) **without using a browser or extensions**. All logic is written in plain Python using `web3.py`.

---

## ⚙️ Features

- ✅ Mass transaction processing
- 🌐 Supports any EVM-compatible network via RPC
- 🔐 Secure wallet decryption from encrypted file
- 🔄 Proxy support for each wallet (e.g. ThunderProxy)
- 📁 Logs and results saved automatically by script

---

## 📁 Project Structure

```
workpiece/
├── config/
│   ├── evm.txt         # Wallet addresses
│   ├── proxies.txt     # Corresponding proxies
│   └── rpc.txt         # Chain name to RPC mapping
├── core/
│   ├── get_token_rate_coingecko.py # Fetch price data from CoingeckoTerminal
│   ├── get_wallets_data.py
│   ├── settings.py
│   └── tx_manager.py
├── utils/
│   └── data_comparison.py # Мisually compares two callData hex strings
├── logs/               # Script logs
├── results/            # Per-script transaction results
├── .env                # Environment config
└── main_example.py     # Template script for transactions
```

---

## 🧪 .env Example

```env
ENCRYPTED_WALLETS_PATH=/path/to/your/encrypted/wallets.csv.enc
WALLET_KEY_PATH=/path/to/your/keyfile.key       # Only if using USB mode
WALLET_SOURCE=keychain                          # Or: usb
USE_PROXY=true                                  # Or: false

```

---

## 🚀 Quick Start

1. **Install dependencies**  
   (You should have Python 3.9+ and `pip` installed)

   ```bash
   pip install -r requirements.txt
   ```

2. **Create `.env`** file (see example above)

3. **Prepare config files:**
   - `evm.txt`: one wallet address per line
   - `proxies.txt`: one proxy per line (same order as addresses)
      host:port:username:password 
   - `rpc.txt`: chain_name,https://rpc-url

4. **Create a script** based on `main_example.py`:
   - Set `chain_name`
   - Set contract address and calldata (`to`, `data`)
   - Set transaction `value`

5. **Run it**:

   ```bash
   python main_example.py
   ```

---

## 📌 Notes

- Use **testnets** first (MegaETH, Monad, etc.) before moving to mainnet
- No advanced Python required: no OOP, no decorators, no frameworks — just logic
- Project is modular and will grow: swaps, bridges, LPs coming next

---

## 📺 Video Guide

Watch on YouTube: **https://www.youtube.com/@scryptoni**  
And on Telegram channel: [@scryptonia](https://t.me/+FuS4BPeF_6RmNjk8)
