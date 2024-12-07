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
connexion_key = None
nonce_list = set()
baby_state = 0
milk_doses = 0 
is_parent = True
interface_active = False
temperatur = None
max_nonce_size = 50 #max nonce dans la tuple
ignore_alert_until = 0 #pour les alertes temp


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
    
def add_nonce(nonce):
    """
    Ajoute un nonce à la liste tout en limitant la taille.
    """
    if len(nonce_list) >= max_nonce_size:
        nonce_list.pop()  # Supprime un élément aléatoire (ou le plus ancien avec une structure adaptée) pour ne pas avoir un MemoryError
    nonce_list.add(nonce)
    
def send_packet_with_nonce(key, type, content):
    """
    Envoie un paquet avec un nonce unique pour éviter les attaques de rejeu.
    """
    nonce = generate_nonce()
    message = (nonce + ":" + content)
    send_packet(key, type, message)
    add_nonce(nonce)
    
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
            add_nonce(nonce)
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
    global session_key
    """
    Réponse au challenge initial de connection avec l'autre micro:bit.
    Retourne True si la connexion est réussie, False sinon.
    """
    incoming = radio.receive()  # Recevoir un challenge
    if incoming:
        type, length, challenge = receive_packet(incoming, key)
        if type == "0x01":
            response = calculate_challenge_response(challenge)
            send_packet_with_nonce(key, "0x02", response)
            session_key = key+response  # Générer une clé de session
            return True
    return False

########
# INIT #
########

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
        display.show(Image.ALL_CLOCKS, delay=100, loop=False, clear=True,)
        if respond_to_connexion_request(key) == True:
            display.show(Image.YES)  # Afficher un symbole de réussite
            sleep(1000)
            connexion_established = True
            return connexion_established
   
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
    
def send_milk_doses():
    """
    Envoie la quantité de lait consommée à l'autre micro:bit via la radio.
    """
    send_packet_with_nonce(session_key, "0x03", str(milk_doses))

def handle_buttons():
    """
    Gère les boutons pour les fonctionnalités :
    A : Ajouter une dose de lait.
    B : Supprimer une dose de lait.
    logo : Réinitialiser à zéro.
    """
    global milk_doses
    if interface_active:
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

###############
# TEMPERATURE #
###############

def receive_temp():
    global temperatur
    incoming = radio.receive()
    if incoming:  # Regarde si il y a un message
        packet_type, length, content = receive_packet(incoming,session_key)
        if packet_type == "0x04":
            temperatur = int(content)  # Upadate la valeur temperatur (temperature) si il recois un packet de type TEMP et la mets en entier

def display_temp():
    if temperatur is not None:  # Check if temp has a valid value
        display.scroll(str(temperatur))  # Display the temperature
    if temperatur is None:
        display.scroll("NONE")
        
def alerte_parent():#CHATGPTED
    music.set_tempo(ticks=4, bpm=200) 
    alert_song = [
        'c4:4', 'e4:4', 'g4:4', 'c5:2',  # Montée rapide
        'r4:2',  # Pause rapide
        'c5:4', 'g4:4', 'e4:4', 'c4:2',  # Descente rapide
        'r4:2',  # Pause rapide
        'c4:4', 'c4:4', 'c4:4', 'r4:2',  # Rebond répétitif pour alerte
    ]
    music.play(alert_song, wait=False, loop=False)
    music.set_tempo(ticks=4, bpm=120)
    
def ignore_alert():
    global ignore_alert_until  # Initialise le temps jusqu'auquel les alertes sont ignorées
    if pin_logo.is_touched() and interface_active == False:
        ignore_alert_until = running_time() + 60000  # Ignorer les alertes pour 60 secondes
        display.show(Image.NO)
        sleep(1000)
        display.scroll("ALERTS MUTED FOR 1m", delay = 60)

def temp():
    global temperatur
    global ignore_alert_until  # Initialise le temps jusqu'auquel les alertes sont ignorées
    
    receive_temp()  # Met à jour la température initialement
    
    if button_b.is_pressed() and interface_active == False:  # Affiche la température si le bouton B est pressé
        display_temp()
    
    # Vérifie si le bouton A est pressé pour ignorer les alertes

    
    # Détecte si la température dépasse les seuils autorisés
    if temperatur is not None:
        # Si la température est trop élevée et que les alertes ne sont pas ignorées
        if temperatur > 35 and running_time() > ignore_alert_until:
            alerte_parent()
            display.show("!")
            sleep(1000)
            display.scroll("HIGH TEMPERATURE", delay=50, wait=True)
            receive_temp()
        
        # Si la température est trop basse et que les alertes ne sont pas ignorées
        elif temperatur < 25 and running_time() > ignore_alert_until:
            alerte_parent()
            display.show("!")
            sleep(1000)
            display.scroll("LOW TEMPERATURE", delay=50, wait=True)
            receive_temp()

##############
# ETAT EVEIL #
##############




def interface(): #état d'éveil du bébé
    global baby_state
    
    if baby_state == 0:
        display.show(Image.ASLEEP)
    if baby_state == 1:
        display.show(Image.HAPPY)
    if baby_state == 2:
    
        display.show(Image.SAD)
        if running_time() > ignore_alert_until:
            alerte_parent()
        sleep(2000)
        display.scroll("CHEK BABY", delay=50, wait=True)

def etat():
    global baby_state
    incoming = radio.receive()
    if incoming:  # Regarde si il y a un message
        packet_type, length, content = receive_packet(incoming, session_key)
        if packet_type == "0x05":
            if content == "endormi":
                baby_state = 0
            if content == "agité":
                baby_state = 1
            if content == "tagité":
                baby_state = 2

        
    interface()
    



########
# MAIN #
########

def main():
    open()
    initialising()
    if connexion_established:
        while True:
            etat()
            toggle_interface()  # Gère l'activation/désactivation de l'interface
            if interface_active and is_parent: # Si l'interface est active et que le micro:bit est parent
                handle_buttons()  # Parent : Gère les boutons
            temp() # Gère la température
            ignore_alert() # Gère l'ignorance des alertes
            
            
        

main()
