# server/app/utils/compute_simhash.py
from simhash import Simhash

SIMHASH_FINGERPRINT_SIZE = 64  # Using 64-bit simhash fingerprints
SIMHASH_THRESHOLD = 3

def compute_simhash(text: str) -> str:
    """Compute the simhash fingerprint for the given text and return it as a string."""
    simhash_obj = Simhash(text, f=SIMHASH_FINGERPRINT_SIZE)
    # Convert the integer value to a string before returning
    return str(simhash_obj.value)