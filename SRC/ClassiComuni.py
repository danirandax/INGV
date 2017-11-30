import os, sys
import time
from datetime import date
import datetime
import smtplib
from email.mime.text import MIMEText
import ConfigParser  # usato nella versione python 2.7
import ftplib
import urllib2
import subprocess, signal
import unicodedata
import requests, zipfile, StringIO
#--------------------------------------------------------------




class Configurazione:
    def __init__(self, nNET, CGPSconf):
        self.DirDatiNET = '%s/'%CGPSconf.par_ar[0]        # DirDatiNET
        self.CartellaNetList = '%s/'%CGPSconf.par_ar[1]   # CartellaNetList
        self.CartellaRcvAnt = '%s/'%CGPSconf.par_ar[2]    #CartellaRcvAnt
        self.DirStfProc = '%s'%CGPSconf.par_ar[3]         #CartellaStfProc
        self.CartellaCopiaSTF = '%s'%CGPSconf.par_ar[4]   #CartellaCopiaSTF
        self.NET = CGPSconf.NETar[nNET]
        self.NETar_test = CGPSconf.NETar_test
        self.fileNetList = ''
        self.fCfg = '../Configurazioni/'+ self.NET + '_Conf.cfg'
        self.ftpNET = ''
        self.user = ''
        self.password = ''
        self.gsac = False
        self.fileDB = '../DBfile/fDB_'+self.NET+'.txt'
        self.fTransTab = '../TransTable/' + self.NET + '_transTab.dat'
        self.FTP_DIR_NewLog = self.DirDatiNET + self.NET + '/' + self.NET + '_FtpNewLog'
        self.DIR_Log_Repo = self.DirDatiNET + '/' + self.NET + '/' + self.NET + '_Log_Repo'
        self.DIR_stf = self.DirDatiNET + self.NET + '/' + self.NET + '_STF_Repo'
        self.DIR_OLD = '../LogMail_OLD'
        self.LogMailDIR = self.DIR_OLD
        self.WeekDay = CGPSconf.par_ar[6]
        self.Time_ar = CGPSconf.par_ar[7]
        self.Destinatari = CGPSconf.par_ar[8]
        self.Log = LogFile(self.LogMailDIR, self.NET)   # passa il parametro nome logfile ed inizializza
        self.GetConfig()                                    # dopo aver caricato i param. da file .cfg
#--
        # self.ftpConn = FTP(self.ftpNET,self.user,self.password, self.gsac, self.Log, self.fileNetList)              # crea le variabili usate in tutto il codice
        # self.mail = Mail(self.listaDestinatari)         # inizializza la lista destinatari della Mail




#--

    def GetConfig(self):
        if not os.path.isfile(self.fCfg):
            try:
                os.makedirs(os.getcwd()+'/../Configurazioni')  # Creo la directori col nome della rete
            except OSError, e:
                self.Log.AddLog('Warning: %s' % str(e), False)
                print('Warning: %s' % str(e))
            config = self.CreaDefConf(self.fCfg)
        else:
            config = ConfigParser.RawConfigParser()
            config.read(self.fCfg)

        try:
            self.ftpNET = config.get('NET', 'FTP')
            self.user = config.get('NET', 'Usr')
            self.password = config.get('NET', 'Pwd')
            # self.listaDestinatari = config.get('Mail', 'listaDestinatari').split()
            # self.Time_ar = config.get('LogParams', 'Time_array')
        except:
            print("missing parameter in %s" %self.fCfg)
            exit(2)

        try:
            self.gsac = (config.get('NET', 'GSAC').strip().lower() == 'true')
        except:
            self.gsac = False


        if not os.path.isdir(self.FTP_DIR_NewLog):
            os.makedirs(self.FTP_DIR_NewLog)
        if not os.path.isdir(self.DIR_Log_Repo):
            os.makedirs(self.DIR_Log_Repo)
        if not os.path.isdir(self.DIR_stf):
            os.makedirs(self.DIR_stf)
        if not os.path.isdir(self.DIR_OLD):
            os.makedirs(self.DIR_OLD)
        if not os.path.isdir(self.LogMailDIR):
            os.makedirs(self.LogMailDIR)
        if not os.path.isdir('../DBfile'):
            os.makedirs('../DBfile')
        if not os.path.isdir('../TransTable'):
            os.makedirs('../TransTable')




        self.Log.AddLog('\nCancellazione file STF nelle directory: %s' % (self.DIR_stf), False)
        ld = os.listdir(self.DIR_stf)
        for nFile in ld:
            try:
                os.remove(self.DIR_stf+'/'+nFile)
            except OSError, e:
                # self.Log.AddLog('\nErrore: %s' % (e), False)
                pass    #   quando i processi delle reti girano in contemporanea, i file nella cartella comune vengono cancellati dal primo processo disponibile


        if self.ftpNET == 'ftp://IPaddress/path/':
            print('\ninserire le configurazione della rete %s' %(self.NET))
            sys.exit(3)

        self.fileNetList = self.CartellaNetList + self.NET.lower() + '.list'
        if not os.path.isfile(self.fileNetList):
            self.Log.AddLog('\nFile Lista delle Stazioni non trovato:\n'+self.fileNetList,False)

        archSTF = '%s/%s/stf/'%(self.CartellaCopiaSTF, self.NET)
        if not os.path.isdir(archSTF):
            try:
                os.makedirs(archSTF)  # Creo la directory col nome della rete
            except OSError, e:
                self.Log.AddLog('Warning: %s' % str(e), False)
                print('Warning: %s' % str(e))






    def CreaDefConf(self,fileConf):
        config = ConfigParser.RawConfigParser()
        config.add_section('NET')
        config.set('NET', 'FTP', 'ftp://IPaddress/path/')
        config.set('NET', 'Usr', 'anonymous')
        config.set('NET', 'Pwd', 'anonymous')
        config.set('NET', 'GSAC', 'False')
        config.add_section('LogParams')
        # config.set('LogParams', 'Time_array', '09:00:00 12:00:00 18:00:00') # usa lo spazio come delimitatore fra orari diversi
        config.set('LogParams', 'Time_array', '08:00')   # usa lo spazio come delimitatore fra orari diversi
        config.add_section('Mail')
        config.set('Mail', 'listaDestinatari', 'daniele.randazzo@ingv.it adriano.cavaliere@ingv.it enrico.serpelloni@ingv.it')

        with open(fileConf, 'wb') as configfile:
            config.write(configfile)

        return config

#---

    def cancOLDfiles(self, DIR_OLD, gg):
        for dirpath, dirnames, filenames in os.walk(DIR_OLD):
            for file in filenames:
                try:
                    curpath = os.path.join(dirpath, file)
                    file_modified = datetime.datetime.fromtimestamp(os.path.getmtime(curpath))
                    if datetime.datetime.now() - file_modified > datetime.timedelta(days=gg):
                        os.remove(curpath)
                except:
                    pass

#----


    def FiltroArray(self, ar1, ar2, target):  # confronto fra gli array, conviene ordinati e il primo piu corto
        ar1 = list(sorted(ar1)) #   duplico per non modificare gli array
        ar2 = list(sorted(ar2))     # ATTENZIONE return .append di ar1 !!!
        comm_ar = []
        i = 0
        while i < len(ar1):
            j = 0
            trovato = False
            while j < len(ar2):
                if target == 'lw':   # 'lw' = 'lower case'
                    s1 = ar1[i].split('\t')[0]
                    s2 = ar2[j].split('\t')[0]
                elif target == 'nf': # 'nf' = 'nfile'
                    s1 = ar1[i].split('\t')[1]
                    s2 = ar2[j].split('\t')[1]
                elif target == 'dt': # 'lw' = 'lower case'
                    s1 = '%s%s'%(ar1[i][:4],ar1[i].split('\t')[2][:8])  #   confronta id e data
                    s2 = '%s%s'%(ar2[j][:4],ar2[j].split('\t')[2][:8])
                elif target == 'id':
                    s1 = ar1[i][:4]
                    s2 = ar2[j][:4]
                if s1 == s2:   #   confronto solo nome stazione
                    comm_ar.append(ar1[i])  # contiene solo elementi con nome delle stazioni in comune
                    ar1.pop(i)
                    ar2.pop(j)
                    trovato = True
                    break
                else:
                    j += 1
            if not trovato:
                i += 1
        return ar1, ar2, comm_ar  #   return [stazioni in comune, stazioni non trovate]
# ---



            # #------------------------------------------------------------------



    def salvaStatioInfo(self, fname, stf, fname_proc, stfProc):
        # 1) STF originali (non rinominati) in ARCHIVE: /data/archive/rinex/CGPS/NETS/EUREF/stf/
        # 2) STF rinominati in PROCESSING:              /data/processing/CGPS/setup/stinfo/stf
        # 3) STF_TEST nouve reti :                      /data/processing/CGPS/setup/stinfo/stf_test
        #
        # quelle verificate le metto in 1) e 2)
        # quelle nuove in 3)

        self.salvaArray(fname, self.DIR_stf, stf)  # Copia in DatiNet file originale


        if (self.NET not in self.NETar_test):  # reti VERIFICATE (quindi non in test)
            path = '%s/%s/stf' % (self.CartellaCopiaSTF, self.NET)
            self.salvaArray(fname, path, stf)  # 1) copia in ARCHIVE del file ORIGINALE da condividere

            path = '%s/stf' % (self.DirStfProc)
            self.salvaArray(fname_proc, path, stfProc)  # 2) copia in PROCESSING del file RINOMINATO da processare
        else:
            path = '%s/stf_test' % (self.DirStfProc)
            self.salvaArray(fname_proc, path, stfProc)  # 3) copia in TEST_PROCESSING del file RINOMINATO

            # ---


    def salvaArray(self, fname, DestDir, Arr):  # stID (e stID3c) = codice stazione (e 3^ colonna); stf = array da scrivere su file StationInfo
        try:
            with open('%s/%s' % (DestDir, fname.lower()), 'w') as file:
                file.writelines([lines for lines in Arr])
                file.close()
        except:
            self.Log.AddLog('\nErrore di scrittura del file: %s\n' % (DestDir + '/' + fname), False)




    def caricaArray(self, logFile):
        Log_ar = []
        try:
            file = open(logFile)
            for line in file:
                inValue = line.decode("iso-8859-15")
                normalizedValue = unicodedata.normalize('NFKC', inValue).encode('utf-8')
                Log_ar.append(normalizedValue)
            file.close()
        except:
            pass
        return Log_ar


# #---------------------------------------

class LogFile:

    def __init__(self, logDir, NET):
        self.NET = NET
        self.nLF = NET+'_mail.log'
        self.lDir = logDir
        self.fLog = ''
        self.file = None
        self.dataRif = ''
        self.initLog()


    def initLog(self):
        if not os.path.isdir(self.lDir):
            os.makedirs(self.lDir)

        # Open the file in write mode
        self.dataRif = str(date.today())
        self.fLog = ''.join([self.lDir, '/', self.dataRif, '_', self.nLF])
        self.file = open(self.fLog, 'a+')
        sApp = ' '.join(['\n\n\nLogfile sw CGPSmetadata (Release 11/10/2017) - Rete:', self.NET])   #   versione
        self.file.write(sApp)
        sApp = ' '.join(['\nData inizio:', time.ctime()])
        self.file.write(sApp)
        sApp = '\n-----------------------------------------------------------------\n'
        self.file.write(sApp)
        self.file.flush()






    def AddLog(self, messaggio, wTimeStamp):
        if (self.dataRif <> str(date.today())):
            self.initLog()

        if wTimeStamp:
            sTime = time.ctime()
            sApp = ' '.join([sTime[11:19], messaggio])
        else:
            sApp = messaggio
        self.file.write(sApp)
        self.file.flush()



    def closeLF(self):
        # Close the file
        self.file.close()



#-------------------------------------------------------------

class Mail():
    def __init__(self, config):
        self.lDest = config.Destinatari

    def sendMail(self,text,subject):

        gamit = True   #   abilita la mail
        if gamit:
            # da SPRITZ, indirizzo del server, non ha bisogno di autenticazione, togliere starttls e login
            # ATTIVARE PER INVIO MAIL DA SERVER INGV:
            server = smtplib.SMTP('mail2.bo.ingv.it', 25)  # con la porta 25 oppure 587
        else:
            # Attivare per invio mail da GOOGLE:
            uName = 'just9125@gmail.com'
            pwd = 'tinaturner99'
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(uName, pwd)


        msg = MIMEText(text)
        msg['Subject'] = subject
        msg['From'] = ' CGPSmetadata'
        msg['To'] = ", ".join(self.lDest.split())
        server.sendmail(msg["From"], msg["To"].split(","), msg.as_string())
        server.quit()



#-------------------------------------------------

class FTP:
    # def __init__(self,FTP,User,Password, gsac,Log,fileNetList):
    def __init__(self, config):
        self.conf = config
        self.org = ''
        self.path = ''
        self.monthdict = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4,
                          'May': 5, 'Jun':6, 'Jul': 7, 'Aug': 8,
                          'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}
        self.thisyear = time.localtime().tm_year
        self.thismonth = time.localtime().tm_mon
        self.initFTP()


    def initFTP(self):
        p1 = self.conf.ftpNET.find('//')
        p2 = self.conf.ftpNET.find('/', p1+2)
        self.org = self.conf.ftpNET[p1 + 2:p2]
        self.path = self.conf.ftpNET[p2:]

    #---

    def dirFTP(self):
        data = []
        try:
            f = ftplib.FTP(self.org)
            f.login(self.conf.user, self.conf.password)
            f.cwd(self.path)
            f.dir(data.append)
            f.quit()
        except ftplib.all_errors, e:
            self.conf.Log.AddLog('\nErrore FTP nella richiesta directory: %s\n' %e, False)
            return data #   se non riesce a collegarsi con FTP, restituisce array vuoto []

        if self.conf.ftpNET.find('igeo.pt') >= 0:   #   caso ftp di RENEP
            return self.dirFtpRenep(data)   #   procedura che prende i nomi delle stazioni dal fileNetList
        else:
            return self.dirFtpStandard(data)   #   Anche per Abruzzo stessa procedura di download della campania
#-----

    def dirFtpRenep(self, data):
        dirApp = []
        fmt = '%m-%d-%y %I:%M%p'
        f = ftplib.FTP(self.org)
        f.login(self.conf.user, self.conf.password)
        i = 0
        while i < len(data):
            # if '_CLIENTES' in data[i]:
            #     data.pop(i)
            #     continue

            ls = data[i].split()
            sDT = ls[0]+' '+ls[1]
            dt = datetime.datetime.strptime(sDT, fmt)

            App_ar = []
            try:
                f.cwd(self.path+ls[3])
                f.dir(App_ar.append)
            except:
                i += 1
                continue

            trovato = False
            for row in App_ar:
                if '.log' in row:
                    fname = row.split()[3]
                    trovato = True
                    break
            if not trovato:
                self.conf.Log.AddLog('\nFTP -> NO Log: %s' %ls[3], False)
                data.pop(i)
                continue

            data[i] = '%s\t%s\t%s\t%s\n' %(fname.lower(), fname, dt.strftime("%Y%m%d%H%M%S"), self.path+ls[3])  # data[i] contiene il fullName del file e la data di creazione ricavata da fTimeDec
            i += 1

        f.quit()
        return data
        # return self.prendiUltimoLog(data)


#-----

    def dirFtpStandard(self, data):
        i = 0
        while i < len(data):
            ls = data[i].split()
            if ls[0][0] == 'd':
                data.pop(i)                 #   toglie le directory dall'elenco
            else:
                fname = ''.join(ls[8:])     #   altrimenti prende il nome
                if fname.find('log',4) < 0:     #   verifico la presenza di 'log'
                    data.pop(i)
                else:
                    data[i] = ''.join([fname.lower(), '\t', fname, '\t', self.fTimeDec(data[i]), '\t','\n'])  # data[i] contiene il fullName del file e la data di creazione ricavata da fTimeDec
                    i += 1
        return data
        # return self.prendiUltimoLog(data)



    def prendiUltimoLog(self, dirList_ar):
        if (dirList_ar == False) or (dirList_ar == None):
            return False

        if len(dirList_ar) < 1:
            return dirList_ar

        for i, nfile in enumerate(dirList_ar):
            if not '\t' in nfile:
                dirList_ar[i] = ''.join([nfile.lower(),'\t',nfile,'\t\t\n'])

        dirList_ar = list(sorted(dirList_ar))

        data = []
        fname = ''
        fOrig = ''
        dt = None
        link = ''
        for line in dirList_ar:
            arApp = line.split('\t')
            newFile = arApp[0]
            newFOrig = arApp[1]
            newDT = arApp[2]
            newLink = arApp[3].strip()

            if newFile.find('/') >= 0:  # non considera le directory nella lista
                continue

            if (not self.conf.gsac) and not((newFile.find('.log') >= 0) or (newFile.find('.txt') >= 0) or (newFile.find('.zip') >= 0)):  # solo file ".log", ".txt" e ".zip"
                continue

            if (fname == ''):   # il primo viene usato come riferimento
                fname = newFile
                fOrig = newFOrig
                dt = newDT
                link = newLink

            if newFile[:4] == fname[:4]:    # scorre la lista nel caso siano presenti piu file della stessa stazione con date diverse, prende l'ultima
                if newDT >= dt:
                    fname = newFile
                    fOrig = newFOrig
                    dt = newDT
                    link = newLink
            else:
                data.append(''.join([fname, '\t', fOrig, '\t', dt, '\t', link, '\n']))
                fname = newFile
                fOrig = newFOrig
                dt = newDT
                link = newLink
        data.append(''.join([fname, '\t', fOrig, '\t', dt, '\t', newLink, '\n']))
        return data



    #---




    def dirHTTP(self):
        if self.conf.ftpNET.find('campania') >= 0:
            return self.dirCampania()   #   procedura che prende i nomi delle stazioni dal fileNetList
        elif self.conf.ftpNET.find('abruzzo') >= 0:
            return self.dirCampania()   #   Anche per Abruzzo stessa procedura di download della campania
        else:
            try:
                response = urllib2.urlopen(self.conf.ftpNET)
                html = response.read().split('\n')  #   file index.html dove sono tutte le info della directory
            except:
                self.conf.Log.AddLog('\nErrore di connessione HTTP: directory\n', False)
                return None #   in caso di errore, restituisce array vuoto

        if self.conf.ftpNET.find('south-tyrolean') >= 0:
            return self.getHttpDirSTPOS(html)   #   altrimenti usato per la rete SudTirolo
        elif self.conf.ftpNET.find('regione.fvg.it') >= 0:
            return self.getHttpDirRegioneFVG(html)   #   altrimenti usato per la rete SudTirolo
        # elif self.conf.ftpNET.find('158.102.161.199') >= 0:
        elif self.conf.gsac:                                    #ToDo In attesa... Da riprendere...
            return self.getHttpDirGNSSPIEMONTE(html)   #   GNSSPIEMONTE
        elif self.conf.ftpNET.find('webrenag.unice.fr') >= 0:
            return self.getHttpDirRENAG(html)   #   GNSSPIEMONTE
        elif self.conf.ftpNET.find('geo.edu.al/gps/logs_AlbGNSS/') >= 0:
            return self.getHttpDirALBANIA(html)   #   GNSSPIEMONTE
        else:
            return self.getHttpDirTabStandard(html)






    def dirCampania(self):
        sDT = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        with open(self.conf.fileNetList) as file:
            data = file.readlines()
            file.close()
        for i, line in enumerate(data):
            fname = line.split('\t')[0].strip()+'.txt'
            data[i] = '%s\t%s\t%s\t%s\n' % (fname.lower(), fname, sDT, '')
            # data[i] = ''.join([fname.lower(), '\t', fname,'\t', '\t', '\n'])
        # data = [line.split('\t')[0].strip()+'.txt\t\t\n' for line in data]
        return data


#------


    def getHttpDirRegioneFVG(self, html):
        data = []
        sDT = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        for line in html:
            p1 = line.find('http://www.regione.fvg.it/rafvg/cms/RAFVG/ambiente-territorio/conoscere-ambiente-territorio/')
            p2 = line.find('.log\"', p1)
            if (p1 >= 0) and (p2>p1):
                fname = line[p1:p2+4].split('/')[-1:][0]
                path =  line[p1:p2+4]
                # data.append(''.join([fname.lower(), '\t', fname, '\t', '\t', path, '\n']))
                data.append('%s\t%s\t%s\t%s\n' %(fname.lower(), fname, sDT, path))
        return data

#---

    def getHttpDirALBANIA(self, html):
        data = []
        sDT = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        for line in html:
            p1 = line.find('href=')
            p2 = line.find('.log\"', p1)
            if (p1 >= 0) and (p2>p1):
                fname = line[p1+6:p2+4]
                path =  self.conf.ftpNET+fname
                data.append('%s\t%s\t%s\t%s\n' %(fname.lower(), fname, sDT, path))

        return data


#------
    def getHttpDirSTPOS(self, html):    #   per la rete south-tyrolean.net
        html = [line.split('<br>') for line in html][2][2:-1]
        data = []
        #       ' 12/7/2016  4:57 PM        15440 <A HREF="/geodetico/Stazioni%20permanenti/log%20Sites/brbz_20141203.txt">brbz_20141203.txt</A>'
        for line in html:
            p1 = line.find('<A HREF=') + 9
            p2 = line.find('\">', p1)
            if p1 >= 0:
                fname = line[p1:p2].split('/')[-1:][0]

                sDT = ' '.join(line[:p1].split()[:3])
                try:
                    dt = time.strptime(sDT, '%m/%d/%Y %I:%M %p')
                except:
                    self.conf.Log.AddLog('\nErrore data nella DATA: %s <-> "m/d/Y I:M p"\n' %sDT, False)
                    return False
                data.append(''.join([fname.lower(), '\t', fname, '\t', time.strftime("%Y%m%d%H%M%S", dt), '\t', '\n']))
        return data

#---
    #
    # ATTENZIONE: si considera standard la pagina HTML nel seguente formato:
    #
    #     Index of /Dati/Logsheets
    # [ICO]	Name	Last modified	Size	Description
    # [DIR]	Parent Directory	 	-
    # [ ]	afal_20080618.log	17-Jul-2013 13:18 	14K
    # [ ]	afal_20150605.log	03-Mar-2016 15:37 	13K
    # [ ]	asia_20080409.log	17-Jul-2013 13:19 	12K
    #
    #
    # fino ad ora trovata in RGP e Veneto
    #

    def getHttpDirTabStandard(self, html):  #   per la rete VENETO, NIGNET, RAP
        for i, line in enumerate(html):
            if line[:6] == '<table':   # cerco inizio tabella
                break

        f = len(html) - 1
        while html[f][:7] <> '<tr><td': # cerco fine tabella
            f -= 1

        html = list(sorted(html[i:f+1]))   #   ritaglio la tabella

        data = []
        fname = ''
        dt = None
        tipo = 0
        pos = 0
        for line in html:
            p1 = line.find('href=')
            p2 = line.find('\">', p1)

            if any([p1<0, p2<0]) == True:   #   se uno qualunque minore di zero
                continue
            newFile = line[p1 + 6:p2]

            newDT, tipo, pos = self.cercaData(line, p2, tipo, pos)
            if not newDT:
                continue


            if (not any(['.txt', '.log', '.zip']) or '/') in newFile:
                continue



            if (fname == ''):   # il primo viene usato come riferimento
                fname = newFile
                dt = newDT

            if newFile[:4] == fname[:4]:    # scorre la lista nel caso siano presenti piu file della stessa stazione con date diverse, prende l'ultima
                if newDT >= dt:
                    fname = newFile
                    dt = newDT
            else:
                data.append('%s\t%s\t%s\t%s\n' % (fname.lower(), fname, time.strftime("%Y%m%d%H%M%S", dt), ''))
                fname = newFile
                dt = newDT
        data.append('%s\t%s\t%s\t%s\n' % (fname.lower(), fname, time.strftime("%Y%m%d%H%M%S", dt), ''))
        return data

#---
    def cercaData(self, line, p2, tipo, pos):
#formato 1: "abuz_20100708.log	31-Aug-2015 15:35	12K	 "
#<tr><td valign="top"><img src="/icons/unknown.gif" alt="[   ]"></td><td><a href="abuz_20100708.log">abuz_20100708.log</a></td>                 <td align="right">31-Aug-2015 15:35  </td><td align="right"> 12K</td><td>&nbsp;</td></tr>

#formato 2: "alsn_20161229.log	12.4 K	04/01/2017 10:44:34	63"
#<tr><td>                                                                <a href="alsn_20161229.log"><img src="/~img42" /> alsn_20161229.log</a><td align=right>12.4 K<td align=right>04/01/2017 10:44:34<td align=right>63
        newDT = None
        col = 0
        p3 = line.find('<td', p2)
        while p3 > 0:
            p3 = line.find('>', p3) + 1
            p4 = line.find('<', p3)
            sDT = line[p3:p4].replace(' ','').replace('-','').replace('/','').replace(':','')
            # sDT = sDT.strip('-')
            # sDT = sDT.strip('/')
            # sDT = sDT.strip(':')
            # 31-Aug-2015 15:35  ->  31Aug20151535  tipo = 1
            # 04/01/2017 10:44:34 -> 04012017104434 tipo = 2

            if tipo == 0:
                try:
                    newDT = time.strptime(sDT, '%d%b%Y%H%M')
                    tipo = 1
                    # return newDT, tipo, col
                    break
                except:
                    try:
                        newDT = time.strptime(sDT, '%d%m%Y%H%M%S')
                        tipo = 2
                        # return newDT, tipo, col
                        break
                    except:
                        # p3 = line.find('<td', p4)
                        # col += 1
                        pass
                # p3 = line.find('<td', p4)
                # col += 1
            elif tipo == 1:
                if col == pos:
                    newDT = time.strptime(sDT, '%d%b%Y%H%M')
                    break
            elif tipo == 2:
                if col == pos:
                    newDT = time.strptime(sDT, '%d%m%Y%H%M%S')
                    break
            p3 = line.find('<td', p4)
            col += 1

        return newDT, tipo, col

            # self.conf.Log.AddLog('\nErrore data nella data: %s <-> "d/m/Y I:M p"' % sDT, False)
                # return False



#-------------------------
    def getHttpDirGNSSPIEMONTE(self, html):  #   per la rete PIEMONTE
        for i, line in enumerate(html):
            if line[:6] == '<table':   # cerco inizio tabella
                break

        f = len(html) - 1
        while html[f][:7] <> '<tr><td': # cerco fine tabella
            f -= 1

        html = list(sorted(html[i+2:f+1]))   #   ritaglio la tabella

        data = []
        fname = ''
        dt = None
        for line in html:
            p1 = line.find('href=')
            p2 = line.find('\">', p1)
            p3 = line.find('right>', p2 + 6)
            p3 = line.find('right>', p3 + 6)
            p4 = line.find('<td', p3)
            if any([p1<0, p2<0, p3<0, p4<0]) == True:   #   se uno qualunque minore di zero
                continue

            newFile = line[p1+6:p2]
            sDT = line[p3+6:p4].strip()
            try:
                newDT = time.strptime(sDT,'%d/%m/%Y %H:%M:%S')
            except:
                self.conf.Log.AddLog('\nErrore data nella data: %s <-> "d/m/Y I:M p"' % sDT, False)
                return False

            if newFile.find('/') >= 0:  # non considera le directory nella lista
                continue

            if (fname == ''):   # il primo viene esato come riferimento
                fname = newFile
                dt = newDT

            if newFile[:4] == fname[:4]:    # scorre la lista nel caso siano presenti piu file della stessa stazione con date diverse, prende l'ultima
                if newDT >= dt:
                    fname = newFile
                    dt = newDT
            else:
                data.append('%s\t%s\t%s\t%s\n'%(fname.lower(), fname, time.strftime("%Y%m%d%H%M%S", dt), ''))
                fname = newFile
                dt = newDT
        data.append('%s\t%s\t%s\t%s\n' % (fname.lower(), fname, time.strftime("%Y%m%d%H%M%S", dt), ''))
        return data


#---

    def getHttpDirRENAG(self, html):  #   per la rete PIEMONTE
        cnt = 0
        for i, line in enumerate(html):
            if ('<table' in line) :   # cerco inizio tabella
                cnt += 1
                if cnt == 2:
                    break
        f = i
        while not ('</table>' in html[f]): # cerco fine tabella
            f += 1

        html = list(sorted(html[i:f]))   #   ritaglio la tabella

        data = []

        fname = ''
        dt = None
        for line in html:
            p1 = line.find('sites/SITES/')
            p2 = line.find('.html\">', p1)
            if any([p1<0, p2<0]) == True:   #   se uno qualunque minore di zero
                continue
            fname = line[p1+12:p2]
            link = self.conf.ftpNET+fname+'/current_log'

            try:
                response = urllib2.urlopen(self.conf.ftpNET+fname)
                html = response.read().split('\n')  # file index.html dove sono tutte le info della directory
            except:
                self.conf.Log.AddLog('\nErrore di connessione HTTP: directory\n', False)
                return None  # in caso di errore, restituisce array vuoto

            for row in reversed(html):
                if 'current_log' in row:
                    p1 = row.find('</a>')
                    sDT = ' '.join(row[p1+4:].split()[:2])
                    break

            try:
                dt = time.strptime(sDT, '%d-%b-%Y %H:%M')    #   05-Jan-2015 17:41
            except:
                self.conf.Log.AddLog('\nErrore data nella data: %s <-> "d-b-Y H:M"' % sDT, False)
                return False
            fname = fname+'.log'
            data.append('%s\t%s\t%s\t%s\n' % (fname.lower(), fname, time.strftime("%Y%m%d%H%M%S", dt), link))

        return data





    #---



#   ATTENZIONE, necessaria mappatura dei nomi file (maiuscolo / minuscolo): [minuscolo, originale, DateTime, Link]

    def dirLink(self):
        self.conf.Log.AddLog('\nRichiesta directory al link: %s\n'%(self.conf.ftpNET), False)

        if self.conf.gsac:
            return self.ListaRENAG()  # rete RENAG: escludo stazioni in comune con la rete RGP
        elif self.conf.ftpNET.find('ftp://') >= 0:
            return self.prendiUltimoLog(self.dirFTP())
        elif self.conf.ftpNET.find('http://') >= 0:
            return self.prendiUltimoLog(self.dirHTTP())



#----

    def fTimeDec(self, line):
        ls = line.split()
        # access, x, y, z, size, ls_month, ls_day, ls_union, ls_filename = ls
        access, x, y, z, size, ls_month, ls_day, ls_union = ls[0:8]
        tm_mon = self.monthdict[ls_month]
        tm_mday = int(ls_day)

        if len(ls_union) in (4, 5):
            if len(ls_union) == 5:
                if ls_union[2] == ':':
                    tm_hour, tm_min = int(ls_union[0:2]), int(ls_union[3:5])
                    tm_year = self.thisyear
                    if tm_mon > self.thismonth:
                        tm_year -= 1
            elif len(ls_union) == 4:
                tm_year = int(ls_union)
                tm_hour, tm_min = 0, 0
        dt = datetime.datetime(tm_year,tm_mon,tm_mday,tm_hour,tm_min,0,0)
        return dt.strftime("%Y%m%d%H%M%S")


#----

    def fDownloadFTP(self, fList, fPath):
        try:
            f = ftplib.FTP(self.org)
            f.login(self.conf.user,self.conf.password)
            f.cwd(self.path)    #   impone il percoso, lo modifica nel caso di link ad altro file
            for i, f_name in enumerate(fList):
                try:
                    arApp = f_name.split('\t')
                    fn = arApp[1]
                    if arApp[3] != '':
                        f.cwd(arApp[3].strip())
                    f.retrbinary("RETR " + fn, open(fPath+'/'+fn, 'wb').write)
                except ftplib.all_errors, e:
                    self.conf.Log.AddLog('\nErrore di connessione FTP: download -> retrieve\n%s'%e, False)
            f.quit()
        except ftplib.all_errors, e:
            self.conf.Log.AddLog('\nErrore di connessione FTP: download -> login', False)
            return False         #   nel caso di errore, esce dalla funzione e restituisce Falso
        return True



    def fDownloadHTTP(self, fList, fPath):
        for i, fname in enumerate(fList):
            fn = fname.split('\t')
            if fn[3] == '\n':
                link = self.conf.ftpNET + fn[1]
            else:
                link = fn[3].strip()

            if link[-4:] != '.zip':
                try:
                    response = urllib2.urlopen(link)
                    html = response.read()  # file index.html dove sono tutte le info della directory
                    with open(fPath+'/'+ fn[1], 'wb') as file:
                        file.writelines(html)
                        file.close()
                    # self.Log.AddLog('\n%3d\t%s\t%s' %(i+1, fn[1], fname.split('\t')[2]), False)
                except:
                    self.conf.Log.AddLog('\nErrore di download HTTP: %s'%(link), False)
                    # return False  # in caso di errore, restituisce array vuoto,

            if link[-4:] == '.zip':
                try:
                    r = requests.get(link, stream=True)
                    z = zipfile.ZipFile(StringIO.StringIO(r.content))
                    # z.extractall(fPath+'/'+ fn[1])
                    z.extractall(fPath)
                except:
                    self.conf.Log.AddLog('\nErrore di download HTTP: %s'%(link), False)
                    # return False  # in caso di errore, restituisce array vuoto,

        return True





    def fDownload(self, fList, fPath):
        self.conf.Log.AddLog('\nDownload di %d Log file:' %len(fList), False)
        status = []
        if self.conf.gsac:
            status = self.DownloadGSAC(fList, fPath)
        elif self.conf.ftpNET.find('ftp://') >= 0:
            status = self.fDownloadFTP(fList,fPath)
        elif self.conf.ftpNET.find('http://') >= 0:
            status = self.fDownloadHTTP(fList, fPath)

        return status

    # -------------------------------


    def ListaRENAG(self): # estrai solo stazioni RENAG senza RGP
        stListRENAG = []
        cmd = subprocess.Popen('/opt/gsacclient/gsacclient.sh -server %s -site.group %s' % (self.conf.ftpNET, 'renag'), shell=True,
            stdout=subprocess.PIPE)
        for line in cmd.stdout:
            if '#' in line:
                continue
            stListRENAG.append(line.split(',')[0])

        stListRGP = []
        cmd = subprocess.Popen('/opt/gsacclient/gsacclient.sh -server %s -site.group %s' % (self.conf.ftpNET, 'rgp'),
                               shell=True, stdout=subprocess.PIPE)
        for line in cmd.stdout:
            if '#' in line:
                continue
            stListRGP.append(line.split(',')[0])

        stListRENAG, stListRGP, stCommon = self.conf.FiltroArray(stListRENAG, stListRGP, 'id')  # toglie i file comuni, su dirAppCompleto restano i file in piu'

        # return stListRENAG
        return self.prendiUltimoLog(stListRENAG)



#------------------------


    def DownloadGSAC(self, stList, fPath):
        self.conf.Log.AddLog('\n\nDownload dal server GSAC: %s'%self.conf.ftpNET, False)

        stfFile = []
        # siteQuery = 'curl "%s/gsacapi/site/search?site.code=%s%s"' %(self.conf.ftpNET,'&site.code='.join(stList),'&output=site.station.info')
        siteQuery = 'curl "%s/gsacapi/site/search?site.code=%s%s"' %(self.conf.ftpNET,'&site.code='.join([line.split('\t')[0] for line in stList]),'&output=site.station.info')
        cmd = subprocess.Popen(siteQuery,shell=True, stdout=subprocess.PIPE)
        for line in cmd.stdout:
            if '*' in line[0]:
                continue
            stfFile.append(line)


        for i, line in enumerate(stfFile):
            stfFile[i] = line[:71]+line.replace('-----', 'DHARP')[71:81]+line[81:]

        for i, line in enumerate(stfFile):
            if not '*' in line:         # trovo il numero di righe del header
                break

        header = '*SITE  Station Name      Session Start      Session Stop       Ant Ht   HtCod  Ant N    Ant E    Receiver Type         Vers                  SwVer  Receiver SN           Antenna Type     Dome   Antenna SN\n'
        cntNotFound = 0
        notFoundList = []
        stfCreati = 0
        while i < len(stfFile):
            stfArch = []
            stfProc = []
            stfArch.append(header)
            stfProc.append(header)

            stIDproc = ''
            stID = stfFile[i].split()[0].upper()
            for line in stList:  # cerco nome per processamento dalla 3^col
                if stID == line.split('\t')[0].upper():
                    stIDproc = line.split('\t')[2].upper()
                    break

            if stIDproc == '':
                stIDproc = stID  # stID non trovato, stazione nuova?
                cntNotFound += 1
                notFoundList.append(stID)

            while i < len(stfFile):
                if stfFile[i].split()[0] == stID:
                    stfArch.append(stfFile[i])
                    stfProc.append(' %s%s'%(stIDproc,stfFile[i][5:]))
                    i += 1
                else:
                    break
            stfArch[-1] = stfArch[-1][:44] + '9999 999  0  0  0' + stfFile[-1][61:]
            stfProc[-1] = stfProc[-1][:44] + '9999 999  0  0  0' + stfFile[-1][61:]

            self.conf.salvaStatioInfo(stID+'.stf', stfArch, stIDproc+'.stf', stfProc)
            stfCreati += 1

        arApp = os.listdir(self.conf.DIR_stf)
        self.conf.Log.AddLog('\n\nFile .stf CREATI:\t%3d'
                        '\nFile Log non trovati:\t%3d'
                        '\nErrore elaboraz.:\t%3d'
                        '\n'
                        '\nSTF files:\t%3d\tfiles in %s' % (stfCreati, cntNotFound, 0, len(arApp), self.conf.DIR_stf), False)

        if cntNotFound > 0:
            self.sendMail = True
            self.conf.Log.AddLog('\n\nI seguenti %d station_ID del server GSAC non sono stati trovati sulla NetList:' % len(notFoundList), False)
            for i, nFile in enumerate(notFoundList):
                self.conf.Log.AddLog('\n%3d\t%s' % (i + 1, nFile), False)




            #-------------------------------









#-----------------------------------
class TimerEventi:

    def __init__(self,Timer_ar, WeekDay):
        self.T_ar = Timer_ar.split()
        self.sWD_ar = WeekDay.lower().split()
        self.WD_ar = []
        self.evTime = []
        self.dataRif = ''
        self.primoRun = False   #   True
        self.Inizializza()

    def Inizializza(self):
        self.evTime = [False] * len(self.T_ar)

        W_ar = {'mon':0, 'tue':1, 'wed':2, 'thu':3, 'fri':4, 'sat':5, 'sun':6}
        for day in self.sWD_ar:
            if day[:3] in W_ar.keys():
                self.WD_ar.append(W_ar[day[:3]])

        self.dataRif = str(date.today())


    def CheckTime(self):
        Evento = False
        if str(date.today()) <> self.dataRif:
            self.Inizializza()
        else:
            for i, time in enumerate(self.T_ar):
                if self.primoRun or ((date.today().weekday() in self.WD_ar) and (not self.evTime[i])):
                    self.primoRun = False

                    sDT = self.dataRif + ' ' + self.T_ar[i]
                    try:
                        DT = datetime.datetime.strptime(sDT, "%Y-%m-%d %H:%M")
                    except:
                        print('\nErrore orario nel file config: %s <-> "hh:mm"\n' % self.T_ar[i])
                        sys.exit(1)

                    nDT = datetime.datetime.now()
                    if nDT > DT:
                        self.evTime[i] = True
                        Evento = True
                        break
        return Evento



#-------------------------------




#----------------------------------------------------------------------




class CGPSconfigurazioni():
    def __init__(self):
        self.NETar = []
        self.NETar_test = []
        self.par = ['CartellaDatiNETs',
                    'CartellaNetList',
                    'CartellaRcvAntTab',
                    'CartellaStfProc',
                    'CartellaCopiaSTF',
                    'MailAttiva',
                    'WeekDay',
                    'Time_Array',
                    'Destinatari',
                    'minLon',
                    'maxLon',
                    'minLat',
                    'maxLat']

        self.par_ar = []
        self.initCGPS()

        self.fRcvAntDat = '%s/%s'%(self.par_ar[2], 'rcvant.dat')
        self.fAntModDat = '%s/%s'%(self.par_ar[2], 'antmod.dat')
        self.fRcvrAntTab = '%s/%s'%(self.par_ar[2], 'rcvr_ant.tab')

        self.RcvrAntTab_ar = []  # Array 2D: con tutti i codici di [[Rcv e Ant],[Duo]]    -> cerco [(R) e (A)] e [(D)]
        self.RcvAntDat_ar = []  # Array 3D: [[Rcv],[Ant],[Duo]]                         -> cerco (R) e (A)
        self.AntModDat_ar = []  # Array 1D: con tutte le calibrazioni                   -> cerco coppie (A)_(D)

        self.getCheckTabs()


    def initCGPS(self):
        CGPS_ar = []
        file = open('CGPSmetadata.cfg')
        for line in file:
            CGPS_ar.append(line)
        file.close()

        for i, line in enumerate(CGPS_ar):
            if '[NETar]' in line:
                break
        for f, line in enumerate(CGPS_ar):
            if '[NETar_END]' in line:
                break
        for line in CGPS_ar[i+1:f-1]:
            s = line.find('#')
            if s < 0:
                s = len(line)
            line = line[:s].strip()
            if line != '':
                if line.find('?') > 0:  #   reti sotto test, da registrare in cartelle diverse
                    line = line.strip('?').strip()
                    self.NETar_test.append(line)
                self.NETar.append(line)

        self.par_ar = self.getPar(CGPS_ar,self.par)

        if self.par_ar[5].lower() == 'true':
            self.par_ar[5] = True
        else:
            self.par_ar[5] = False

        try:
            for r, row in enumerate(self.par_ar[10:14]):
                self.par_ar[r+10] = float(row.strip())
        except:
            print ('Errore di conversione LonLat nel file CGPSconf')




    def getPar(self, ConfAr, par_ar):
        par_val = [None] * len(par_ar)

        for p, par in enumerate(par_ar):
            trovato = False

            for l, log in enumerate(ConfAr):
                log = log[:log.find('#')]

                if ('%s ='%par.lower()) in log.lower():
                    trovato = True

                    log = log[log.find('=') + 1:].strip()

                    log = log.replace('\'','')
                    log = log.replace(',','.')
                    par_val[p] = log
                    break
            if not trovato:
                par_val[p] = None
                print('\nNon trovato CGPSconfig: %s'%par_ar[p])
                exit(3)
        return par_val




#-------

    def getCheckTabs(self):
# carica i dati dal file "rcvant.dat"
        if os.path.isfile(self.fRcvAntDat):  # se esiste,
            with open(self.fRcvAntDat) as file:
                arApp = file.readlines()
                file.close()
            self.RcvAntDat_ar.append(self.getRcvAntDat(arApp, '#RECCOD', 15, 20))
            self.RcvAntDat_ar.append(self.getRcvAntDat(arApp, '#ANTCOD', 15, 15))
            # self.RcvAntDat_ar.append(self.getDuomoTab(arApp)) #   LISTA DUOMO NON COMPLETA, VEDI  RcvrAntTab_ar[1]
        else:
           print('Non esiste file Check Table:\n%s\n' % self.fRcvAntDat)

# carica i dati dal file "rcvr_ant.tab"
        if os.path.isfile(self.fRcvrAntTab):  # se esiste,
            with open(self.fRcvrAntTab) as file:
                arApp = file.readlines()
                file.close()
            self.RcvrAntTab_ar.append(self.getRcvAntTab(arApp))   #   selezione delle righe, in cui cercare Receiver and Antenna
            self.RcvrAntTab_ar.append(self.getDuomoTab(arApp))
        else:
           print('Non esiste file Check Table:\n%s\n' % self.fRcvrAntTab)

# carica i dati dal file "antmod.dat"
        if os.path.isfile(self.fAntModDat):  # se esiste,
            with open(self.fAntModDat) as file:
                arApp = file.readlines()
                file.close()
            self.AntModDat_ar = self.getAntModDat(arApp)   #   selezione grossolana delle righe, in cui cercare R,A,D.
        else:
           print('Non esiste file Check Table:\n%s\n' % self.elab.cfg.fAntModDat)









#---

    def getAntModDat(self, arApp):
        tab_ar = []
        for r, row in enumerate(arApp):
            if (row[0] != ' ') and (row[0] != '#') and (row[15] == ' ') and ((row[16:20]).isalnum()) and (row[21] == ' '):
                tab_ar.append(row[:20])
        return list(sorted(tab_ar))


#---

    def getRcvAntTab(self, arApp):
        for r, row in enumerate(arApp):
            if row[0] == '\n':       #   cerco riferimento di start, solo 1' char
                break

        for s, row in enumerate(arApp):
            if row == '| Antenna Domes        |                                                       |\n':
                break

        tab_ar = []
        for r, row in enumerate(arApp[r:s]):
            if (row[0] == '|') and (row[2:5] != '---') and (row[25:30] != '     ') and (row[2:22] != '                    ')  and (row[2:17] != 'xxxxxxxxxxxxxxx'):
                sApp = row[2:22].strip()
                tab_ar.append(sApp)
        return list(sorted(tab_ar))



#---
    def getRcvAntDat(self, arApp, sRif, start, delta):

        for r, line in enumerate(arApp):
            if line[:len(sRif)] == sRif:    # cerca il riferimento di partenza
                break

        arApp = arApp[r:]
        checkTab_ar = []
        sRif = ' END'   # Riferimento di fine paragrafo
        stop = start + delta
        for r, line in enumerate(arApp):
            if line[:len(sRif)] != sRif:
                line = line[:stop]
                if (line[start:stop].strip() != '') and (line[0] != '#') and (line[7:13] == '      '):
                    checkTab_ar.append(line[start:stop].strip())
            else:
                break
        return list(sorted(checkTab_ar))
#---

    def getDuomoTab(self, arApp):
        for r, row in enumerate(arApp):
            if row == '| Antenna Domes        |                                                       |\n':
                break

        for s, row in enumerate(arApp):
            if row == '| Abbreviations        |                      Description                      |\n':
                break

        checkTab_ar = []
        sRif = '| xxxxxxxxxxxxxxx '
        for r, line in enumerate(arApp[r:s]):
            if line[:len(sRif)] == sRif:
                checkTab_ar.append(line[18:22])
            else:
                continue
        return list(sorted(checkTab_ar))










#----------------------------------------------------------------------



class ControlloProcessi:
    def __init__(self, Avvio):
        self.avvio = Avvio

        pass

    def run(self):
        pass

    def stop(self):
        pass

    def LeggiPidFiles(self):
        pass

    def getProcesStatus(self):
        pass

    def confrontaPID(self):
        pass