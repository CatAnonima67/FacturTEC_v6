curp = "VIRE040511HGRLPRS4"
rfc = "VIRO030721LMS"
apellidop = "Vielma"
apellidom = "Pintor"
apellidopH = "Locas"
apellidomH = "Pintor"

def validarPadreHijo(curps, rfcs,apellidop,apellidom,apellidopH,apellidomH):
        curp_relevante = curp[:10] + curp[13:16]
        curpCMama = curp[3]
        if (curp_relevante[:2] == rfc[:2] or curpCMama == rfc[3])and(apellidom == apellidomH or apellidop == apellidopH) :
                es_valido = True
        else:
            es_valido = False
        return es_valido

def lol():  
    if not validarPadreHijo(curp,rfc, apellidop, apellidom, apellidopH, apellidomH):
        print("Es ")

lol()