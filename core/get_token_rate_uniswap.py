import requests
import time
import json
from loguru import logger

def get_uniswap_quote(token_in, token_out, max_retries=5, delay=3):
    url = "https://trading-api-labs.interface.gateway.uniswap.org/v1/quote"
    amount_in = str(1000000000000000000)

    headers = {
        "Content-Type": "application/json",
        "x-api-key": "JoyCGj29tT4pymvhaGciK4r1aIPvqW6W53xT1fwo",
        "origin": "https://app.uniswap.org",
        "referer": "https://app.uniswap.org/",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
    }

    payload_dict = {
        "amount": amount_in,
        "tokenIn": token_in,
        "tokenOut": token_out,
        "tokenInChainId": 10143,
        "tokenOutChainId": 10143,
        "type": "EXACT_INPUT",
        "swapper": "0xAAAA44272dc658575Ba38f43C438447dDED45358",
        "protocols": ["V3", "V2", "V4"],
    }

    encoded_payload = json.dumps(payload_dict)


    for attempt in range(1, max_retries + 1):
        try:
            response = requests.post(url, headers=headers, data=encoded_payload)

            if response.status_code == 200:
                response_json = response.json()
                quoted_amount = response_json.get("quote", {}).get("output", {}).get("amount")
                if quoted_amount:
                    return int(quoted_amount)
                else:
                    logger.error(f"Full API Response: {response.text}")
                    return None
            else:
                logger.error(f"API Error Response: {response.text}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Attempt {attempt}/{max_retries} - A network error occurred: {e}")

        if attempt < max_retries:
            time.sleep(delay)

    logger.critical("Failed to get data after all retries.")
    return None


if __name__ == "__main__":
    token_in = "0x0000000000000000000000000000000000000000"
    token_out = "0xe0590015a873bf326bd645c3e1266d4db41c4e6b"
    quote = get_uniswap_quote(token_in, token_out)
    logger.info(quote)
    logger.info(quote/1e18)


