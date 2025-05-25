import random
import asyncio
from web3 import Web3
from loguru import logger
import primp
from core.settings import get_rpc_url, USE_PROXY

class TX_MANAGER:
    def __init__(self, address, proxy_string=None, chain_name=None, rpc_url=None):
        if not rpc_url and not chain_name:
            raise ValueError("You must specify either rpc_url or chain_name")

        self.address = Web3.to_checksum_address(address)
        valid_versions = [f"chrome_{v}" for v in range(128, 134) if v != 132]
        chosen_version = random.choice(valid_versions)

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

    def send_transaction(self, signed_txn):
        return self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)

    def get_nonce(self):
        return self.w3.eth.get_transaction_count(self.address)

    async def check_transaction_status(self, tx_hash, attempts=3, delay=30):
        for attempt in range(attempts):
            try:
                receipt = self.w3.eth.get_transaction_receipt(tx_hash)
                if receipt:
                    return receipt
            except Exception as e:
                logger.warning(f"Attempt {attempt+1}: failed to retrieve status for {tx_hash.hex()}: {e}")
            await asyncio.sleep(delay)
        return None


