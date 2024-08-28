from sha_256 import sha_256
from noise_collection import collect_noise
import math


class HashDRBG:
    MAX_SUPPORTED_SECURITY_BITS = 256
    OUTPUT_LENGTH = 256
    PREDICTION_RESISTANT = True
    MAX_LENGTH = math.pow(2, 35)
    MAX_BITS_PER_REQUEST = math.pow(2, 19)
    RESEED_INTERVAL = math.pow(2, 48)
    SEED_LENGTH = 440
    def __init__(
            self, 
            requested_bits: int=256,
            personalization_string: str="",
            additional_input: str=""
            ):
        self.requested_bits = requested_bits
        self.__personalization_string = personalization_string
        self.__additional_input = additional_input
        if self.requested_bits > self.MAX_SUPPORTED_SECURITY_BITS:
            self.status = "Error 1"
        elif self.__personalization_string > self.MAX_PERSONALIZATION_STRING_LENGTH:
            self.status = "Error 2"
        else:
            self.status = "Success"
    
    def get_entropy_input(self, entropy_bits: int):
        """ Gets a random string of certain entropy from the RNG
        
        :param entropy_bits:    The number of bits of entropy needed
        :return entropy_input:  The string with the specified bits of entropy
        """
        # The entropy input should be at least the desired bits security
        self.__entropy_input = collect_noise(entropy_bits)
        if len(self.__entropy_input < entropy_bits):
            self.status = "Error 3"
    
    def hash_derivation_function(self, input_string, num_bits):
        """ """
        temp = None
        length = num_bits / self.OUTPUT_LENGTH
        counter = 1
        for _ in range(1, length+1):
            temp = temp + sha_256(str(counter) + str(num_bits) + input_string)
            counter += 1
        requested_bits = bin(int(temp, 16))[2:num_bits+3] # Account for the 0b and the non-inclusive stopping index
        self.status = "Success"
        return requested_bits

    def instantiate_algorithm(self):
        """ Provides instance variables for the first seeding"""
        seed_material = self.entropy_input + self.__personalization_string
        seed = self.hash_derivation_function(self, seed_material, 256)
        self.__v = seed
        self.__c = self.hash_derivation_function(self, "00000000" + self.__v, self.SEED_LENGTH)
        self.__reseed_counter = 1
    
    def reseed(self):
        """ Provides new seed for added security"""
        seed_material = "00000001" + self.__v + self.__entropy_input + self.__additional_input
        seed = self.hash_derivation_function(self, seed_material, self.SEED_LENGTH)
        self.__v = seed
        self.__c = self.hash_derivation_function(self, "00000000" + self.__v, self.SEED_LENGTH)
        self.__reseed_counter = 1

    def hashgen(self):
        """ """
        m = math.ceil(self.requested_bits / self.OUTPUT_LENGTH)
        data = self.__v
        big_w = None
        for _ in range(1, m+1):
            small_w = sha_256(data)
            big_w = big_w + small_w # Concatenate w to W
            data = (int(data, 2) + 1) % math.pow(2, self.SEED_LENGTH)
        return big_w[:self.requested_bits]

    def generate(self):
        """ Generates pseudorandom bits"""
        if self.__reseed_counter > self.RESEED_INTERVAL:
            return "Reseed needed"
        if self.__additional_input != None:
            w = sha_256("00000010" + self.__v + self.__additional_input)
            self.__v = (int(self.__v, 2) + int(w, 16)) % math.pow(2, self.SEED_LENGTH)
        returned_bits = self.hashgen(self, self.requested_bits, self.__v)
        h = sha_256("00000011" + self.__v)
        self.__v = (self.__v + h + self.__c + self.__reseed_counter) % math.pow(2, self.SEED_LENGTH)
        self.__reseed_counter += 1
        self.status = "Sucess"
        return returned_bits

    def main(self):
        self.status, self.__entropy_input = self.get_entropy_input(1.5 * self.requested_bits) # The entropy input plus the nonce
        if self.status != "Success":
            return self.status, "Invalid"
        