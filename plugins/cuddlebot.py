plugName = 'Cuddle Bot'

def plugid_genName(inMSG):
	#This makes sure this is only triggered when BennuBot recieves a message
	if not inMSG or len(inMSG) != 6:
        return
	sendMSG(inMSG[0], inMSG[1], inMSG[2], inMSG[3])	
	if inMSG[0] == '/me cuddles Panties':
        sendMSG('/me cuddles ' + inMSG[4], inMSG[1], inMSG[2], inMSG[3])                

def load():
    global funcs
    funcs = dict(funcs.items() + [('functrigger', plugid_callName)])
	return plugid_genName