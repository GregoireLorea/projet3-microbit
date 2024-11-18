from microbit import *
import music
import radio

def radioconfig(): 
    radio.config(group=7, power=7)
    radio.on()

def open():
    music.play(music.JUMP_UP)
    display.show(Image.HOUSE)
    sleep(1000)
    display.scroll('Be:Bi Parent', delay=60)

def getmsg():
    temp = str(radio.receive())
    msg = temp.split("|")
    return msg



open()
# while True

#     en fonction de l'état deveil du bb, afficher et prévenir parent
#     en fonction de l'ampleur et de la durée de mouvement bb, prévenir parent
#     if 
#     if 
#     if


def main():
    radioconfig()
    open()
    while True:
        
        getmsg()
        global msg

        if msg

        