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


from Cryptodome.Cipher import DES

key = dh1_shared[:8]


def pad(text):
    while len(text) % 8 != 0:
        text += b' '
    return text


des = DES.new(key, DES.MODE_ECB)
text = b'Python fucking sucks!'
padded_text = pad(text)

encrypted_text = des.encrypt(padded_text)
print(encrypted_text)

data = des.decrypt(encrypted_text)
print(data)