import json
import random
import asyncio
from web3 import Web3
from loguru import logger
import primp
from core.settings import get_rpc_url, USE_PROXY
from pathlib import Path

ERC20_ABI_PATH = "abis/ERC20.json"

class TX_MANAGER:
    def __init__(self, private_key: str, proxy_string=None, chain_name=None, rpc_url=None):
        if not rpc_url and not chain_name:
            raise ValueError("You must specify either rpc_url or chain_name")

        valid_versions = [f"chrome_{v}" for v in range(128, 134) if v != 132]
        chosen_version = random.choice(valid_versions)

        self.private_key = private_key
        self.account = Web3().eth.account.from_key(private_key)
        self.address = Web3.to_checksum_address(self.account.address)

        self.headers = None
        formatted_proxy = None

        if USE_PROXY:
            if not proxy_string:
                raise ValueError("Proxy is enabled in settings, but no proxy_string was provided.")
            host, port, user, password = proxy_string.strip().split(":")
            formatted_proxy = f"http://{user}:{password}@{host}:{port}"

            self.client = primp.Client(
                impersonate=chosen_version,
                impersonate_os="macos",
                proxy=formatted_proxy
            )
            self.headers = self.client.headers
        else:
            self.client = primp.Client(
                impersonate=chosen_version,
                impersonate_os="macos"
            )
            self.headers = self.client.headers

        self.rpc_url = rpc_url or get_rpc_url(chain_name)

        proxy_kwargs = {
            "proxies": {
                "http": formatted_proxy,
                "https": formatted_proxy
            }
        } if USE_PROXY else {}

        self.w3 = Web3(Web3.HTTPProvider(
            self.rpc_url,
            request_kwargs={
                "headers": self.headers,
                **proxy_kwargs
            }
        ))

        self.chain_id = self.w3.eth.chain_id
        self.erc20_abi = self._load_abi(ERC20_ABI_PATH)


    def supports_eip1559(self):
        try:
            return "baseFeePerGas" in self.w3.eth.fee_history(1, "latest", [20])
        except:
            return False

    def get_gas_fees(self):
        if self.supports_eip1559():
            fee_history = self.w3.eth.fee_history(5, "latest", [50])
            base_fee = fee_history["baseFeePerGas"][-1]
            rewards = [r[0] for r in fee_history["reward"] if r]
            if rewards:
                rewards.sort()
                mid = len(rewards) // 2
                priority = rewards[mid] if len(rewards) % 2 else (rewards[mid - 1] + rewards[mid]) // 2
                priority = int(priority * random.uniform(1.03, 1.1))
            else:
                priority = int(base_fee * 0.1)
            return {
                "maxPriorityFeePerGas": priority,
                "maxFeePerGas": max(base_fee + priority, int(base_fee * 1.15))
            }
        else:
            return {"gasPrice": int(self.w3.eth.gas_price * random.uniform(1.05, 1.1))}


    def get_nonce(self):
        return self.w3.eth.get_transaction_count(self.address)

    def send_transaction(self, tx: dict, description: str = "Transaction"):
        signed_tx = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        logger.info(f"{description} sent. Transaction hash: {tx_hash.hex()}")
        return tx_hash

    async def check_transaction_status(self, tx_hash, attempts=3, delay=10):
        for attempt in range(attempts):
            await asyncio.sleep(delay)
            try:
                receipt = self.w3.eth.get_transaction_receipt(tx_hash)
                if receipt:
                    return receipt
            except Exception as e:
                logger.warning(f"Attempt {attempt+1}: failed to retrieve status for {tx_hash.hex()}: {e}")

        return None
    @staticmethod
    def _load_abi(path_str):
        path = Path(path_str)
        if not path.exists():
            logger.error(f"ABI file not found at path: {path}")
            raise FileNotFoundError(f"ABI file not found at {path}")
        with open(path, "r") as f:
            abi = json.load(f)
            logger.info(f"ABI loaded successfully from {path}")
            return abi

    def get_contract(self, contract_address: str, abi: dict = None):
        if abi is None:
            abi = self.erc20_abi

        return self.w3.eth.contract(address=Web3.to_checksum_address(contract_address), abi=abi)

    def get_native_balance(self):
        try:
            balance_wei = self.w3.eth.get_balance(self.address)
            return balance_wei, self.w3.from_wei(balance_wei, 'ether')
        except Exception as e:
            logger.error(f"Failed to get native balance for {self.address}: {e}")
            return 0, 0.0

    def get_token_balance(self, token_address):
        try:
            contract = self.get_contract(token_address)
            balance_raw = contract.functions.balanceOf(self.address).call()
            decimals = contract.functions.decimals().call()
            return balance_raw, balance_raw / (10 ** decimals)
        except Exception as e:
            logger.error(f"Failed to get token balance for {token_address}: {e}")
            return 0, 0.0

    def get_allowance(self, token_address, spender_address):
        try:
            contract = self.get_contract(token_address)
            allowance = contract.functions.allowance(self.address, Web3.to_checksum_address(spender_address)).call()
            return allowance
        except Exception as e:
            logger.error(f"Failed to get allowance for spender {spender_address}: {e}")
            return 0

    async def ensure_allowance(self, token_address: str, spender_address: str, amount_needed: int):
        log = logger.bind(wallet=self.address, token=token_address, spender=spender_address)
        try:
            current_allowance = self.get_allowance(token_address, spender_address)
            if current_allowance >= amount_needed:
                log.info(f"Allowance is sufficient ({current_allowance} >= {amount_needed}). No action needed.")
                return True

            log.warning(f"Insufficient allowance ({current_allowance} < {amount_needed}). Proceeding with new approval.")
            amount_to_approve = amount_needed
            contract = self.get_contract(token_address)

            tx_data = {
                "from": self.address,
                "nonce": self.get_nonce(),
                "value": 0,
                **self.get_gas_fees()
            }

            log.info(f"Building transaction to approve exact amount: {amount_to_approve}")
            approve_tx = contract.functions.approve(
                Web3.to_checksum_address(spender_address),
                amount_to_approve
            ).build_transaction(tx_data)

            tx_hash = self.send_transaction(approve_tx, description=f"Approve transaction for {amount_to_approve}")
            receipt = await self.check_transaction_status(tx_hash)

            if receipt and receipt.get("status") == 1:
                log.success("Approve transaction for exact amount confirmed successfully.")
                return True
            else:
                status = receipt.get('status') if receipt else 'Not found'
                log.error(f"Approve transaction failed or timed out. Status: {status}")
                return False
        except Exception:
            log.exception("A critical error occurred during the ensure_allowance process.")
            return False
