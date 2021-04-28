public_key = '''-----BEGIN PUBLIC KEY-----
MIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEAp9DeZnbiEu6GgMW2023f
ORIgk7FYSQS2F9QshC3L424xzgow7WibrOoAcz5bp4w6E9A2eSchgxXhJIFGUQtY
XnTQ0+dEsqszptDQGK5iwH4IlG5TwwEqKhuG41wzzoSPVqKZpnE8Ne+clFxJ3Q3i
4N/ielPXLq2jR31HnmMMt8mpstLMWbqNr/NisXOVeF0gjALOSyH8sIxA3mb/mpWG
2BSfEyrwfCWzJAn9eygc9L/YA1+BdrwwvSxmUU/VXvRdT5U+qSpavttyqurvl6Lb
0sFQSj5EXyAVzImBYrnVq9eid6aaqhYweG1im+Nkwj0zDBxzHYcdumVH0XFFkf4o
QHyVcxR0rm9MD55xHLNxkvNnwNg5dyiEngREfjVC/j+VFSKbjs59qAwVdmmqOjrC
2rw+frcqk/IdBruq+QtJ92XjtSG37kGiaROJ5AKmBO/Fc0d02ESmxQyymzNspJQg
yGn2SMzV9R80xlHzTOAz9VStfGp9cTBi90xmSPHnbaRXdDl5/ADB7o9r1o3zkH09
vpkO7SRkq5lvzvUvG0ijnzMwft3c4OSZ1EI07uNqSddILHVco/EzSFd4UMlCXEtm
AUEMhOA4K4MGPHzpHeYG+gzQs4g1YEd7FNYzOK9EYbDSW0ordwUclHFq3irCs/47
s1f6Y3Zu3A8nnw/4Rn0vJ3cCAwEAAQ==
-----END PUBLIC KEY-----'''

import collections
import base64

# Crypto can be found at https://pypi.python.org/pypi/pycrypto
from Crypto.Signature import PKCS1_v1_5
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA
import hashlib

# PHPSerialize can be found at https://pypi.python.org/pypi/phpserialize
import phpserialize

# Convert key from PEM to DER - Strip the first and last lines and newlines, and decode
public_key_encoded = public_key[26:-25].replace('\n', '')
public_key_der = base64.b64decode(public_key_encoded)

# input_data represents all of the POST fields sent with the request
# Get the p_signature parameter & base64 decode it.
def verify_signature(logger, input_data):
    if 'p_signature' not in input_data:
        logger.info("no signature in call")
        logger.info(input_data)
        return False
    signature = input_data['p_signature']

    # Remove the p_signature parameter
    del input_data['p_signature']

    # Ensure all the data fields are strings
    for field in input_data:
        input_data[field] = str(input_data[field])

    # Sort the data
    sorted_data = collections.OrderedDict(sorted(input_data.items()))

    # and serialize the fields
    serialized_data = phpserialize.dumps(sorted_data)

    # verify the data
    key = RSA.importKey(public_key_der)
    digest = SHA.new()
    digest.update(serialized_data)
    verifier = PKCS1_v1_5.new(key)
    signature = base64.b64decode(signature)
    if verifier.verify(digest, signature):
        logger.info("verified from inside function")
        return True
    else:
        logger.info("Not verified for some reason")
        return False
