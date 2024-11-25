from microbit import *
import radio
import random
import music

#Can be used to filter the communication, only the ones with the same parameters will receive messages
#radio.config(group=23, channel=2, address=0x11111111)
#default : channel=7 (0-83), address = 0x75626974, group = 0 (0-255)

#Initialisation des variables du micro:bit
radio.on()
connexion_established = False
key = "KEYWORD"
connexion_key = None
nonce_list = set()
baby_state = 0

#Quantité de lait variable
milk_doses = 0 
is_parent = True
interface_active = False
temperatur = None


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
        #Letters encryption/decryption
        if char.isalpha():
            key_index = i % key_length
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
            key_index = i % key_length
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
    
def send_packet(key, type, content):
    """
    Envoi de données fournies en paramètres
    Cette fonction permet de construire, de chiffrer puis d'envoyer un paquet via l'interface radio du micro:bit

    :param (str) key:       Clé de chiffrement
           (str) type:      Type du paquet à envoyer
           (str) content:   Données à envoyer
	:return none
    """
    message = (type + "|" + str(len(content)) + "|" + str(content))  # Construire le message
    encrypted_message = vigenere(message, key)  # Chiffrer le message
    radio.send(encrypted_message)  # Envoyer via l'interface radio

def send_packet_with_nonce(key, type, content):
    """
    Envoie un paquet avec un nonce unique pour éviter les attaques de rejeu.
    """
    nonce = generate_nonce()
    message = (nonce + ":" + content)
    send_packet(key, type, message)
    nonce_list.add(nonce)
    
#Unpack the packet, check the validity and return the type, length and content
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

def receive_packet(packet_received, key):
    """
    Traite les paquets reçus via l'interface radio du micro:bit.
    Si un nonce est détecté comme déjà utilisé, le message est ignoré.
    """
    type, length, message = unpack_data(packet_received, key)
    if message:
        nonce, content = message.split(':', 1)
        if nonce not in nonce_list:  # Vérifie que le nonce est unique
            nonce_list.add(nonce)
            return type, length, content
    return "", 0, ""


#Calculate the challenge response
def calculate_challenge_response(challenge):
    """
    Calcule la réponse au challenge initial de connection envoyé par l'autre micro:bit

    :param (str) challenge:            Challenge reçu
	:return (srt)challenge_response:   Réponse au challenge
    """
    challenge_reponse = hashing(challenge)
    return challenge_reponse

#Respond to a connexion request by sending the hash value of the number received
def respond_to_connexion_request(key):
    """
    Réponse au challenge initial de connection avec l'autre micro:bit.
    Retourne True si la connexion est réussie, False sinon.
    """
    incoming = radio.receive()  # Recevoir un challenge
    if incoming:
        type, length, challenge = receive_packet(incoming, key)
        if type == "CHALLENGE":
            response = calculate_challenge_response(challenge)
            send_packet_with_nonce(key, "RESPONSE", response)
            return True
        elif type == "RESPONSEY":
            return True
    return False


def open():
    """
    Allumage du microbit
    """
    music.play(music.JUMP_UP)
    display.show(Image.HOUSE)
    sleep(1000)
    display.scroll('Be:Bi Parent', delay=60)

def initialising():
    """
    Connexion entre les deux microbits
    """
    global connexion_established
    start_time = running_time()  # Temps de départ
    while running_time() - start_time < 15000:  # Timeout de 15 secondes
        # respond_to_connexion_request(key)
        # display.show(Image.ALL_CLOCKS, delay=100, loop=False, clear=True)
        if respond_to_connexion_request(key) == True:
            display.show(Image.YES)  # Afficher un symbole de réussite
            sleep(1000)
            connexion_established = True
            return connexion_established
   
    while True:
            display.show(Image.NO)  # Afficher un symbole d'échec
            sleep(5000)
            display.scroll("ERROR CONNECTION: REBOOT MICROBITS", delay=60)



def display_milk_doses():
    """
    Affiche la quantité de lait consommée en doses sur le panneau LED.
    """
    display.scroll("Milk: {}".format(milk_doses), delay=80)
    
def send_milk_doses():
    """
    Envoie la quantité de lait consommée à l'autre micro:bit via la radio.
    """
    send_packet_with_nonce(key, "MILK", str(milk_doses))

def handle_buttons():
    """
    Gère les boutons pour les fonctionnalités :
    A : Ajouter une dose de lait.
    B : Supprimer une dose de lait.
    logo : Réinitialiser à zéro.
    """
    global milk_doses

    # Ajouter une dose de lait
    if button_a.was_pressed():
        milk_doses += 1
        display.show(Image.HAPPY)
        sleep(500)
        display_milk_doses()
        send_milk_doses()

    # Supprimer une dose de lait
    elif button_b.was_pressed():
        if milk_doses > 0:
            milk_doses -= 1
        display.show(Image.SAD)
        sleep(500)
        display_milk_doses()
        send_milk_doses()

    # Réinitialiser la quantité de lait
    if pin_logo.is_touched():
        milk_doses = 0
        display.show(Image.NO)
        sleep(500)
        display_milk_doses()
        send_milk_doses()


def toggle_interface():
    """
    Active ou désactive l'interface de gestion en fonction d'une pression longue.
    """
    global interface_active

    # Vérifie une pression longue sur le bouton A
    if button_a.is_pressed():
        start_time = running_time()
        while button_a.is_pressed():
            if running_time() - start_time > 2000:  # Appui long (2 secondes)
                interface_active = not interface_active
                display.show(Image.YES if interface_active else Image.NO)
                sleep(1000)
                return


def receive_temp():
    global temperatur
    incoming = radio.receive()
    if incoming:  # Check if there is a message received
        packet_type, length, content = receive_packet(incoming, key)
        if packet_type == "TEMP":
            temperatur = int(content)  # Update the temp value if a TEMP packet is received

def display_temp():
    if temperatur is not None:  # Check if temp has a valid value
        display.scroll(temperatur)  # Display the temperature

def temp():
    receive_temp()
    if button_b.is_pressed():
        display_temp()
        
        



def main():
    open()
    initialising()
    if connexion_established:
        while True:
            display.show(Image.ASLEEP)
            toggle_interface()  # Gère l'activation/désactivation de l'interface
            if interface_active and is_parent:
                handle_buttons()  # Parent : Gère les boutons
            
            temp()
        

main()
