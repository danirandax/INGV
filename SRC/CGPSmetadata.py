#!/usr/bin/python

from multiprocessing import Process
from daemon import Daemon
#from Elaborazione import *
from StationInfo import *
from TranslationTable import *
import sys

"""
Autore: Daniele Ranazzo - INGV Bologna
data: 15/12/2016 16:51

# Attivare il python 2.7
# per rivedere il processo usa
ps -eo pid,etime,cmd | grep CGPSmetadata.py | nl

# Copiare sul server spritz
#da PC sorgente:
scp /opt/CGPSmetadata/SRC/*.* gamit@spritz:/opt/CGPSmetadata/SRC
scp /opt/CGPSmetadata/Configurazioni/*.* gamit@spritz:/opt/CGPSmetadata/Configurazioni

# per girare in background usa
# ineriere la shebang (ovvero #!/usr/bin/python)
nohup python CGPSmetadata.py start &

# FTP EUREF
ftp://anonymous@igs-rf.ign.fr/pub/sitelogs/epn/

# Formato station_info su spritz:
cd /data/archive/log/CGPS/stf/EUREF
"""

#------------------------------------------------------------------

class daemEPOS(Daemon):
    def __init__(self, nNET, CGPSconf):
        self.nNET = nNET
        self.CGPSconf = CGPSconf
        self.NET = CGPSconf.NETar[nNET]
        self.pidfile = '/tmp/daemon_' + self.NET + '.pid'
        self.MailAttiva = CGPSconf.par_ar[5]


    def run(self):      # OVERRAIDED PROCEDURE CALLED BY THE DAEMON

        conf = Configurazione(self.nNET, self.CGPSconf)  # load configuration and global variables
        ftpConn = FTP(conf)              # crea le variabili usate in tutto il codice
        mail = Mail(conf)         # inizializza la lista destinatari della Mail
        elabNET = Elabora(conf, ftpConn, self.CGPSconf)           # initialise elaboration data
        TimerEv = TimerEventi(conf.Time_ar, conf.WeekDay)         # Timer to run the process
        gpsLog = LogScan(elabNET)                        # log file manager
        tTab = TranslationTable(elabNET)                 # load CheckTable e TranslatioTable to match RECEIVER, ANTENNA and DUOMO codes
        gpsStf = StationInfo(conf, elabNET, ftpConn, gpsLog, tTab)       # procedures to create station-info files

        if conf.NET == 'RENEP':
            language = 1            # Portuguese
        else:
            language = 0            # English

        print('processo %2d = %s\t\tppid= %d\tpid= %d' %(self.nNET, self.CGPSconf.NETar[self.nNET],os.getppid(), os.getpid()))


        while True: # *********** LOOP TO RUN ACCORDING THE TIME TABLE
            if TimerEv.CheckTime():
                if elabNET.InitDbRif():
                    if elabNET.ConfrontoDataFtp_Fdb(gpsLog, language):
                        gpsLog.LogCompFTPnew_LogRepo(language)  # LOAD THE WEB AND REPOSITORY STATUS IMAGE INTO ARRAYS
                    gpsStf.checkStfDir(language)                # MATACH EACH STATION OF THE NETWORK
                    # gpsStf.cambioParStorico()                   # Trova il cambio dei parametri nello storico STF

                    tTab.AggiornaTTab()                         # UPDATE THE TRANSLATION TABLE
                    conf.cancOLDfiles(conf.DIR_OLD, 30)         # DELETE OLDER FILES (NUMBER OF DAYS)


                if elabNET.sendMail and self.MailAttiva:        # ENABLE TO SEND MAIL ALERTS
                    fp = open(elabNET.cfg.Log.fLog, 'rb')
                    mail.sendMail(fp.read(),conf.NET+'_sw_CGPS_Metadata_update')
                    fp.close()
            time.sleep(20)  # TIME INTERVAL
            conf.Log.closeLF()






#TODO detect del cambio di almento uno dei seguenti parametri: altezza, Rcvr (e SN) o Ant(e SN)

#TODO Verifica ultima data dei logfile, alert su non aggiornati da dTT






#----------------------------------------------------


if __name__ == "__main__":



    def CreaProcessi(Avvio):            # CREATE AS MANY PROCESSES AS THE NETWORKS, EACH PROCESS IS RUN AS A DAEMON

        CGPSconf = CGPSconfigurazioni() # LOAD COMMON CONFIGURATIONS
        for nNET, NET in enumerate(CGPSconf.NETar): # ITERATE TO RUN THE PROCESSES PASSING THE PARAMETERS
            p = Process(target=CreaDemone, args=(nNET, CGPSconf, Avvio)) # EACH PROCESS CREATE A DAEMON
            p.start()
            p.join()
        ControlloProcessi(Avvio)




    def CreaDemone(nNET, CGPSconf, Avvio):
        daemon = daemEPOS(nNET, CGPSconf)
        if Avvio:
            daemon.start()
        else:
            daemon.stop()


#------------------


    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            CreaProcessi(True)
        elif 'stop' == sys.argv[1]:
            CreaProcessi(False)
        # print(' '.join(['\nProcesso',sys.argv[0], 'interrotto con regolare STOP\n']))
        # elif 'restart' == sys.argv[1]:
        #     daemon.restart()
        else:
            print("Unknown command")
            sys.exit(2)
        sys.exit(0)
    else:
        print("usage: %s start|stop|restart" % sys.argv[0])
        sys.exit(2)



#-----------------------------

#   todo a fine ciclo leggi i PID con:
#   os.system('ps -eo pid,cmd|grep CGPSmetadata.py')
#   bisogna leggere il PID dai file /tmp/daemon_stazione.pid
#   dopo aver atteso 10 sec che tutti i processi siano realmente attivi
#   cat /tmp/daemon_*   ->  pid \t NET
