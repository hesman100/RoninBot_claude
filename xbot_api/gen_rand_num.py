import secrets

def generate_random_hex(length=16):
    """Generate a random hexadecimal string of a given length."""
    random_hex = secrets.token_hex(length // 2)  # Each byte corresponds to two hex digits
    return random_hex

# Example usage
random_hex_number = generate_random_hex()
print("Random Hexadecimal Number:", random_hex_number)
