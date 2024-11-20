import random

def vigenere(message, key, decryption=False):
    text = ""
    key_length = len(key)
    key_as_int = [ord(k) for k in key]

    for i, char in enumerate(str(message)):
        key_index = i % key_length
        #Letters encryption/decryption
        if char.isalpha():
            if decryption:
                modified_char = chr((ord(char.upper()) - key_as_int[key_index] + 26) % 26 + ord('A'))
            else : 
                modified_char = chr((ord(char.upper()) + key_as_int[key_index] - 26) % 26 + ord('A'))
            #Put back in lower case if it was
            if char.islower():
                modified_char = modified_char.lower()
            text += modified_char
        #Digits encryption/decryption
        elif char.isdigit():
            if decryption:
                modified_char = str((int(char) - key_as_int[key_index]) % 10)
            else:  
                modified_char = str((int(char) + key_as_int[key_index]) % 10)
            text += modified_char
        else :
            text += char
    return text


def send_packet(key, type, content):
    """
    Envoi de données fournies en paramètres
    Cette fonction permet de construire, de chiffrer puis d'envoyer un paquet via l'interface radio du micro:bit.

    :param (str) key:       Clé de chiffrement
    :param (str) type:      Type du paquet à envoyer
    :param (str) content:   Données à envoyer
    :return: None
    """
    print(key)
    print(type)
    print(content)
    message = (f"{type}|{len(content)}|{content}")
    print(message)  # Construire le message
    encrypted_message = vigenere(message, key)   # Chiffrer le message

key = "KEYWORD"
challenge = str(random.randint(1000, 9999))  # Générer un challenge aléatoire
send_packet(key, "CHALLENGE", challenge)

challenge = str(random.randint(1000, 9999))
