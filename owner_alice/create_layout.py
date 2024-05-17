from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.hazmat.primitives.serialization import  load_pem_public_key
from securesystemslib.signer import CryptoSigner
from in_toto.models.layout import Layout
from in_toto.models.metadata import Envelope
from securesystemslib.signer import SSlibKey
from typing import Dict, Any

def _load_public_key_from_file(path: str) -> Dict[str, Any]:
    """Internal helper to load key from SubjectPublicKeyInfo/PEM file."""
    with open(path, "rb") as f:
        data = f.read()

    crypto_public_key = load_pem_public_key(data)
    key = SSlibKey.from_crypto(crypto_public_key)

    # Create a key_dict, which is accepted by `verifylib.in_toto_verify` or `Metablock.verify_signature`
    # NOTE: securesystemslib and in-toto key dicts differ:
    # the former don't include the keyid, which the latter require
    key_dict = key.to_dict()
    key_dict["keyid"] = key.keyid

    return key_dict

def main():
  # Load Alice's private key to later sign the layout
  with open("alice", "rb") as f:
    key_alice = load_pem_private_key(f.read(), None)

  signer_alice = CryptoSigner(key_alice)
  # Fetch and load Bob's and Carl's public keys
  # to specify that they are authorized to perform certain step in the layout
  # https://github.com/in-toto/in-toto/issues/663
  key_bob  = _load_public_key_from_file("../functionary_bob/bob.pub")
  key_carl  = _load_public_key_from_file("../functionary_carl/carl.pub")  


  layout = Layout.read({
      "_type": "layout",
      "keys": {
          key_bob["keyid"]: key_bob,
          key_carl["keyid"]: key_carl,
      },
      "steps": [{
          "name": "clone",
          "expected_materials": [],
          "expected_products": [["CREATE", "demo-project/foo.py"], ["DISALLOW", "*"]],
          "pubkeys": [key_bob["keyid"]],
          "expected_command": [
              "git",
              "clone",
              "https://github.com/in-toto/demo-project.git"
          ],
          "threshold": 1,
        },{
          "name": "update-version",
          "expected_materials": [["MATCH", "demo-project/*", "WITH", "PRODUCTS",
                                "FROM", "clone"], ["DISALLOW", "*"]],
          "expected_products": [["MODIFY", "demo-project/foo.py"], ["DISALLOW", "*"]],
          "pubkeys": [key_bob["keyid"]],
          "expected_command": [],
          "threshold": 1,
        },{
          "name": "package",
          "expected_materials": [
            ["MATCH", "demo-project/*", "WITH", "PRODUCTS", "FROM",
             "update-version"], ["DISALLOW", "*"],
          ],
          "expected_products": [
              ["CREATE", "demo-project.tar.gz"], ["DISALLOW", "*"],
          ],
          "pubkeys": [key_carl["keyid"]],
          "expected_command": [
              "tar",
              "--exclude",
              ".git",
              "-zcvf",
              "demo-project.tar.gz",
              "demo-project",
          ],
          "threshold": 1,
        }],
      "inspect": [{
          "name": "untar",
          "expected_materials": [
              ["MATCH", "demo-project.tar.gz", "WITH", "PRODUCTS", "FROM", "package"],
              # FIXME: If the routine running inspections would gather the
              # materials/products to record from the rules we wouldn't have to
              # ALLOW other files that we aren't interested in.
              ["ALLOW", ".keep"],
              ["ALLOW", "alice.pub"],
              ["ALLOW", "root.layout"],
              ["ALLOW", "*.link"],
              ["DISALLOW", "*"]
          ],
          "expected_products": [
              ["MATCH", "demo-project/foo.py", "WITH", "PRODUCTS", "FROM", "update-version"],
              # FIXME: See expected_materials above
              ["ALLOW", "demo-project/.git/*"],
              ["ALLOW", "demo-project.tar.gz"],
              ["ALLOW", ".keep"],
              ["ALLOW", "alice.pub"],
              ["ALLOW", "root.layout"],
              ["ALLOW", "*.link"],
              ["DISALLOW", "*"]
          ],
          "run": [
              "tar",
              "xzf",
              "demo-project.tar.gz",
          ]
        }],
  })

  metadata = Envelope.from_signable(layout)

  # Sign and dump layout to "root.layout"
  metadata.create_signature(signer_alice)
  metadata.dump("root.layout")
  print('Created demo in-toto layout as "root.layout".')

if __name__ == '__main__':
  main()
