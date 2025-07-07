# https://testnet.monad.xyz/ NATIVE_SWAP 
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
            address_for_data = address.lower()[2:]

########################################################################################################################

            # SWAP Configuration
            slip_rate = 0.005
            min_eth, max_eth = 0.005, 0.01  # ETH (MON) input range

            # Addresses normalization
            token_contract_in = "0x760AfE86e5de5fa0Ee542fc7B7B713e1c5425701".lower()[2:]

            token_pools = {
                "0x0f0bdebf0f83cd1ee3974779bcb7315f9808c714": "0x6e4b7be5ef7f8950c76baa0bd90125bc9b33c8db",#DAK
                "0xe0590015a873bf326bd645c3e1266d4db41c4e6b": "0xc0ce32eee0eb8bf24fa2b00923a78abc5002f91e", #CHOG
                "0xfe140e1dce99be9f4f15d657cd9b7bf622270c50": "0x212fde77a42d55f980d0a0304e7eebe1e999c60f" #YAKI
            }

            token_contract_out = random.choice(list(token_pools.keys()))
            pool_contract = token_pools[token_contract_out]
            token_contract_out = token_contract_out.lower()[2:]

            if pool_contract == "0x6e4b7be5ef7f8950c76baa0bd90125bc9b33c8db":
                symbol = "DAK"
            elif pool_contract == "0xc0ce32eee0eb8bf24fa2b00923a78abc5002f91e":
                symbol = "CHOG"
            else:
                symbol = "YAKI"

            logger.info(f"Selected token: {symbol}, contract: {token_contract_out}, pool: {pool_contract}")

            # input amount
            amount_in = round(random.uniform(min_eth, max_eth), 6)
            value = Web3.to_wei(amount_in, "ether")  # to wei
            hex_amount_in = hex(value)[2:]

            # output amount
            _, rate = get_token_ratio_wei('monad-testnet', pool_contract)
            amount_out = int(amount_in * rate)
            min_amount_out = int(amount_out * (1 - slip_rate))
            hex_min_amount_out = hex(min_amount_out)[2:]

            # tx configuration
            chain_name = 'monad'
            to_address = Web3.to_checksum_address("0x4c4eABd5Fb1D1A7234A48692551eAECFF8194CA7")

            #********************************************************************************************#
            data = f'''
            0x5ae401dc
            {deadline(1186).zfill(64)}
            0000000000000000000000000000000000000000000000000000000000000040
            0000000000000000000000000000000000000000000000000000000000000001
            0000000000000000000000000000000000000000000000000000000000000020
            00000000000000000000000000000000000000000000000000000000000000e4472b43f3
            {hex_amount_in.zfill(64)}
            {hex_min_amount_out.zfill(64)}
            0000000000000000000000000000000000000000000000000000000000000080
            {address_for_data.zfill(64)}
            0000000000000000000000000000000000000000000000000000000000000002
            {token_contract_in.zfill(64)}
            {token_contract_out.zfill(64)}
            00000000000000000000000000000000000000000000000000000000
            '''
########################################################################################################################

            data = data.replace('\n', '').replace(' ', '')

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
