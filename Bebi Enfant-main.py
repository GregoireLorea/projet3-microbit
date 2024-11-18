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

def states():
    if accelerometer.get_x() > 10 or accelerometer.get_y() > 10 or accelerometer.get_z() > 10:
        radio.send()#implémenter message pour parent (reveillé)
    
    if accelerometer.was_gesture('2g'):
        radio.send()#implémenter message pour parent (agité)

    if accelerometer.was_gesture('6g'):
        radio.send()#implémenter message pour parent (très agité)



def microphone():
    if microphone.current_event() == SoundEvent.LOUD:
        radio.send()#envoie a bbi parent qu'il est réveillé
        for x in range(2):#joue frère jaques
            music.play(['C4:4', 'D4', 'E4', 'C4'])

        for x in range(2):
            music.play(['E4:4', 'F4', 'G4:8'])
    elif microphone.current_event() == SoundEvent.QUIET:
        radio.send()#envoie a bbi parent qu'il est endormi


def main():
    radioconfig()
    open()
    while True

        en fonction de son état d'éveil, rassurer bebe
        en fonction de l'ampleur et de la durée de ses mouvements
        if 
        if 
        if
