from microbit import *
import music
import radio

def radioconfig():  
    radio.config(group=7, power=7)#on config la radio, groupe 07, et power=7 pour la distance
    radio.on() #on allume la radio
    
def open():
    music.play(music.JUMP_UP)
    display.show(Image.DUCK)
    sleep(1000)
    display.scroll('Be:Bi Enfant', delay=60)

def states(): #0x01
    if accelerometer.was_gesture() != accelerometer.is_gesture():
        radio.send("0x05|7|reveillé")#implémenter message pour parent (reveillé)
    
    if accelerometer.was_gesture('shake'):
        radio.send("0x05|5|agité")#implémenter message pour parent (agité)

    if accelerometer.was_gesture('freefall'):
        radio.send("0x05|6|tagité")#implémenter message pour parent (très agité)



def microphone():
    while True:
        if microphone.current_event() == SoundEvent.LOUD:
                radio.send([""])#envoie a bbi parent qu'il est réveillé
                
                for x in range(2):#joue frère jaques (optionnel)
                    music.play(['C4:4', 'D4', 'E4', 'C4'])

                for x in range(2):
                    music.play(['E4:4', 'F4', 'G4:8'])
                
                    
        if microphone.current_event() == SoundEvent.QUIET:
                radio.send("dodo")


def main():
    radioconfig()
    open()
    while True

        en fonction de son état d'éveil, rassurer bebe
        en fonction de l'ampleur et de la durée de ses mouvements
        if 
        if 
        if
