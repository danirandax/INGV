#!/usr/bin/python
from CGPSmetadata import *

"""
Autore: Daniele Ranazzo - INGV Bologna
data: 15/12/2016 16:51

# Attivare il python 2.7
source /home/dr/virtenvCGPS/bin/activate
python /opt/CGPSmetadata/SRC/CGPSmetadata.py start


# per girare in background usa
# ineriere la shebang (ovvero #!/usr/bin/python)
nohup python CGPSmetadata.py start &

# per rivedere il processo usa
 ps ax | grep CGPSmetadata.py


# per girare da terminale (sotto python 2.7)
# bisogna modificare owner user:group a questo file:
sudo chown danielerandazzo:root CGPSmetadata.py

# FTP EUREF
ftp://anonymous@igs-rf.ign.fr/pub/sitelogs/epn/

"""



#------------------------------------------------------------------


if __name__ == "__main__":


    def CreaDemone(nNET, CGPSconf, Avvio):
        # daemon = daemEPOS(0, '/tmp/daemon_' + NET + '.pid', NET,CartellaDatiNETs, CartellaNetList, CartellaRcvAntTab, CartellaStfProc, CartellaCopiaSTF, MailAttiva)  # fa girare il run() come override del demone
        daemon = daemEPOS(nNET, CGPSconf)  # fa girare il run() come override del demone
        daemon.run()


#------------------
    CGPSconf = CGPSconfigurazioni()

    CreaDemone(18, CGPSconf, True)   #   indicare il numero corrispondente alla rete
#
# [NETar]	# usare: 1) "#" per commentare, 2) "?" indica reti in test
# EUREF	# 0
# GREF
# SONEL
# ERVA
# ITACYL
# CATNET	# 5
# UNAVCO
# RGP
# VENETO
# STPOS
# CAMPANIA	# 10
# FREDNET
# FVG
# GEODAF
# RING
# REP	# 15
# IGNE
# IGS
# RENEP
# RGAN
# NIGNET 	# 20
# SEGAL
# ALBANIA ?
# RAP
# RENAG ?
# EUSKADI ?	# 25
# SPINGNSS ?
# #ABRUZZO	#   esclusa dall'elaborazione
# #CARM

