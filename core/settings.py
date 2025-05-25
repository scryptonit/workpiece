import os
from dotenv import load_dotenv

load_dotenv()

CONFIG_DIR = "config"
LOG_DIR = "logs"
RESULTS_DIR = "results"

EVM_PATH = os.path.join(CONFIG_DIR, "evm.txt")
PROXY_PATH = os.path.join(CONFIG_DIR, "proxies.txt")
RPC_PATH = os.path.join(CONFIG_DIR, "rpc.txt")
USE_PROXY = os.getenv("USE_PROXY", "true").strip().lower() == "true"

def get_rpc_url(chain_name: str, rpc_file: str = RPC_PATH) -> str:
    with open(rpc_file, 'r') as f:
        for line in f:
            if line.strip():
                try:
                    name, url = line.strip().split(",", 1)
                    if name.strip().lower() == chain_name.strip().lower():
                        return url.strip()
                except ValueError:
                    continue
    raise ValueError(f'RPC URL for "{chain_name}" not found in {rpc_file}')

def load_lines(path):
    with open(path, "r") as f:
        return [line.strip() for line in f.readlines()]

evm_lines = load_lines(EVM_PATH)
proxy_lines = load_lines(PROXY_PATH)

with open(RPC_PATH, 'r') as file:
    RPC_URL = file.readline().strip()
