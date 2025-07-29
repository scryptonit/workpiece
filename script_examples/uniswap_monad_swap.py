# UNISWAP MONAD-TESTNET MON/CHOG SWAP
# =================================================================================================================
# Скопируйте этот файл в корневую папку проекта
# Copy this file to the root directory of the project
# =================================================================================================================


import os
import random
import asyncio
import time
from core.get_token_rate import get_token_ratio_wei
from web3 import Web3
from loguru import logger
from core.get_wallets_data import get_wallets
from core.tx_manager import TX_MANAGER
from core.settings import evm_lines, proxy_lines, RPC_URL, RESULTS_DIR, LOG_DIR

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

            txm = TX_MANAGER(
                chain_name="monad",
                private_key=private_key,
                proxy_string=proxy
            )

            #################################################################
            # SWAP Configuration
            slip_rate = 0.005  # 0.5%
            min_eth, max_eth = 0.05, 0.1  # ETH (MON) input range

            # Addresses normalization
            address_for_data = address.lower()[2:]
            token_contract_in = "0x760AfE86e5de5fa0Ee542fc7B7B713e1c5425701".lower()[2:] # WMON
            token_contract_out = "0xE0590015A873bF326bd645c3E1266d4db41C4E6B".lower()[2:] # CHOG
            pool_contract = "0xc0ce32eee0eb8bf24fa2b00923a78abc5002f91e" # WMON/CHOG uniswap pool

            # input amount
            amount_in = round(random.uniform(min_eth, max_eth), 6)
            value = Web3.to_wei(amount_in, "ether")  # to wei
            hex_amount_in = hex(value)[2:]

            # output amount
            _, rate = get_token_ratio_wei('monad-testnet', pool_contract)
            amount_out = int(amount_in * rate)
            min_amount_out = int(amount_out * (1 - slip_rate))
            hex_min_amount_out = hex(min_amount_out)[2:]
            #################################################################
            nonce = txm.get_nonce()
            gas = txm.get_gas_fees()
            data = f'''
            0x3593564c
            0000000000000000000000000000000000000000000000000000000000000060
            00000000000000000000000000000000000000000000000000000000000000a0
            {deadline(1800).zfill(64)}
            0000000000000000000000000000000000000000000000000000000000000002
            0b00000000000000000000000000000000000000000000000000000000000000
            0000000000000000000000000000000000000000000000000000000000000002
            0000000000000000000000000000000000000000000000000000000000000040
            00000000000000000000000000000000000000000000000000000000000000a0
            0000000000000000000000000000000000000000000000000000000000000040
            0000000000000000000000000000000000000000000000000000000000000002
            {hex_amount_in.zfill(64)}
            0000000000000000000000000000000000000000000000000000000000000100
            {address_for_data.zfill(64)}
            {hex_amount_in.zfill(64)}
            {hex_min_amount_out.zfill(64)}
            00000000000000000000000000000000000000000000000000000000000000a0
            0000000000000000000000000000000000000000000000000000000000000000
            000000000000000000000000000000000000000000000000000000000000002b
            {token_contract_in}000064{token_contract_out}
            000000000000000000000000000000000000000000
            0c
            '''
            data = data.replace('\n', '').replace(' ', '')


            to_address = Web3.to_checksum_address("0x3aE6D8A282D67893e17AA70ebFFb33EE5aa65893")

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

            tx_hash = txm.send_transaction(tx, description=f"Transaction for {address}")

            await asyncio.sleep(random.randint(10, 12))

            receipt = await txm.check_transaction_status(tx_hash)
            if receipt and receipt.get("status") == 1:
                logger.info(f"Confirmed: {tx_hash.hex()}")
                save_result(RESULT_FILE, address)
                await asyncio.sleep(random.randint(10, 15))
            else:
                logger.error(f"Transaction status error: {tx_hash.hex()}")

        except Exception as e:
            logger.error(f"{address}: {e}")
            continue


if __name__ == "__main__":
    asyncio.run(process_transactions())
    logger.info("Execution completed.")
