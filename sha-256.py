import math
import sympy

def split_string(
        original_string: str,
        interval: int
        ) -> str:
    """ Splits a given string into sections of equal length
    
    :param original_string: The string being split
    :param interval:        The number of digits before a space
    :return split_string:   The new string with spaces
    """
    split_string = ""
    for i in range(interval, len(original_string), interval):
        split_string += (original_string[i-interval:i] + " ") # Copy a slice and add a space after
    split_string += original_string[-interval:] # No space after the last slice
    return split_string

def string_to_binary(
        original_string: str
        ) -> str:
    """ Converts a string to binary using ascii
    
    :param string:          The string being turned to binary
    :return binary_string:  The final binary version of the string 
    """
    binary_string = ""
    for char in original_string:
        binary_string += bin(ord(char))[2:].zfill(8) # Converts each character to ascii, then binary, then strips 0b, then pads to make each 8 bits
    return binary_string

def float_to_binary(
        original_float: float,
        num_bits: int
        ) -> str:
    """ Converts the floating point part of a number to binary
    
    :param original_float:  Complete float, with all digits
    :param num_bits:        The number of floating point decimals you want to convert to binary
    :return binary_float:   The floating point part converted to binary
    """
    original_float_decimal_part = original_float - int(original_float) # Only get the decimal part of the number
    binary_float = "" # Where the binary of the decimal part will be stored
    current_two_exponent = -1
    while len(binary_float) < num_bits: # Continue until the desired number of bits is met
        current_power_of_two = math.pow(2, current_two_exponent)
        if original_float_decimal_part - current_power_of_two >= 0:
            binary_float += "1"
            original_float_decimal_part -= current_power_of_two
        else:
            binary_float += "0"
        current_two_exponent -= 1
    return binary_float

def get_primes(
        n: int,
        current_prime: int=2,
        primes: list=[]
        ) -> list:
    """ Gets the first n primes after a number
    
    :param n:               The number of primes to get
    :param current_prime:   The first prime to start with
    :param primes:          The list of primes after current_prime
    :return primes:
    """
    if len(primes) < n:
        primes.append(current_prime)
        get_primes(n, sympy.nextprime(current_prime, 1), primes)

    return primes

def message_schedule_remaining(W_schedule: list, t: int) -> list:
    """ Get the remaining elements 16-63 for the message schedule
    
    :param W_schedule:  The current state of the message schedule array
    :param t:           The current index of W being solved
    :return sigma_1(Wt2) + Wt7 + sigma_0(Wt15) + Wt16 
    """
    sigma_0 = sigma_calculation(W_schedule[t-15], "small", [7, 18, 3])
    sigma_1 = sigma_calculation(W_schedule[t-2], "small", [17, 19, 10])
    Wt7 = W_schedule[t-7]
    Wt16 = W_schedule[t-16]
    result = (bin( # There must be a way to do addition mod 2**32 using XOR, but I didn't figure it out
        sigma_1
        + int(Wt7, 2) 
        + sigma_0
        + int(Wt16, 2)
        )[2:])[-32:].zfill(32) # Only the 32 least significant bits
    #print(f"t: {t}")
    #print(f"{bin(sigma_1)}, {bin(int(Wt7, 2))}, {bin(sigma_0)}, {bin(int(Wt16, 2))}") # To check all the addends
    #print(result)
    return str(result)
    

def sigma_calculation(
        bit_input: str,
        sigma_type: str,
        values: list[int]
        ) -> str:
    """ Calculates either the lowercase (small) or uppercase (big) sigma functions
    
    :bit_input:     The number being used for the calculation
    :sigma_type:    Whether small or big sigma is being calculated
    :values:        The rotation and shift values being used
    :return:        The end sigma value
    """
    bit_input = bit_input.zfill(32) # ensure the input is 32 bits long

    def rotation(value: int):
        return bit_input[-value:] + bit_input[:-value]
    
    def rshift(value: int):
        return bin(int(bit_input, 2) >> value)[2:].zfill(32)
    
    match sigma_type:
        case "small":
            addend1 = rotation(values[0])
            addend2 = rotation(values[1])
            addend3 = rshift(values[2])
            #print(bin(int(addend1, 2) ^ int(addend2, 2) ^ int(addend3, 2))[2:].zfill(32)) # Inconsistent with the video, but Idk what hes doing. All the addends match up, but his doesn't look like bit addition mod 2
        case "big":
            addend1 = rotation(values[0])
            addend2 = rotation(values[1])
            addend3 = rotation(values[2])
            #print(bin(int(addend1, 2) ^ int(addend2, 2) ^ int(addend3, 2))[2:].zfill(32)[-32:])

    return int(addend1, 2) ^ int(addend2, 2) ^ int(addend3, 2) # XOR is equal to addition mod 2

def choose(
        word_1: str,
        word_2: str,
        word_3: str
        ) -> str:
    """ The choose function described in the sha 256 paper
    
    :param word_1: The word that determines what other word to choose from
    :param word_2: If a bit in word_1 is 0, choose from here
    :param word_3: If a bit in word_1 is 1, choose from here
    :return result: The resulting string
    """
    result = ""
    for i, char in enumerate(word_1):
        match char:
            case "0":
                result += word_3[i]
            case "1":
                result += word_2[i]
    return int(result, 2)


def majority(
        word_1: str,
        word_2: str,
        word_3: str
        ) -> str:
    """ Returns the bit in each position that is the majority out of 3 words
    """
    result = ""
    for i, _ in enumerate(word_1):
        bit_counts = {"0": 0, "1": 0}
        bit_counts[word_1[i]] += 1
        bit_counts[word_2[i]] += 1
        bit_counts[word_3[i]] += 1
        if bit_counts["0"] > bit_counts["1"]:
            result += "0"
        else:
            result += "1"
    return int(result, 2)

def main():
    original_input = "846832194668976586392458758758765875087587578657865348760987584702354720957340957832094875483509237095872309845284629658466987686986789698679587666666666676565675657587578575785875875649863438479839739843987394846832194668976586392458758758765875087587578657865348760987584702354720957340957832094875483509237095872309845284629658466987686986789698679587666666666676565675657587578575785875875649863438479839739843987394846832194668976586392458758758765875087587578657865348760987584702354720957340957832094875483509237095872309845284629658466987686986789698679587666666666676565675657587578575785875875649863438479839739843987394"
    #original_input = "RedBlockBluejlkdfas;RedBlockBluejlkdfas;RedBlockBluejlkdfas;RedBlockBluejlkdfas;"
    #original_input = "RedBlockBlue"
    original_length_binary = len(str(original_input)) * 8 # Each character is represented by 8 bits

    binary_string = string_to_binary(str(original_input)) # Convert the original input to binary

    binary_string += "1" # Add a 1 bit to indicate start of padding

    while (len(binary_string) + 64) % 512 != 0: # K will be negative if the original message is over (a multiple of 512) - 65 bits long
        binary_string += "0" # Add 0 bits until the number is a mutliple of 512 bits
    binary_string += bin(original_length_binary)[2:].zfill(64) # Replace the last 64 bits with the length of the original message
    print(len(binary_string))
    binary_string_blocks = split_string(binary_string, 512) # Split the string into blocks of 512
    
    M_blocks = [
        [
        word
        for word in split_string(str(block), 32).split(" ")] 
        for block in binary_string_blocks.split(" ")
        ] # Split each block into 32 bit sections
    #print(M_blocks)
    # Hash values (SHA-224/256 constants)
    prime_numbers = get_primes(64)
    H_hash = [[
        int(float_to_binary(math.pow(p, 1/2), 32), 2)
        for p in prime_numbers[:8]
    ]]
    """
    Turns out I could just convert the big binary to hex all along, but I still think these list comprehensions were great practice
    split_binary_decimal_parts = [
        split_string(b, 4).split(" ") 
        for b in binary_decimal_parts
        ]
    # Craziest list comprehension I have written so far
    h = [
        "".join(word) # Join the hex together
        for word in [[hex(int(char, 2))[2:] # Convert to hex, remove the 0x from the hex value
                      for char in a]        # For each binary subgroup of 4 within each binary grouping
                      for a in split_binary_decimal_parts] # For each binary grouping
                      ]
    """
    K_constants = [
        hex(int(float_to_binary(math.pow(p, 1/3), 32), 2))[2:]
        for p in prime_numbers[:64]
    ]
    for i in range(1, len(M_blocks) + 1):
        # Get the message schedule
        W_schedule = [j for j in M_blocks[i-1]] # Start out with the first 15 words of that block
        for t in range(16, 64): # For the rest of the sub-schedule
            W_schedule.append(message_schedule_remaining(W_schedule, t))
    
        # Working variables
        a, b, c, d, e, f, g, h = (H_hash[i-1][j] for j in range(0, 8))
        for t in range(0, 64):
            T1 = int(bin( # All of this junk is to simulate addition mod 2 to the 32
                h 
                + sigma_calculation(bin(e)[2:][-32:], "big", [6, 11, 25])
                + choose(
                    bin(e)[2:][-32:].zfill(32),
                    bin(f)[2:][-32:].zfill(32), 
                    bin(g)[2:][-32:].zfill(32)
                    )
                + int(K_constants[t], 16)
                + int(W_schedule[t], 2)
            )[2:][-32:].zfill(32), 2)

            T2 = int(bin(
                sigma_calculation(bin(a)[2:], "big", [2, 13, 22])
                + majority(
                    bin(a)[2:][-32:].zfill(32), 
                    bin(b)[2:][-32:].zfill(32), 
                    bin(c)[2:][-32:].zfill(32)
                    )
            )[2:][-32:].zfill(32), 2)

            h = g
            g = f
            f = e
            e = int((bin(d + T1)[2:])[-32:].zfill(32), 2)
            d = c
            c = b
            b = a
            a = int((bin(T1 + T2)[2:])[-32:].zfill(32), 2)

        H_hash.append(
            [
                int(hex(a + H_hash[i-1][0])[-8:], 16),
                b + H_hash[i-1][1],
                c + H_hash[i-1][2],
                d + H_hash[i-1][3],
                e + H_hash[i-1][4],
                f + H_hash[i-1][5],
                g + H_hash[i-1][6],
                h + H_hash[i-1][7]
            ])

    SHA_256_Hash = "".join([hex(i)[-8:] for i in H_hash[-1]])
    print(SHA_256_Hash)

if __name__ == "__main__":
    main()