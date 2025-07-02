from itertools import zip_longest
import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)


def _parse_hex_data(hex_data: str) -> tuple[str, list[str]]:
    if not isinstance(hex_data, str) or not hex_data:
        return " (нет данных) ", []

    clean_data = hex_data.lstrip('0x')

    SELECTOR_CHARS = 8
    CHUNK_CHARS = 64

    if len(clean_data) < SELECTOR_CHARS:
        return f"0x{clean_data}", []

    selector = f"0x{clean_data[:SELECTOR_CHARS]}"
    rest_of_data = clean_data[SELECTOR_CHARS:]
    chunks = [rest_of_data[i:i + CHUNK_CHARS] for i in range(0, len(rest_of_data), CHUNK_CHARS)]
    return selector, chunks


def display_comparison_and_recap(hex_data1: str, hex_data2: str, column_width: int = 70):
    selector1, chunks1 = _parse_hex_data(hex_data1)
    selector2, chunks2 = _parse_hex_data(hex_data2)

    header1 = "calldata 1"
    header2 = "calldata 2"
    print(f"{header1:<{column_width}}{header2}")
    print("-" * (column_width + 64))

    color = Fore.GREEN if selector1 == selector2 else Fore.RED
    print(f"{color}{selector1:<{column_width}}{selector2}")

    for i, (chunk1, chunk2) in enumerate(zip_longest(chunks1, chunks2, fillvalue="")):
        color = Fore.GREEN if chunk1 == chunk2 else Fore.RED
        print(f"{color}{chunk1:<{column_width}}{chunk2}")

    print("-" * 66)
    print(selector1)
    for chunk in chunks1:
        print(chunk)


if __name__ == "__main__":
    data_one = ""
    data_two = ""
    display_comparison_and_recap(data_one, data_two)
