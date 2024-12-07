from cryptography.hazmat.primitives.asymmetric import rsa
from securesystemslib.signer import CryptoSigner

# Generate key pair with non-default arguments
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=4096,
)

signer = CryptoSigner(private_key)

# store private key securely
with open ("privkey.pem", "wb") as f:
    f.write(signer.private_bytes)

# update alice private key
with open ("privkey.pem", "rb") as src, open ("alice", "wb") as dst:
    dst.write(src.read())

# update alice public key
pubkey = signer.public_key.to_dict()['keyval']['public']
with open ("alice.pub", "w") as f:
    f.write(pubkey)