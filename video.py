
import numpy as np
# Convert message to binary
def msgtobinary(msg):
    if isinstance(msg, str):
        result = ''.join([format(ord(i), "08b") for i in msg])
    elif isinstance(msg, (bytes, np.ndarray)):
        result = [format(i, "08b") for i in msg]
    elif isinstance(msg, (int, np.uint8)):
        result = format(msg, "08b")
    else:
        raise TypeError("Input type is not supported in this function")
    return result

# Key Scheduling Algorithm (KSA)
def KSA(key):
    key_length = len(key)
    S = list(range(256))
    j = 0
    for i in range(256):
        j = (j + S[i] + key[i % key_length]) % 256
        S[i], S[j] = S[j], S[i]
    return S

# Pseudo-Random Generation Algorithm (PRGA)
def PRGA(S, n):
    i = 0
    j = 0
    key = []
    while n > 0:
        n -= 1
        i = (i + 1) % 256
        j = (j + S[i]) % 256
        S[i], S[j] = S[j], S[i]
        K = S[(S[i] + S[j]) % 256]
        key.append(K)
    return key

# Convert string to ASCII array
def preparing_key_array(s):
    return [ord(c) for c in s]

# Encrypt plaintext using RC4
def encryption(plaintext, key):
    S = KSA(key)
    keystream = np.array(PRGA(S, len(plaintext)))
    plaintext = np.array([ord(i) for i in plaintext])
    cipher = keystream ^ plaintext
    ctext = ''.join([chr(c) for c in cipher])
    return ctext

# Decrypt ciphertext using RC4
def decryption(ciphertext, key):
    S = KSA(key)
    keystream = np.array(PRGA(S, len(ciphertext)))
    ciphertext = np.array([ord(i) for i in ciphertext])
    decoded = keystream ^ ciphertext
    dtext = ''.join([chr(c) for c in decoded])
    return dtext

# Embed data into video frame
def embed(frame, data, key):
    # Encrypt the data
    data = encryption(data, preparing_key_array(key))
    data += '^^*'  # Append end marker

    binary_data = msgtobinary(data)
    length_data = len(binary_data)
    index_data = 0

    for i in range(len(frame)):
        for j in range(len(frame[i])):
            pixel = frame[i][j]
            r, g, b = msgtobinary(pixel)

            # Embed data in the LSB of each channel
            if index_data < length_data:
                pixel[0] = int(r[:-1] + binary_data[index_data], 2)
                index_data += 1
            if index_data < length_data:
                pixel[1] = int(g[:-1] + binary_data[index_data], 2)
                index_data += 1
            if index_data < length_data:
                pixel[2] = int(b[:-1] + binary_data[index_data], 2)
                index_data += 1

            if index_data >= length_data:
                break
        if index_data >= length_data:
            break
    return frame

# Extract data from video frame
def extract(frame, key):
    data_binary = ""
    final_decoded_msg = ""

    for i in range(len(frame)):
        for j in range(len(frame[i])):
            pixel = frame[i][j]
            r, g, b = msgtobinary(pixel)

            # Collect LSBs
            data_binary += r[-1]
            data_binary += g[-1]
            data_binary += b[-1]

            if len(data_binary) >= 8:
                byte = data_binary[:8]
                data_binary = data_binary[8:]
                decoded_data = chr(int(byte, 2))
                final_decoded_msg += decoded_data

                if final_decoded_msg[-5:] == "^^*":
                    final_decoded_msg = final_decoded_msg[:-5]
                    decrypted_msg = decryption(final_decoded_msg, preparing_key_array(key))
                    return decrypted_msg

    return ""