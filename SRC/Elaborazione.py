#!/usr/bin/python
from ClassiComuni import *
from os import listdir
from os.path import isfile, join
import shutil   #   serve per fare il move dei file
import pyproj   #   per il calcolo di Lon Lat Alt


#-------------------------------------------------------------------

class Elabora:
    def __init__(self, conf, ftpConn, CGPSconf):
        self.ftpConn = ftpConn
        self.cfg = conf
        self.dbData_ar = []         #  Array stazioni dal DB_File, dopo il confronto restano le stazioni che non esistono piu su FTP
        self.ftpData_ar = []        #  Array stazioni da FTP, dopo il confronto restano le stazioni che non esistono piu su DB_File
        self.difData_ar = []        #  Array stazioni con data diversa fra DB_File ed FTP
        self.RepoDir_ar = []
        self.NetList_ar = []
        self.stazEscluse_ar = []
        self.Update = False
        self.sendMail = False
        self.RcvAntDat_ar = CGPSconf.RcvAntDat_ar
        self.RcvrAntTab_ar = CGPSconf.RcvrAntTab_ar
        self.AntModDat_ar = CGPSconf.AntModDat_ar
        self.minLon = CGPSconf.par_ar[9]
        self.maxLon = CGPSconf.par_ar[10]
        self.minLat = CGPSconf.par_ar[11]
        self.maxLat = CGPSconf.par_ar[12]



    def InitDbRif(self):
        self.ftpData_ar = []
        self.NetList_ar = []
        self.stazEscluse_ar = []
        self.dbData_ar = []
        self.difData_ar = []
        self.RepoDir_ar = []
        self.Update = False


        sApp = ' '.join(['\nLog:', time.ctime()])
        self.cfg.Log.AddLog(sApp, False)

        if os.path.isfile(self.cfg.fileNetList):  # se non esiste, creo il DB di riferimento
            with open(self.cfg.fileNetList) as file:
                arApp = file.readlines()
                file.close()
                for i, line in enumerate(arApp):
                    sApp = line.replace('\t', ' ')
                    if (sApp <> '') and (sApp <> '\n'):
                        arApp1 = sApp.split()
                        if len(arApp1) == 7:
                            # self.NetList_ar.append(sApp)
                            self.NetList_ar.append('\t'.join(arApp1))
                        elif len(arApp1) < 7:
                            self.cfg.Log.AddLog(''.join(['\nATTENZIONE: verificare riga: %d\n%s\n del file Lista stazioni: %s\n\t-> per essere elaborata deve avere 7 campi separati dal (tab)'%(i+1, arApp[i], self.cfg.fileNetList), '\n\n']),False)
                            self.Update = True
                        else:
                            self.stazEscluse_ar.append(sApp) #   lista delle stazioni escluse, usata per ripulire gli altri array
                self.NetList_ar = list(sorted(self.NetList_ar))
        else:
            self.cfg.Log.AddLog(''.join(['\nATTENZIONE: manca il file Lista stazioni: ', self.cfg.fileNetList,'\n\n']), True)
            return False





        self.ftpData_ar = self.ftpConn.dirLink()

        if not self.ftpData_ar:
            self.Update = True
            return False        # restituisce esito dovuto alla connessione
        # self.ftpData_ar = self.ftpConn.prendiUltimoLog(self.ftpData_ar) #   garantische che ogni ID stazione sia unico ed il piu' recente



        if not os.path.isfile(self.cfg.fileDB):  # se non esiste, creo il DB di riferimento
            self.dbData_ar = self.ftpData_ar
            self.UpdateDB(self.ftpData_ar)
            self.cfg.Log.AddLog('\nATTENZIONE: manca DB, impossibile fare un confronto...',True)
            self.cfg.Log.AddLog(''.join(['\nArchivio DB creato: ', self.cfg.fileDB,'\n\n']),False)
        else:  # altrimenti leggo il file DB
            with open(self.cfg.fileDB) as file:
                self.dbData_ar = file.readlines()
                file.close()


        if not self.cfg.gsac:   #   per reti GSAC la dir "Log_Repo" e' sempre vuota, quindi salto il blocco
            dirAppCompleto = list(sorted([f for f in listdir(self.cfg.DIR_Log_Repo) if isfile(join(self.cfg.DIR_Log_Repo, f))]))  #   directory originale, con caratteri upper e/o lower case
            self.RepoDir_ar = self.ftpConn.prendiUltimoLog(dirAppCompleto)  #   directory formato [lower\tfname\t\t\n]
            arApp, dirAppCompleto, arApp = self.cfg.FiltroArray(self.RepoDir_ar, dirAppCompleto,'nf')    #   toglie i file comuni, su dirAppCompleto restano i file in piu'
            for nFile in dirAppCompleto:
                self.spostaFile(nFile, self.cfg.DIR_Log_Repo, self.cfg.DIR_OLD, True)

            if self.cfg.NET == 'CAMPANIA':
                self.dbData_ar = []    #   caso Campania: il sito non da info sulla data, azzero il REPO per scaricare sempre i files

            arApp, arApp1, self.dbData_ar = self.cfg.FiltroArray(self.dbData_ar, self.RepoDir_ar,'nf')  # rendo il dbData coerente con i file in RepoDir

        if len(self.stazEscluse_ar) > 0:
            self.cfg.Log.AddLog('\nEsclusi dal download %d stazioni del file %s:\n' %(len(self.stazEscluse_ar), self.cfg.fileNetList), False)
            for i, sApp in enumerate(self.stazEscluse_ar):
                self.cfg.Log.AddLog('%3d -> %s' %(i+1, sApp), False)
            arApp, self.ftpData_ar, arApp = self.cfg.FiltroArray(self.stazEscluse_ar, self.ftpData_ar, 'id') # escludo le stazioni anche dalle liste, altrimenti continua a chiederle
            arApp, self.dbData_ar, arApp = self.cfg.FiltroArray(self.stazEscluse_ar, self.dbData_ar, 'id')
            arApp, self.RepoDir_ar, arApp= self.cfg.FiltroArray(self.stazEscluse_ar, self.RepoDir_ar, 'id')  #   le stazioni nel Repo, anche vecchie devono cmq essere elaborate



        return True                 #   restituisce esito dovuto alla connessione



    def UpdateDB(self, arDB):
        # if os.path.exists(self.cfg.fileDB):
        #     os.remove(self.cfg.fileDB)

        file = open(self.cfg.fileDB, 'w')
        for line in arDB:
            file.write(line)
        file.flush()
        file.close()




# ---


    def spostaFile(self, nFile, fromDir, toDir, wTStamp):
        if nFile == '':
            return

        if nFile.find('\t') > 0:
            nFile = nFile.split('\t')[1]

        if wTStamp:
            nFileDest = time.strftime('%y%m%d_%H%M%S_') + nFile
        else:
            nFileDest = nFile
        try:
            nFile = fromDir + '/' + nFile
            if os.path.isfile(nFile):
                shutil.move(nFile, toDir + '/' + nFileDest)
        except IOError, e:
            print e


#---


    def ConfrontoDataFtp_Fdb(self, LogScan, language):
        self.LogScan = LogScan
        self.Update = False
        self.sendMail = False

        sApp = '\n\nTotalizzatore elenco Stazioni: ' \
               '\n NetList: \t %3d \tstazioni in lista' \
               '\n!NetList: \t %3d \tstazioni escluse dalla lista' \
               '\n DB_file: \t %3d \tstazioni in lista presenti su FTP' \
               '\n DB_ftp:  \t %3d \tstazioni in totale su FTP' \
               '\n LogRepos:\t %3d \tLog file in Log_Repo\n\n' % (len(self.NetList_ar), len(self.stazEscluse_ar),len(self.dbData_ar), len(self.ftpData_ar), len(self.RepoDir_ar))
        self.cfg.Log.AddLog(sApp, False)

        # *********** Confronto fDB <-> FTP, la funz. FiltroArray restituisce anche la differenza  **********

        if (len(self.ftpData_ar) > 0) and self.ftpData_ar[0].split('\t')[2] != '':        #   se esiste informazione sulla data
            dbApp, ftpApp, commAr = self.cfg.FiltroArray(self.dbData_ar, self.ftpData_ar,'dt')  #   confronto le date
        else:
            dbApp, ftpApp, commAr = self.cfg.FiltroArray(self.dbData_ar, self.ftpData_ar,'nf')  #   confronto nome file

        if len(ftpApp) > 0:     #   questi file sono FTP nuovi rispetto al DB, bisogna aggiornare il fDB con questi nuovi file (append nuovi ID o sostituizione se stesso ID)
            ftpApp, arApp, commAr = self.cfg.FiltroArray(ftpApp, self.NetList_ar, 'id')

            if self.cfg.gsac:
                self.confrStazGSAC(ftpApp, commAr)      # le stazioni GSAC, non scaricano log file ma direttamente gli stf. Bisogna solo aggiornare la lista di stazioni
            else:
                self.scaricaLog(ftpApp, commAr, language)   # Confronta la lista dei Log e li scarica nelle opportune dir

        if self.Update:                     # aggiorno il fDB dopo tutte le modiche
            self.dbData_ar = self.ftpConn.prendiUltimoLog(self.dbData_ar)
            self.UpdateDB(self.dbData_ar)   # aggiorno il fDB dopo tutte le modiche

        return True  # restituisce esito dovuto alla connessione


# #------------------------------------------------------------------


    def scaricaLog(self, ftpApp, commAr, language):   # scarico Log file (caso non gsac in quanto non esistono log)
        if len(commAr) > 0:  # Metto in FTPnew i file FTP nuovi appartenenti alla NetList quindi in "commAr"
            self.cfg.Log.AddLog('\nAggiornamento stazioni della NetList:', False)
            # if not self.ftpConn.fDownload(commAr, self.ftpData_ar, self.cfg.FTP_DIR_NewLog):  # scarico solo i file Log con date diverse
            if not self.ftpConn.fDownload(commAr, self.cfg.FTP_DIR_NewLog):  # scarico solo i file Log con date diverse
                return False
            [self.dbData_ar.append(row) for row in commAr]
            self.Update = True

        if len(ftpApp) > 0:  # questi file sono nuovi ma non nella NetList, quindi li metto nel LogRepo
            self.cfg.Log.AddLog('\n\nAggiornamento stazioni fuori NetList:', False)

            # if not self.ftpConn.fDownload(ftpApp, self.ftpData_ar,self.cfg.DIR_Log_Repo):  # scarico solo i file Log con date diverse
            if not self.ftpConn.fDownload(ftpApp, self.cfg.DIR_Log_Repo):  # scarico solo i file Log con date diverse
                return False
            [self.dbData_ar.append(row) for row in ftpApp]
            self.Update = True

            # verifia queste stazioni rientrano nel range di interesse
            ecef = pyproj.Proj(proj='geocent', ellps='WGS84', datum='WGS84')
            lla = pyproj.Proj(proj='latlong', ellps='WGS84', datum='WGS84')
            for n, staz in enumerate(ftpApp):
                Log_ob = self.LogScan.CaricaLog(self.cfg.DIR_Log_Repo + '/' + staz.split('\t')[1], language)

                if (Log_ob == None) or (any(Log_ob.p2_val) == None):  # verifico solo se possibile caricare il file
                    self.cfg.Log.AddLog('\nWarning: non possibile verificare coordinate XYZ con : %s' % (
                    self.cfg.DIR_Log_Repo + '/' + staz.split('\t')[1]), False)
                    continue

                # calcolo LON, LAT dalle coordinate X,Y: VERIFICARE !!!
                lon, lat, alt = pyproj.transform(ecef, lla, Log_ob.p2_val[0], Log_ob.p2_val[1], Log_ob.p2_val[2],
                                                 radians=False)
                self.cfg.Log.AddLog('\n%3d %s\tlon= %6.4f lat= %6.4f alt= %6.4f\t\t-> ' % (n + 1, staz[:4], lon, lat, alt),
                                    False)
                if any([lon < self.minLon, lon > self.maxLon, lat < self.minLat, lat > self.maxLat]) == True:
                    self.cfg.Log.AddLog('AREA INTERESSE: FUORI', False)
                else:
                    self.cfg.Log.AddLog('AREA INTERESSE: OK', False)
                    self.sendMail = True


#------------------------

    def confrStazGSAC(self, ftpApp, commAr):
        if len(commAr) > 0:  # Metto in FTPnew i file FTP nuovi appartenenti alla NetList quindi in "commAr"
            self.cfg.Log.AddLog('\nAggiornamento %2d stazioni GSAC della NetList:' %len(commAr), False)
            for num, staz in enumerate(commAr):
                self.cfg.Log.AddLog('\n%2d\t%s' % (num, staz.split('\t')[0]), False)
            [self.dbData_ar.append(row) for row in commAr]
            self.Update = True
            self.sendMail = True

        if len(ftpApp) > 0:  # questi file sono nuovi ma non nella NetList, quindi li metto nel LogRepo
            self.cfg.Log.AddLog('\n\nAggiornamento %2d stazioni GSAC fuori NetList:' %len(ftpApp), False)
            for num, staz in enumerate(ftpApp):
                self.cfg.Log.AddLog('\n%2d\t%s' % (num, staz.split('\t')[0]), False)
            [self.dbData_ar.append(row) for row in ftpApp]
            self.Update = True
            self.sendMail = True




