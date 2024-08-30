from Hash_DRBG import HashDRBG


def main():
    csprng = HashDRBG(personalization_string="1011")
    csprng.get_entropy_input(int(1.5 * csprng.requested_bits)) # Entropy input plus nonce
    csprng.instantiate_algorithm()

    total_requested_bits = None
    while type(total_requested_bits) != int or total_requested_bits < 0: # Handle invalid inputs
        try:
            total_requested_bits = input("Number of bits to generate: ")
            total_requested_bits = int(total_requested_bits)
        except ValueError:
            print("Try again")

    aggregator = 0 # Current number of bits generated
    bit_output = "" # Bits output
    while aggregator < total_requested_bits:
        bit_output += csprng.generate() # Generate next random bits and add to output
        aggregator += csprng.requested_bits # Add the number of bits of output
    if (len(bit_output) * 4) > (total_requested_bits / 4):
        bit_output = hex(int(bin(int(bit_output, 16))[2:total_requested_bits+2], 2))[2:].zfill(int(total_requested_bits/4))
    print(len(bit_output))


if __name__ == "__main__":
    main()