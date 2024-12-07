from microbit import *
import radio
import random
import music

######################
# TYPES DE PAQUETS   #
# 0x01 : CHALLENGE   #
# 0x02 : REPONSE     #
# 0x03 : MILK DOSES  #
# 0x04 : TEMPERATURE #
# 0x05 : ETAT EVEIL  #
######################


#Initialisation des variables du micro:bit
radio.on()
connexion_established = False
key = "GROUPEB07ONT0P"
session_key = ""
connexion_key = None
nonce_list = set()
baby_state = 0
max_nonce_size = 20 #ajouté pour ne pas limiter la mémoire, MEMORY OUT OF RANGE
last_send_time = 0  # Temps du dernier envoi
send_duration_agité = 5000  # Durée en millisecondes pour "agité" (5 secondes)
send_duration_très_agité = 10000  # Durée en millisecondes pour "très agité" (10 secondes)
previous_state = ""

milk_doses = 0

#####################
# CRYPTO ET GENERAL #
#####################

def hashing(string):
	"""
	Hachage d'une chaîne de caractères fournie en paramètre.
	Le résultat est une chaîne de caractères.
	Attention : cette technique de hachage n'est pas suffisante (hachage dit cryptographique) pour une utilisation en dehors du cours.

	:param (str) string: la chaîne de caractères à hacher
	:return (str): le résultat du hachage
	"""
	def to_32(value):
		"""
		Fonction interne utilisée par hashing.
		Convertit une valeur en un entier signé de 32 bits.
		Si 'value' est un entier plus grand que 2 ** 31, il sera tronqué.

		:param (int) value: valeur du caractère transformé par la valeur de hachage de cette itération
		:return (int): entier signé de 32 bits représentant 'value'
		"""
		value = value % (2 ** 32)
		if value >= 2**31:
			value = value - 2 ** 32
		value = int(value)
		return value

	if string:
		x = ord(string[0]) << 7
		m = 1000003
		for c in string:
			x = to_32((x*m) ^ ord(c))
		x ^= len(string)
		if x == -1:
			x = -2
		return str(x)
	return ""
    
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
        else:
            text += char
    return text

def generate_nonce():
    """
    Génère le nonce
    """
    return str(random.randint(100000, 999999))
    
def send_packet_with_nonce(key, type, content):
    """
    Envoie un paquet avec un nonce unique pour éviter les attaques de rejeu.
    """
    nonce = generate_nonce()
    message = (nonce + ":" + content)
    send_packet(key, type, message)
    add_nonce(nonce)  

def add_nonce(nonce):
    """
    Ajoute un nonce à la liste tout en limitant la taille.
    """
    if len(nonce_list) >= max_nonce_size:
        nonce_list.pop()  # Supprime un élément aléatoire (ou le plus ancien avec une structure adaptée) pour ne pas avoir un MemoryError
    nonce_list.add(nonce)
    
def send_packet(key, type, content):
    """
    Envoi de données fournies en paramètres
    Cette fonction permet de construire, de chiffrer puis d'envoyer un paquet via l'interface radio du micro:bit.

    :param (str) key:       Clé de chiffrement
    :param (str) type:      Type du paquet à envoyer
    :param (str) content:   Données à envoyer
    :return: None
    """
    message = (type + "|" + str(len(content)) + "|" + content)  # Construire le message
    encrypted_message = vigenere(message, key)   # Chiffrer le message
    radio.send(encrypted_message)                # Envoyer via l'interface radio

#Decrypt and unpack the packet received and return the fields value
def unpack_data(encrypted_packet, key):
    """
    Déballe et déchiffre les paquets reçus via l'interface radio du micro:bit
    Cette fonction renvoit les différents champs du message passé en paramètre

    :param (str) encrypted_packet: Paquet reçu
           (str) key:              Clé de chiffrement
	:return (srt)type:             Type de paquet
            (int)length:           Longueur de la donnée en caractères
            (str) message:         Données reçue
    """
    try:
        decrypted_message = vigenere(encrypted_packet, key, decryption=True)  # Déchiffrer, grace a decryption = True (false de base)
        type, length, message = decrypted_message.split('|')  # Découper les champs
        length = int(length)  # Convertir la longueur en entier
        if len(message) == length:  # Vérification de cohérence
            return type, length, message
    except:
        pass  # Gestion d'erreur
    return "", 0, ""  # Retourner des valeurs vides en cas d'erreur


#Unpack the packet, check the validity and return the type, length and content
def receive_packet(packet_received, key):
    """
    Traite les paquets reçus via l'interface radio du micro:bit.
    Si un nonce est détecté comme déjà utilisé, le message est ignoré.
    """
    type, length, message = unpack_data(packet_received, key)
    if message:
        nonce, content = message.split(':', 1)
        if nonce not in nonce_list:  # Vérifie que le nonce est unique
            add_nonce(nonce)
            return type, length, content
    return "", 0, ""
    
def calculate_challenge_response(challenge):
    """
    Calcule la réponse au challenge initial de connection envoyé par l'autre micro:bit

    :param (str) challenge:            Challenge reçu
	:return (srt)challenge_response:   Réponse au challenge
    """
    challenge_reponse = hashing(challenge)
    return challenge_reponse
    
#Ask for a new connection with a micro:bit of the same group
def establish_connexion(key):
    global session_key
    """
    Établissement de la connexion avec l'autre micro:bit.
    Si une erreur survient ou si la connexion échoue, retourne une chaîne vide.

    :param (str) key: Clé de chiffrement
    :return (str): Réponse au challenge si succès, chaîne vide sinon.
    """
    challenge = str(random.randint(1000, 9999))  # Générer un challenge aléatoire
    send_packet_with_nonce(key, "0x01", challenge)  # Envoi du challenge
    
    start_time = running_time()  # Temps de départ
    while running_time() - start_time < 15000:# Timeout de 5 secondes
        display.show(Image.ALL_CLOCKS, delay=100, loop=False, clear=True)
        received_packet = radio.receive()  # Réception d'un paquet
        if received_packet:
            # Déchiffrer et extraire les données du paquet
            packet_type, length, content = receive_packet(received_packet, key)
            if packet_type == "0x02":
                # Valider la réponse
                expected_response = calculate_challenge_response(challenge)
                if content == expected_response:
                    session_key = key+content
                    display.show(Image.YES)  # Afficher un symbole de réussite
                    sleep(1000)
                    display.clear()
                    return True 
                    
                    

    # Si aucun paquet valide reçu dans le temps imparti
    
    display.show(Image.NO)
    sleep(5000)
    display.scroll("ERROR CONNECTION: REBOOT MICROBITS", delay=60)
    return False  # Retourner une chaîne vide

########
# INIT #
########

def open():
    """
    Allumage du microbit
    """
    music.play(music.JUMP_UP)
    display.show(Image.DUCK)
    sleep(1000)
    display.scroll('Be:Bi Enfant', delay=60)

def initialising():
    """
    Connexion entre les deux microbits
    """
    global connexion_established
    if establish_connexion(key) == True:
        connexion_established = True
        return connexion_established
    else:
        while True:
            display.show(Image.NO)  # Afficher un symbole d'échec
            sleep(5000)
            display.scroll("ERROR CONNECTION: REBOOT MICROBITS", delay=60)

########
# LAIT #
########

def display_milk_doses():
    """
    Affiche la quantité de lait consommée en doses sur le panneau LED.
    """
    display.scroll("Milk: {}".format(milk_doses), delay=80)


def receive_milk_doses():
    """
    Reçoit la quantité de lait consommée depuis un autre micro:bit.
    """
    global milk_doses
    incoming = radio.receive()
    
    if incoming:
        packet_type, length, content = receive_packet(incoming, session_key)
        if packet_type == "0x03":
            milk_doses = content
            display_milk_doses()
        
def interface():
    """
    Affiche la quantité de lait si le bouton A est pressé.
    """

    if button_a.is_pressed():
        display_milk_doses()

###############
# TEMPERATURE #
###############

def send_temp():
    current_temp = str(temperature())
    send_packet_with_nonce(session_key, "0x04", current_temp)
    if button_b.is_pressed():
        display.scroll(current_temp)

##############
# ETAT EVEIL #
##############
def degrée_agitation():
    global durée_mouvement
    état = "endormi"
    if accelerometer.was_gesture('2g') or accelerometer.was_gesture('shake'):
        état = "agité"
    if accelerometer.was_gesture("3g") or accelerometer.was_gesture("freefall"):
        état = "tagité"
    return état

def etat():
    état = degrée_agitation()
    if état == "endormi":
        send_etat(état)
        sleep(300)
    if état == "agité":
        send_etat(état)
        sleep(2000)
    if état == "tagité":
        send_etat(état)
        for x in range(2):
            music.play(['C4:4', 'D4', 'E4', 'C4'])
        for x in range(2):
            music.play(['E4:4', 'F4', 'G4:8'])
        sleep(2000)
    

def send_etat(état):
    send_packet_with_nonce(session_key, "0x05", état)
    send_packet_with_nonce(session_key, "0x05", état)
    send_packet_with_nonce(session_key, "0x05", état)
    send_packet_with_nonce(session_key, "0x05", état)
    send_packet_with_nonce(session_key, "0x05", état)
    send_packet_with_nonce(session_key, "0x05", état)
    send_packet_with_nonce(session_key, "0x05", état)
        

########
# MAIN #
########

def main():
    open()
    initialising()
    if connexion_established:
        while True:
            display.show(Image.DUCK)
            receive_milk_doses()
            interface()
            send_temp()
            etat()
            
            
main()



