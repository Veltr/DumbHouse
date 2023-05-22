from diffiehellman import DiffieHellman

# automatically generate two key pairs
dh1 = DiffieHellman(group=14, key_bits=128)
dh2 = DiffieHellman(group=14, key_bits=128)

# get both public keys
dh1_public = dh1.get_public_key()
dh2_public = dh2.get_public_key()

# generate shared key based on the other side's public key
dh1_shared = dh1.generate_shared_key(dh2_public)
dh2_shared = dh2.generate_shared_key(dh1_public)


from Cryptodome.Cipher import AES

data = b'abacaba'

# key = b'Sixteen byte key'
key = dh1_shared[:32]
cipher = AES.new(key, AES.MODE_EAX)
nonce = cipher.nonce
ciphertext, tag = cipher.encrypt_and_digest(data)

cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)

plaintext = cipher.decrypt(ciphertext)

try:
    cipher.verify(tag)
    print("The message is authentic:", plaintext)
except ValueError:
    print("Key incorrect or message corrupted")


