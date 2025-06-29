import requests
from decimal import Decimal, getcontext

getcontext().prec = 100

API = "https://api.geckoterminal.com/api/v2"

def fetch_json(path, params=None):
    resp = requests.get(API + path, params=params or {})
    resp.raise_for_status()
    return resp.json()

def list_all_networks():
    nets, page = [], 1
    while True:
        resp = fetch_json("/networks", {"page": page})
        nets += [n["id"] for n in resp["data"]]
        if not resp.get("links", {}).get("next"):
            break
        page += 1
    return sorted(nets)

def fmt_dec(d):
    if d is None:
        return "N/A"
    try:
        return f"{Decimal(d).normalize():f}".rstrip('0').rstrip('.') or "0"
    except:
        return str(d)

def get_pool_info(chain, pool_addr):
    resp = fetch_json(
        f"/networks/{chain}/pools/{pool_addr}",
        params={"include": "base_token,quote_token"}
    )
    data = resp["data"]
    attrs = data["attributes"]
    relationships = data["relationships"]

    included_tokens = {
        inc["id"]: {
            "symbol": inc["attributes"]["symbol"],
            "decimals": inc["attributes"]["decimals"]
        }
        for inc in resp.get("included", [])
        if inc["type"] == "token"
    }

    base_token_id = relationships["base_token"]["data"]["id"]
    quote_token_id = relationships["quote_token"]["data"]["id"]

    base_token_info = included_tokens.get(base_token_id, {})
    quote_token_info = included_tokens.get(quote_token_id, {})

    return {
        "price_bq": attrs.get("base_token_price_quote_token"),
        "price_qb": attrs.get("quote_token_price_base_token"),
        "base_symbol": base_token_info.get("symbol"),
        "quote_symbol": quote_token_info.get("symbol"),
        "base_decimals": base_token_info.get("decimals"),
        "quote_decimals": quote_token_info.get("decimals"),
    }

def get_token_ratio_wei(chain: str, pool: str):
    info = get_pool_info(chain, pool)

    base_dec = info["base_decimals"]
    quote_dec = info["quote_decimals"]
    price_bq = info["price_bq"]
    price_qb = info["price_qb"]

    if base_dec is None or quote_dec is None or price_bq is None or price_qb is None:
        raise ValueError("Missing decimals or price")

    base_unit = Decimal(10) ** base_dec
    quote_unit = Decimal(10) ** quote_dec

    price_bq_dec = Decimal(price_bq)
    price_qb_dec = Decimal(price_qb)

    quote_per_base = (price_bq_dec * quote_unit).quantize(Decimal('1'))
    base_per_quote = (price_qb_dec * base_unit).quantize(Decimal('1'))

    return int(quote_per_base), int(base_per_quote)


def main():
    nets = list_all_networks()
    print(f"Networks found: {len(nets)}")
    for i, nid in enumerate(nets):
        print(f"{i:3d}: {nid}")
    ch = input("Select network (index or ID): ").strip()
    if ch.isdigit():
        idx = int(ch)
        if 0 <= idx < len(nets):
            chain = nets[idx]
        else:
            print("Invalid network index.")
            return

    elif ch in nets:
        chain = ch
    else:
        print("Network ID not found.")
        return

    pool = input("Enter pool address: ").strip()

    try:
        raw_info = get_pool_info(chain, pool)
        base, quote = raw_info["base_symbol"], raw_info["quote_symbol"]

        print(f"\nPair {base}/{quote} on {chain}:")
        print(" Price ")
        print(f" - 1 {base} = {fmt_dec(raw_info['price_bq'])} {quote}")
        if raw_info['price_qb']:
            print(f" - 1 {quote} = {fmt_dec(raw_info['price_qb'])} {base}")

        quote_per_base, base_per_quote = get_token_ratio_wei(chain, pool)
        print("\n Integer ratio (in minimal units) ")
        print(f" (Decimals: {base} = {raw_info['base_decimals']}, {quote} = {raw_info['quote_decimals']})")
        print(f" - {10 ** raw_info['base_decimals']} wei{base} = {quote_per_base} wei{quote}")
        print(f" - {10 ** raw_info['quote_decimals']} wei{quote} = {base_per_quote} wei{base}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
