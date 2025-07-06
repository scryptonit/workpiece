import os
import random
import asyncio
import time
from web3 import Web3
from loguru import logger
from core.get_wallets_data import get_wallets
from core.tx_manager import TX_MANAGER
from core.settings import evm_lines, proxy_lines, RESULTS_DIR, LOG_DIR

script_name = os.path.splitext(os.path.basename(__file__))[0]

RESULT_FILE = os.path.join(RESULTS_DIR, f"{script_name}.txt")
LOG_FILE = os.path.join(LOG_DIR, f"{script_name}.log")

os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

logger.add(LOG_FILE, format="{time} {level} {message}", level="INFO")

def load_processed(path):
    processed = {}
    if os.path.exists(path):
        with open(path, "r") as f:
            for line in f:
                try:
                    addr, status = line.strip().split(";")
                    processed[addr] = int(status)
                except:
                    continue
    return processed

def save_result(path, address):
    processed = load_processed(path)
    processed[address] = processed.get(address, 0) + 1
    with open(path, "w") as f:
        for addr, stat in processed.items():
            f.write(f"{addr};{stat}\n")

def deadline(seconds):
    return hex(int(time.time()) + seconds)[2:]


async def process_transactions():
    wallets = get_wallets()
    processed = load_processed(RESULT_FILE)
    random.shuffle(wallets)

    for address, private_key in wallets:
        try:
            address = Web3.to_checksum_address(address)

            if processed.get(address, 0) >= 1:
                logger.info(f"{address} already processed. Skipping.")
                continue

            if address not in evm_lines:
                logger.warning(f"{address} not found in evm.txt. Skipping.")
                continue

            proxy = proxy_lines[evm_lines.index(address)]
            #####################################################################
            chain_name = ''
            data = ''
            value = Web3.to_wei("0", "ether")
            to_address = Web3.to_checksum_address("")
            #####################################################################
            
            txm = TX_MANAGER(
                chain_name=chain_name,
                address=address,
                proxy_string=proxy
            )

            nonce = txm.get_nonce()
            gas = txm.get_gas_fees()

            tx = {
                "chainId": txm.chain_id,
                "data": data,
                "from": address,
                "to": to_address,
                "nonce": nonce,
                "value": value,
                **gas
            }

            tx["gas"] = int(txm.w3.eth.estimate_gas(tx) * random.uniform(1.12, 1.15))

            signed = txm.w3.eth.account.sign_transaction(tx, private_key)
            tx_hash = txm.send_transaction(signed)

            logger.info(f"Transaction sent | {address}. {tx_hash.hex()}")
            await asyncio.sleep(random.randint(15, 30))

            receipt = await txm.check_transaction_status(tx_hash)
            if receipt and receipt.get("status") == 1:
                logger.info(f"Confirmed: {tx_hash.hex()}")
                save_result(RESULT_FILE, address)
                await asyncio.sleep(random.randint(100, 150))
            else:
                logger.error(f"Transaction status error: {tx_hash.hex()}")

        except Exception as e:
            logger.error(f"{address}: {e}")
            continue


if __name__ == "__main__":
    asyncio.run(process_transactions())
    logger.info("Execution completed.")
