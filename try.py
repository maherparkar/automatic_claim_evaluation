# from PIL import Image
# from numpy import asarray
# from Crypto.Cipher import DES3
# from Crypto import Random
# key = 'Sixteen byte key'
# iv = Random.new().read(DES3.block_size) #DES3.block_size==8
# cipher_encrypt = DES3.new(key, DES3.MODE_OFB, iv)
#
# # load the image and convert into
# # numpy array
# img = Image.open('metadata.JPG')
# numpydata = asarray(img)
#
# # data
# # print(numpydata)
# plaintext = str(numpydata)
#
# from cryptography.fernet import Fernet
#
# # we will be encrypting the below string.
# message = plaintext
#
# key = Fernet.generate_key()
#
# fernet = Fernet(key)
# encMessage = fernet.encrypt(message.encode())
#
# print("original string: ", message)
# print("encrypted string: ", encMessage)
# decMessage = fernet.decrypt(encMessage).decode()
#
# print("decrypted string: ", decMessage)
# data = [['discharge summary', 'bills'], [['aaaa', 'bbbbb'], ['aaaaaccc']], [['str', 'list'], ['str']]]
# final_json = {}
# for i in range(len(data[0])):
#     temp_json = {}
#     for j in range(len(data[1][i])):
#         temp_json[str(data[1][i][j])] = str(data[2][i][j])
#     final_json[data[0][i]] = temp_json
# print(final_json)

# Python3 code to demonstrate
# Matching elements count
# using list comprehension and index() + len()

data = [['generic'], [['patient name across all document']], [['pharmacy bill', 'bills', 'policy']], '']
final_json = {}
final_all_json = {}
for i in range(len(data[0])):
    temp_json = {}
    for j in range(len(data[1][i])):
        temp_json[str(data[1][i][j])] = data[2][i]
    final_json[data[0][i]] = temp_json
final_all_json["data"] = final_json
final_all_json["rule_name"] = str(data[3])
print("final_all_json",final_all_json)
