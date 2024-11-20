from microbit import *
import music
import radio
import speech
import time
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
    if temp:
        msg = temp.split("|")
        return msg

def if_states(msg):
    
    while msg[0] == "0x05":
        if msg[2] == "reveillé":
            display.show(Image.HAPPY)
        
        if msg[2] == "agité":
            display.show(Image.SURPRISED)

        if msg[2] == "tagité":
            for i in range(3):
                display.show(Image.ANGRY)
                speech.say('Baby ALERT', speed=90)
                
                time.sleep_ms(600)
                music.play(music.JUMP_UP)
                time.sleep_ms(600)
            display.clear()



def main():
    radioconfig()
    open()
    while True:
        
        msg = getmsg()

        if msg:
            if_states(msg)

        else:
            display.show(Image.ASLEEP)


main()


        