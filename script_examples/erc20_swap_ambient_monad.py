# AMBIENT MONAD-TESTNET CHOG/MON SWAP
# =================================================================================================================
# Скопируйте этот файл в корневую папку вашего проекта
# Copy this file to the root directory of your project
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
            # tx configuration
            chain_name = 'monad'
            to_address = Web3.to_checksum_address("0x88B96aF200c8a9c35442C8AC6cd3D22695AaE4F0")
            txm = TX_MANAGER(
                chain_name=chain_name,
                private_key=private_key,
                proxy_string=proxy
            )

            # SWAP Configuration
            slip_rate = 0.05

            # Addresses normalization
            token_contract_in = "0xe0590015a873bf326bd645c3e1266d4db41c4e6b"
            hex_token_contract_in = token_contract_in.lower()[2:]

            # token_contract_out = "".lower()[2:]
            pool_contract = "0x4d2e4c5ff07d1c82d512335dea0a1aa82c031a86"

            # input amount
            token_in_balance, _ = txm.get_token_balance(token_contract_in)
            amount_in = int(round(token_in_balance * random.uniform(0.05, 0.1), -13))
            hex_amount_in = hex(amount_in)[2:]

            # output amount
            rate, _ = get_token_ratio_wei('monad-testnet', pool_contract)
            amount_out = int(Web3.from_wei(amount_in,"ether") * rate)
            min_amount_out = int(amount_out * (1 - slip_rate))
            hex_min_amount_out = hex(min_amount_out)[2:]



            # ********************************************************************************************#
            data = f'''
            0xa15112f9
            0000000000000000000000000000000000000000000000000000000000000001
            0000000000000000000000000000000000000000000000000000000000000040
            0000000000000000000000000000000000000000000000000000000000000140
            0000000000000000000000000000000000000000000000000000000000000000
            {hex_token_contract_in.zfill(64)}
            0000000000000000000000000000000000000000000000000000000000008ca0
            0000000000000000000000000000000000000000000000000000000000000000
            0000000000000000000000000000000000000000000000000000000000000000
            {hex_amount_in.zfill(64)}
            0000000000000000000000000000000000000000000000000000000000000000
            0000000000000000000000000000000000000000000000000000000000010001
            {hex_min_amount_out.zfill(64)}
            0000000000000000000000000000000000000000000000000000000000000000
            '''
            ########################################################################################################################

            data = data.replace('\n', '').replace(' ', '')


            #### APPROVE
            token_address = Web3.to_checksum_address(token_contract_in)
            spender_address = Web3.to_checksum_address(to_address)

            approval_success = await txm.ensure_allowance(
            token_address=token_address,
            spender_address=spender_address,
            amount_needed=amount_in
            )

            if approval_success:
                logger.success("Manual approval was successful!")
            else:
                logger.error("Manual approval failed.")

            ### MAIN TRANSACTION


            nonce = txm.get_nonce()
            gas = txm.get_gas_fees()

            tx = {
                "chainId": txm.chain_id,
                "data": data,
                "from": address,
                "to": to_address,
                "nonce": nonce,
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
