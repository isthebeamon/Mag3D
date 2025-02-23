import os
import random
from typing import Set
import numpy as np
import re

def random_number_generator(min_val: int = 1, max_digits: int = None) -> int:
    import os, random
    from typing import Set

    # If no max_digits is provided, choose one randomly between 1 and 9.
    if max_digits is None:
        max_digits = random.randint(1, 9)
    max_val = int('1' + '0' * max_digits)  # e.g., max_digits=3 gives max_val=1000

    def _load_used_numbers(filename: str = "used_seeds.csv") -> Set[int]:
        try:
            with open(filename, 'r') as f:
                # split on commas, filter out any empty strings, and convert to int.
                return set(int(num) for num in f.read().strip().split(',') if num)
        except FileNotFoundError:
            return set()

    def _append_number(number: int, filename: str = "used_seeds.csv") -> None:
        if os.path.exists(filename) and os.path.getsize(filename) > 0:
            with open(filename, 'a') as f:
                f.write(f",{number}")
        else:
            with open(filename, 'w') as f:
                f.write(f"{number}")

    # total candidates available
    possible_space = max_val - min_val + 1
    attempts = 0

    # Try out unique seed candidates until a unique one is found or possibilities are exhausted.
    while attempts < possible_space:
        used_numbers = _load_used_numbers()  # re-read used seeds on every attempt
        new_seed = random.randint(min_val, max_val)
        if new_seed not in used_numbers:
            _append_number(new_seed)
            return new_seed
        attempts += 1

    # If we have tried all possible seeds, then raise an error.
    raise ValueError("All possible numbers have been used!")


def extract_phantom_value(filename):
    cc_pattern = r'CC\[(\d+(\.\d+)?)\]cm'
    ml_pattern = r'ML\[(\d+(\.\d+)?)\]cm'
    pa_pattern = r'PA\[(\d+(\.\d+)?)\]cm'

    cc_match = re.search(cc_pattern, filename)
    ml_match = re.search(ml_pattern, filename)
    pa_match = re.search(pa_pattern, filename)

    cc = float(cc_match.group(1)) if cc_match else 0.0
    ml = float(ml_match.group(1)) if ml_match else 0.0
    pa = float(pa_match.group(1)) if pa_match else 0.0

    return cc, ml, pa

def read_raw_file(file_path, width=3584, height=2816, dtype=np.float32):
    """
    Read a raw file and return it as a 2D numpy array
    """
    try:
        with open(file_path, 'rb') as f:
            if hasattr(np, '__name__') and np.__name__ == 'cupy':
                import numpy as cpu_np
                data = np.asarray(cpu_np.fromfile(f, dtype=dtype))
            else:
                data = np.fromfile(f, dtype=dtype)
        return data.reshape((height, width))
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None
