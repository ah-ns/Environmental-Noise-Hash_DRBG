from sha_256 import sha_256
#from noise_collection import collect_noise
import math


class HashDRBG:
    MAX_SUPPORTED_SECURITY_BITS = 256   # Depends on the source of entropy
    OUTPUT_LENGTH = 256                 # How many bits the output number will be
    PREDICTION_RESISTANT = False        # Not implemented
    MAX_PERSONALIZATION_ADDITIONAL_LENGTH = math.pow(2, 35)
    MAX_BITS_PER_REQUEST = math.pow(2, 19)  # Prevents the number from being predictable
    RESEED_INTERVAL = math.pow(2, 48)       # Max no. of requests before a reseed
    SEED_LENGTH = 440                       # Depends on the hash function
    def __init__(
            self,
            requested_bits: int=MAX_SUPPORTED_SECURITY_BITS,
            personalization_string: str="", # Optional
            additional_input: str=""        # Optional
            ):
        self.requested_bits = requested_bits
        self.__personalization_string = personalization_string
        self.__additional_input = additional_input

        if self.requested_bits > self.MAX_SUPPORTED_SECURITY_BITS: # Do not supply bits if more than max amount are needed
            self.status = "Error 01"
        elif len(self.__personalization_string) > self.MAX_PERSONALIZATION_ADDITIONAL_LENGTH \
        or len(self.__additional_input) > self.MAX_PERSONALIZATION_ADDITIONAL_LENGTH:
            self.status = "Error 02"
        else:
            self.status = "Success"

    def get_entropy_input(self, entropy_bits: int):
        """ Gets a random string of certain entropy from the RNG
        
        :param entropy_bits:    The number of bits of entropy needed
        :__entropy_input:       The string with the specified bits of entropy
        """
        # The entropy input should be at least the desired bits security
        self.status, self.__entropy_input = "Success", "1100011000100110101011010100000101110010011001011101111100000010110000100100100000000111101000111011001100000000000011100001001110001001001111000111011010111111110101011110111111111011101011010000101110010101110000011001001111001110110110011010101010010000101011111110000111000000111011101001001000101001011000111110011100001111011010000101110100001100111100100110101010011110100001101000000111001111000000110001110011010011100100000011000010000100100000000110011000101001" # For testing
        #self.status, self.__entropy_input = collect_noise(entropy_bits)
        self.__entropy_input = self.__entropy_input[:entropy_bits]
        if len(self.__entropy_input) < entropy_bits: # There is no current source of entropy
            self.status = "Error 03"
        
    def instantiate_algorithm(self):
        """ Provides instance variables for the first seeding
        
        :binary __v:        Essential secret value used in reseeding and generation
        :binary __c:        Essential secret value used in reseeding and generation
        :__reseed_counter:  No. of numbers generated with current seed
        """
        seed_material = self.__entropy_input + self.__personalization_string
        seed = self.hash_derivation_function(seed_material, 256)
        self.__v = seed
        self.__c = self.hash_derivation_function("00000000" + self.__v, self.SEED_LENGTH)
        self.__reseed_counter = 1

    def hash_derivation_function(self, input_string, num_bits):
        """ Mixes input with changing variables using hashing algorithm
        
        :param input_string:    String that is being hashed
        :param num_bits:        Number of bits to return out of the hash
        :return requested_bits: First num_bits of the hash
        """
        temp = ""
        length = math.ceil(num_bits / self.OUTPUT_LENGTH)

        for count in range(1, length+1):
            temp = temp + sha_256(str(count) + str(num_bits) + input_string)
        requested_bits = bin(int(temp, 16))[2:num_bits+2] # Account for the 0b and the non-inclusive stopping index
        
        self.status = "Success" # TODO: capture potential errors in this function

        return requested_bits

    def reseed(self):
        """ Provides new seed for renewed security"""
        seed_material = "00000001" + self.__v + self.__entropy_input + self.__additional_input
        seed = self.hash_derivation_function(self, seed_material, self.SEED_LENGTH)
        self.__v = seed
        self.__c = self.hash_derivation_function(self, "00000000" + self.__v, self.SEED_LENGTH)
        self.__reseed_counter = 1 # New seed, so reset counter

    def hashgen(self):
        """ """
        m = math.ceil(self.requested_bits / self.OUTPUT_LENGTH)
        data = self.__v
        big_w = ""

        for _ in range(m):
            small_w = sha_256(data)
            big_w = big_w + small_w # Concatenate w to W
            data = (int(data, 2) + 1) % int(math.pow(2, self.SEED_LENGTH))

        return big_w[:self.requested_bits]

    def generate(self):
        """ Generates requested number of pseudorandom bits"""
        if self.__reseed_counter > self.RESEED_INTERVAL:
            return "Reseed needed"
        
        if self.__additional_input != "":
            w = sha_256("00000010" + self.__v + self.__additional_input)
            self.__v = bin((int(self.__v, 2) + int(w, 16)) % int(math.pow(2, self.SEED_LENGTH)))[2:]
        returned_bits = self.hashgen()

        h = sha_256("00000011" + self.__v)
        self.__v = bin((
            int(self.__v, 2) 
            + int(h, 16) 
            + int(self.__c, 2) 
            + self.__reseed_counter) % int(math.pow(2, self.SEED_LENGTH)))[2:]
        self.__reseed_counter += 1

        self.status = "Success" # TODO: capture potential errors in this function

        return returned_bits