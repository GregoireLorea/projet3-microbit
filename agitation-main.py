##############
# ETAT EVEIL #
##############
def degrée_agitation():
    global durée_mouvement
    état = "endormi"
    x = accelerometer.get_x()
    y = accelerometer.get_y()
    z = accelerometer.get_z()

    # l'intensité du mouvement
    intensity = math.sqrt(x**2 + y**2 + z**2)

    # Seuils d'intensité
    ampleur_agité = 910
    ampleur_très_agité = 1900  #trouvé par test

    # Seuils de durée pour changer d'état
    durée_agité = 5
    durée_très_agité = 10    #trouvé par test

    

    # Mise à jour de la durée du mouvement selon l'intensité
    if intensity > ampleur_très_agité:
        durée_mouvement += 1
        if durée_mouvement > durée_très_agité:
            return "très agité"
            
        
    elif intensity > ampleur_agité:
        durée_mouvement += 1
        if durée_mouvement > durée_agité:
            return "agité"
        
    else:  # Si l'intensité est faible
        durée_mouvement = 0
        return "endormi"

    return état

def etat():
    état = degrée_agitation()

    if état == "endormi":
        send_packet_with_nonce(key, "ETAT", état)
    elif état == "agité":        
        send_packet_with_nonce(key, "ETAT", état)
        sleep(2000)
    elif état == "très agité":
        send_packet_with_nonce(key, "ETAT", état)   
        sleep (10000)