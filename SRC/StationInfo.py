#!/usr/bin/python
from ScanLog import *




class StationInfo:
    def __init__(self, config, elabNET, ftpConn, LogScan, tTab):
        self.conf = config
        self.elab = elabNET
        self.ftpConn = ftpConn
        self.LogScan = LogScan
        self.tTab = tTab
        self.StfDir_ar = []


#----

    # def creaStationInfo(self, Log_ob, DestDir, archSTF):
    def creaStationInfo(self, Log_ob):

        stf = stf_ob()
        stfProc = stf_ob()  # file creato con nome e ID rinominati secondo la 3^ colonna del file .list

        dtInf = datetime.datetime.strptime('9999-1-1T00:00Z', '%Y-%m-%dT%H:%MZ')
        sApp = '*SITE  Station Name      Session Start      Session Stop       Ant Ht   HtCod  Ant N    Ant E    Receiver Type         Vers                  SwVer  Receiver SN           Antenna Type     Dome   Antenna SN\n'
        stf.Rows_ar.append(sApp)
        stfProc.Rows_ar.append(sApp)


        s = Log_ob.p1_val[1]
        stf.col_ar[0] = ''.join(i for i in s if ord(i) < 128)    # SITE ID - tolgo caratteri non ASCII

        s = Log_ob.p1_val[0]
        stf.col_ar[1] = ''.join(i for i in s if ord(i) < 128)    # Station Name - tolgo caratteri non ASCII

        stf.col_ar[5] = 'DHARP'  # HtCod

        fn3col = Log_ob.stfTabName.upper()[:4]
        if fn3col == '':
            self.elab.cfg.Log.AddLog('\nAttenzzione ID vuoto nella 3^ col del file.list', False)
            return False

        # DEBUG
        # if fn3col == 'FRNS':
        #     pass


        i3 = 0
        i4 = 0
        PeriodiAllineati = False

        dti3_old = dti4_old = 0

        while True:
            startP3, dti3 = self.convDT2Jul(Log_ob.p3_ar[i3][5])
            if len(Log_ob.p3_ar) > i3+1:
                stopP3, dtf3 = self.convDT2Jul(Log_ob.p3_ar[i3+1][5])   # lo STOP deve coincidere con l'inizio del successivo
                if dtf3 < dti3:
                    self.elab.cfg.Log.AddLog('\nAttenzione: par.3 sub.%s la data di fine precede l\'inizio'%i3, False)
                    return False
            else:
                stopP3, dtf3 = '9999 999  0  0  0', dtInf

            startP4, dti4 = self.convDT2Jul(Log_ob.p4_ar[i4][10])
            if len(Log_ob.p4_ar) > i4+1:
                stopP4, dtf4 = self.convDT2Jul(Log_ob.p4_ar[i4+1][10])  # lo STOP deve coincidere con l'inizio del successivo
                if dtf4 < dti4:
                    self.elab.cfg.Log.AddLog('\nAttenzione: par.4 sub.%s la data di fine precede l\'inizio'%i4, False)
                    return False

            else:
                stopP4, dtf4 = '9999 999  0  0  0', dtInf

            if (startP3 == '') or (startP4=='') or (stopP3 == '') or (stopP4=='') :
                return False    #   caso di formato sbagliato della data




            if not PeriodiAllineati:     #   la stazione inizia ad acquisire quando completa di Antenna e Ricevitore, altrimenti vengono scartati i periodi della stazione non completa
                if dti3 == dti4:
                    PeriodiAllineati = True
                elif dti3 < dti4:
                    if dtf3 < dti4:
                        i3 += 1
                        self.elab.cfg.Log.AddLog('\nPeriodi non allineati nel Log file par.3 (Rcvr),\n\tscarto: %s - %s' % (startP3, stopP3), False)
                        # self.elab.Update = True
                        continue
                    else:
                        dti3 = dti4
                        startP3 = startP4
                        PeriodiAllineati = True
                elif dti4 < dti3:
                    if dtf4 < dti3:
                        i4 += 1
                        self.elab.cfg.Log.AddLog('\nPeriodi non allineati nel Log file par.4 (Ant),\n\t scarto: %s - %s' % (startP4, stopP4), False)
                        # self.elab.Update = True
                        continue
                    else:
                        dti4 = dti3
                        startP4 = startP3
                        PeriodiAllineati = True



            iPeriodo = max(dti3,dti4)
            fPeriodo = min(dtf3,dtf4)
        # usare solo Start Time per ordinare i periodi, lo stop viene posto uguale
            if iPeriodo == dti3:
                stf.col_ar[2] = startP3 # Session Start
            else:
                stf.col_ar[2] = startP4 # Session Start

            if fPeriodo == dtf3:
                stf.col_ar[3] = stopP3  # Session Stop
            else:
                stf.col_ar[3] = stopP4  # Session Stop




            #   ANTENNA
            stf.col_ar[4] = Log_ob.p4_ar[i4][3] #   Marker->ARP Up Ecc. (m) <-> Ant Ht
            stf.col_ar[6] = Log_ob.p4_ar[i4][4] #   Marker->ARP North Ecc(m)
            stf.col_ar[7] = Log_ob.p4_ar[i4][5] #   Marker->ARP East Ecc(m)

            #   RECEIVER
            stf.col_ar[8] = Log_ob.p3_ar[i3][0] #   Receiver Type
            (stf.col_ar[9],  stf.col_ar[10]) = self.RetrieveSwVer(Log_ob.p3_ar[i3][3]) #   Firmware Version

            stf.col_ar[11] = Log_ob.p3_ar[i3][2] #   Receiver SN

            stf.col_ar[12] = Log_ob.p4_ar[i4][0]    # Antenna Type + Duomo, SELEZIONO solo Antenna Type
            stf.col_ar[13] = Log_ob.p4_ar[i4][0]    # Antenna Type + Duomo, SELEZIONO solo Duomo

            stf.col_ar[14] = Log_ob.p4_ar[i4][1]    #   Antenna SN


            if not self.tTab.verifStfRow(stf):
                return False

            sApp, err = self.formattaRiga(stf)
            stf.Rows_ar.append(sApp)
            if err:
                self.elab.cfg.Log.AddLog('\nWarning per il file stf: %s -> %s' % (Log_ob.p1_val[0], Log_ob.p1_val[1]), False)




            stfProc.Rows_ar.append(''.join([' ', fn3col, sApp[5:]]))     #   sostituisco ID col nome 3^ colonna del file.list

            if dtf3 < dtf4:
                i3 += 1
            elif dtf3 > dtf4:
                i4 += 1
            else:
                i3 += 1
                i4 += 1


            if (dtf3 == dtInf) and (dtf4 == dtInf):
                break

            if i3 >= len(Log_ob.p3_ar) or i4 >= len(Log_ob.p4_ar):
                break


        fname = Log_ob.p1_val[1].lower()[:4] + '.stf'
        fname_proc = Log_ob.stfTabName.lower()[:4] + '.stf'
        self.conf.salvaStatioInfo(fname, stf.Rows_ar, fname_proc, stfProc.Rows_ar)      # salva StationInfo nelle directory previste


        return True
#----------------






    def RetrieveSwVer(self, Vers):
        SwVer = 0.00
        if Vers.find('/') > 0:
            Ver = Vers.split('/')[0]
        else:
            Ver = Vers

        vApp = Ver.replace('.','')  #unico simbolo ammesso nella versione sw
        if vApp.isdigit():
            try:
                SwVer = float(Ver)
                if SwVer > 100:
                    SwVer = 0.0
            except:
                pass

        return (Vers, SwVer)


#----
    def convDT2Jul(self,sDT):
        # fmt = '%Y-%m-%dT%H:%MZ'   #   vincoli troppo stretto
        fmt = '%Y%m%d%H%M'  #   per allentare i vincoli, non verifico la "Z" alla fine
        sApp = sDT

        # DEBUG
        if not sDT:
            return


        sDT = sDT.upper()
        sDT = sDT.replace('(','')   #   elimino le eventuali parentesi
        sDT = sDT.replace(')','')
        sDT = sDT.replace('T','')
        sDT = sDT.replace('Z','')
        sDT = sDT.replace('U','')
        sDT = sDT.replace('-','')
        sDT = sDT.replace(':','')
        sDT = sDT.replace(' ','')

        if sDT == None:
            return '????'

        if (len(sDT) == 8) or (len(sDT) == 9):
            sDT = sDT + '0000'  #   se non incluso, aggiungi orario
        try:
            dt = datetime.datetime.strptime(sDT, fmt)
            tt = dt.timetuple()
        except:
            try:
                dt = datetime.datetime.strptime(sDT, '%d%b%Y%H%M')
                tt = dt.timetuple()
            except:
                self.elab.cfg.Log.AddLog('\nErrore nella data: "%s" <-> "yyyy-mm-ddTHH:MM"' % (sApp), False)
                return '', datetime.datetime.strptime('999901010000', fmt)

        return ' '.join([str(tt.tm_year).rjust(4),str(tt.tm_yday).rjust(3),str(tt.tm_hour).rjust(2),str(tt.tm_min).rjust(2),' 0']), dt




#----

    def formattaRiga(self, stf):
        err = False
        try:
            AntHt = float(stf.col_ar[4])
        except:
            AntHt = 0.00
            if not ((stf.col_ar[4] == '') or (stf.col_ar[4] == '(F8.4)')):
                self.elab.cfg.Log.AddLog('\nconversione AntHt= "%s" -> 0.00' % (stf.col_ar[4]), False)
                err = True

        try:
            AntN = float(stf.col_ar[6])
        except:
            AntN = 0.00
            if not ((stf.col_ar[6] == '') or (stf.col_ar[6] == '(F8.4)')):
                self.elab.cfg.Log.AddLog('\nconversione AntN= "%s" -> 0.00' % (stf.col_ar[6]), False)
                err = True

        try:
            AntE = float(stf.col_ar[7])
        except:
            AntE = 0.00
            if not ((stf.col_ar[7] == '') or (stf.col_ar[7] == '(F8.4)')):
                self.elab.cfg.Log.AddLog('\nconversione AntE= "%s" -> 0.00' % (stf.col_ar[7]), False)
                err = True



        # COME DA FORTRAN:
        # x = spazi
        # a = caratteri ascii
        # i = numeri decimali
        # f = numeri float
        # (1x, 4a, 2x, 16a, 2x, i4, 1x, i3, 1x, i2, 1x, i2, 1x, i2, 2x, i4, 1x, i3, 1x, i2, 1x, i2, 1x, i2 , f9.4, 2x, 5a, f9.4, f9.4, 2x, a20, 2x, a20, 2x, f5.2, 2x, a20, 2x, a15, 2x, a4, 3x, a20)

        # self.fieldFormat = '%-4s  %-16s  %17s  %17s%9.4f  %-5s%9.4f%9.4f  %-20s  %-20s  %5.2f  %-20s  %-15s  %-4s   %-20s\n'
        sApp = (' %-4s  %-16s  %-17s  %-17s%9.4f  %-5s%9.4f%9.4f  %-20s  %-20s  %5.2f  %-20s  %-15s  %-4s   %-20s\n'
                %(stf.col_ar[0][:4], stf.col_ar[1][:16], stf.col_ar[2][:17], stf.col_ar[3][:17],
                                  AntHt, stf.col_ar[5][:5], AntN, AntE, stf.col_ar[8][:20],stf.col_ar[9][:20], stf.col_ar[10],
                                  stf.col_ar[11][:20], stf.col_ar[12][:15], stf.col_ar[13][:4],stf.col_ar[14][:20]))

        return sApp, err



#----

    def CheckLog(self, Log_ob):
        if (Log_ob.p1_val[1] == ''):
            self.elab.cfg.Log.AddLog('\nErrore Site Name, Log file di : %s' % (Log_ob.p1_val[1]), False)
            return False
        if (len(Log_ob.p3_ar) < 1):
            self.elab.cfg.Log.AddLog('\nErrore nel paragrafo 3 del Log file di: %s\n' % (Log_ob.p1_val[1]), False)
            return False
        if (len(Log_ob.p4_ar) < 1):
            self.elab.cfg.Log.AddLog('\nErrore nel paragrafo 4 del Log file di: %s\n' % (Log_ob.p1_val[1]), False)
            return False

        return True # se Test pass, allora True

#----






    def checkStfDir(self, language):
        if self.conf.gsac:  # CASO DI SERVER TIPO "GSAC"
            NetLApp, ftpApp, commApp = self.conf.FiltroArray(self.elab.NetList_ar, self.elab.ftpData_ar, 'id')  # restituisce i 2 array senza gli elementi comuni
            return self.ftpConn.fDownload(commApp, self.conf.DIR_stf)  # scarico solo gli stf appartenenti alla Netlist


        self.StfDir_ar = list(sorted([f for f in listdir(self.elab.cfg.DIR_stf) if isfile(join(self.elab.cfg.DIR_stf, f))]))    # lista file STF restanti, dopo aver tolto quelli da aggiornare
        Stf_App, NetL_App, arApp = self.conf.FiltroArray(self.StfDir_ar, self.elab.NetList_ar, 'id') # restituisce i 2 array senza gli elementi comuni, per creare STF solo per i nuovi log-file
        if len(NetL_App) > 0:
            self.elab.cfg.Log.AddLog('\n----------------------------------------\nFile StationInfo nella lista da elaborare: %d\n' % len(NetL_App), False)

        errList = []
        notfoundList = []
        contSTF = 0
        cntNonTrovato = 0
        cntErr = 0
        for i, line in enumerate(NetL_App):
            trovato = False
            for j, fName in enumerate(self.elab.RepoDir_ar):
                if fName[:4] == line[:4]:
                    trovato = True
                      # DEBUG
                    if 'scac' in fName.lower():
                        pass

                    #  1)  carico le righe dei Log in modo ordinato nell'oggetto, come array, per facilitare confronto e crearae stationinfo
                    Log_ob = self.LogScan.CaricaLog(self.elab.cfg.DIR_Log_Repo + '/' + self.elab.RepoDir_ar[j].split('\t')[1], language)

                    if (Log_ob == None) or (not self.CheckLog(Log_ob)):     #   verifico solo se possibile caricare il file
                        self.elab.cfg.Log.AddLog('\nErrore: non possibile creare StationInfo col file log: %s\n' %self.elab.RepoDir_ar[j].split('\t')[1], False)
                        cntErr += 1
                        continue


                    # 2) verifica e sostituisci i campi dentro Log_ob
                    try:
                        Log_ob.stfTabName = line.split('\t')[2] #carico il nome della 3^ col da usare per il processamento
                        if self.creaStationInfo(Log_ob):     #   3)  Crea StationInfo con campi corretti, senza verificare
                        # if self.creaStationInfo(Log_ob, self.elab.cfg.DIR_stf, self.elab.cfg.CartellaCopiaSTF):     #   3)  Crea StationInfo con campi corretti, senza verificare
                            contSTF += 1
                        else:
                            self.elab.cfg.Log.AddLog('\nNON possibile creare file: %s.stf\n-----------' % (fName[:4]), False)
                            cntErr += 1
                            errList.append(fName.split('\t')[1])
                    except IOError, e:
                        self.elab.cfg.Log.AddLog('\n -> Errore nel creare file %s.stf -> %s\n-----------' % (self.elab.RepoDir_ar[j][:4], e), False)
                        cntErr += 1
                        errList.append(fName.split('\t')[1])
            if not trovato:
                cntNonTrovato += 1
                notfoundList.append(line.split('\t')[0])
        arApp = listdir(self.elab.cfg.DIR_stf)
        self.elab.cfg.Log.AddLog('\n\nFile .stf CREATI:\t%3d'
                                 '\nFile Log non trovati:\t%3d'
                                 '\nErrore elaboraz.:\t%3d'
                                 '\n'
                                 '\nSTF files:\t%3d\tfiles in %s' % (contSTF, cntNonTrovato, cntErr, len(arApp), self.elab.cfg.DIR_stf), False)
        if len(errList) > 0:
            self.elab.sendMail = True   #   decide se mandare la mail di report
            self.elab.cfg.Log.AddLog('\n\nErrore nel creare %d file stf, segue la lista' %len(errList), False)
            for i, nFile in enumerate(errList):
                self.elab.cfg.Log.AddLog('\n%3d\t%s'%(i+1, nFile), False)

        if len(notfoundList) > 0:
            self.elab.sendMail = True
            self.elab.cfg.Log.AddLog('\n\nI seguenti %d Log-File della NetList non sono stati trovati:' %len(notfoundList), False)
            for i, nFile in enumerate(notfoundList):
                self.elab.cfg.Log.AddLog('\n%3d\t%s'%(i+1, nFile), False)

#----------

    def cambioParStorico(self):     #detect cambio di RCVR, ANT a DUOMO su tutto lo storico STF
        dirSTF = list(sorted([f for f in listdir(self.conf.DIR_stf) if isfile(join(self.conf.DIR_stf, f))]))  # directory originale, con caratteri upper e/o lower case

#*SITE  Station Name      Session Start      Session Stop       Ant Ht   HtCod  Ant N    Ant E    Receiver Type         Vers                  SwVer  Receiver SN           Antenna Type     Dome   Antenna SN
# ACOR  A Coruna          1998 340 10 10  0  2001 353  0  0  0   3.0420  DHARP   0.0000   0.0000  ASHTECH UZ-12         UE00-0A12              0.00  00224                 ASH700936D_M     SNOW   16122

        RAD_old = []    # RAD => RcvrAntDome
        RAD_new = []
        Report = []
        for fName in dirSTF:
            f_ar = self.conf.caricaArray('%s/%s'%(self.conf.DIR_stf, fName))

            line = f_ar[1:]
            RAD_old = [line[26:44], line[98:119], line[171:187], line[187:194]] #[Data, Rcvr, Ant, Duo]
            Report.append(', '.join(RAD_old))
            for line in f_ar[2:]:
                RAD_new = [line[26:44], line[98:119], line[171:187],line[187:194]]
                if any[RAD_new[1]!=RAD_old[1],RAD_new[2]!=RAD_old[2],RAD_new[3]!=RAD_old[3]]:
                  Report.append(', '.join(RAD_new))
                RAD_old = RAD_new


# todo continuare

#------------------------------------------



#------------------------------------------


class stf_ob:
    def __init__(self):
        self.rowNumber = 0
        # self.mstinf = ''
        self.col_name =['*SITE',                                #   0
                        'Station Name',
                        'Session Start',
                        'Session Stop',
                        'Ant Ht', 'HtCod', 'Ant N', 'Ant E',    #   4
                        'Receiver Type', 'Vers',                #   8
                        'SwVer', 'Receiver SN',                 #   10
                        'Antenna Type', 'Dome',                 #   12
                        'Antenna SN']                       #   14

        self.fieldFormat = '%-4s  %-16s  %17s  %17s%9.4f  %-5s%9.4f%9.4f  %-20s  %-20s  %5.2f  %-20s  %-15s  %-4s   %-20s\n'
        #   posizione        0    1     2     3   4       5 6    7      8     9     10     11    12    13    14
        self.col_ar = [None] * len(self.col_name)              #   include mstinf
        self.Rows_ar = []



# COME DA FORTRAN:
# x = spazi
# a = caratteri ascii
# i = numeri decimali
# f = numeri float
#(1x, 4a, 2x, 16a, 2x, i4, 1x, i3, 1x, i2, 1x, i2, 1x, i2, 2x, i4, 1x, i3, 1x, i2, 1x, i2, 1x, i2 , f9.4, 2x, 5a, f9.4, f9.4, 2x, a20, 2x, a20, 2x, f5.2, 2x, a20, 2x, a15, 2x, a4, 3x, a20)
# PALI  Domaine de la pa  2007 340 23  0  0  2008 265 22  0  0   0.0000  DHARP   0.0000   0.0000  TRIMBLE NETRS               1.1-3            0.00  46411                 TRM41249.00      NONE   60177
# ACAE  Pozzuoli-Accadem  2000  56  0  0  0  2001 188  0  0  0   0.6350  DHARP   0.0000   0.0000  TRIMBLE 4000SSI       7.29/3.07              0.00  24258                 TRM29659.00      NONE   160508
#------------------------------------------
