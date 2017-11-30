#!/usr/bin/python
# -*- coding: utf-8 -*-
# import os, sys
from ClassiComuni import *
import unicodedata
from os import listdir
from os.path import isfile, join

import time

#------------------------------------------
class LogScan:
    def __init__(self, elabora):
        self.elab = elabora
        self.FtpNewLog_list = ''
        self.OldLog_rows = []
        self.NewLog_rows = []


#---



    def cercaPar(self, Log_ar, start, sPar, limit):
        for i, line in enumerate(Log_ar[start:]):   #   cerca a partire da start
            if Log_ar[i][:limit].find(sPar) >= 0:   #   entro un "limit" di caratteri
                return i
        self.elab.cfg.Log.AddLog('\nErrore: Riferimento "%s" non trovato nel Log' %sPar, False)
        return -1   #   se errore



#---


    def getVal(self, Log_ar, par_ar):
        par_val = [None] * len(par_ar)

        for p, par in enumerate(par_ar):
            for l, log in enumerate(Log_ar):
                if par.lower() in log.lower():
                    par_val[p] = log[log.find(':')+1:].strip()
                    break
                if l == len(Log_ar):
                    par_val[p] = None

        return par_val


#---



    def CaricaLog(self, logFile, language):
        logFile = logFile.strip('\n\t')

        # Log_ar = []
        # try:
        #     file = open(logFile)
        #     for line in file:
        #         inValue = line.decode("iso-8859-15")
        #         normalizedValue = unicodedata.normalize('NFKC', inValue).encode('utf-8')
        #         Log_ar.append(normalizedValue)
        #     file.close()
        # except:
        #     pass
        # return self.CaricaLog_ar(Log_ar, language)
        return self.CaricaLog_ar(self.elab.cfg.caricaArray(logFile), language)




    def CaricaLog_ar(self, Log_ar, language):
        Log_ob = Log()  # creo oggetto

        # carico info dal paragrafo 1
        start = self.cercaPar(Log_ar, 0, Log_ob.FindRef[language][0],40)
        stop = self.cercaPar(Log_ar, start, Log_ob.FindRef[language][1], 40)
        if (start < 0) or (stop < 0):
            return None

        Log_ob.p1_val = self.getVal(Log_ar[start:stop], Log_ob.p1[language])
        if not any(Log_ob.p1_val):
            return None

        # dal paragrafo 2 prendi coordinate
        # carico info dal paragrafo 2
        start = stop
        start = self.cercaPar(Log_ar, start, Log_ob.FindRef[language][1],40)
        stop = self.cercaPar(Log_ar, start, Log_ob.FindRef[language][2], 40)
        if (start < 0) or (stop < 0):
            return None

        Log_ob.p2_val = self.getVal(Log_ar[start:stop], Log_ob.p2[language])
        if not any(Log_ob.p2_val):
            return None
        for i, val in enumerate(Log_ob.p2_val):
            val = val.replace(',','.')
            val = val.replace('(','')
            val = val.replace(')','')
            val = val.replace('m','')
            val = val.replace(' ','')
            Log_ob.p2_val[i] = float(val)


        # carico info dal paragrafo 3
        start = stop
        subRow_ar = []
        sRif = Log_ob.FindRef[language][2]
        for r, line in enumerate(Log_ar[start:]):   #   cerco in tutto il Log file
            p = line[:32].find(sRif)
            if p > 0:   #   cerco sRif fra i primi 20 char, tolgo il paragrafo '3.', tolgo gli spazi e verifico sia numerico
                if ((line[:p].split('3.')[1]).strip()).isdigit():
                    subRow_ar.append(start + r)

        if len(subRow_ar) == 0:
            self.elab.cfg.Log.AddLog('\nErrore: Paragrafo 3 non trovato', False)
            return None

        LPar = len(Log_ob.p3[language]) + 4    #   limito la ricerca dei parametri

        for r in range(len(subRow_ar)):
            Log_ob.p3_val = self.getVal(Log_ar[subRow_ar[r]:subRow_ar[r]+ LPar], Log_ob.p3[language])
            if None in Log_ob.p3_val:
                self.elab.cfg.Log.AddLog('\nErrore: Paragrafo 3: campo non riconosciuto', False)
                return None #  segnalare e passare avanti
            else:
                Log_ob.p3_ar.append(Log_ob.p3_val)



        # carico info dal paragrafo 4
        start = subRow_ar[-1]
        subRow_ar = []
        sRif = Log_ob.FindRef[language][3]
        # for r, line in enumerate(Log_ar[start:stop]):
        for r, line in enumerate(Log_ar[start:]):
            p = line[:32].find(sRif)
            if p > 0:   #   cerco sRif fra i primi 20 char, tolgo il paragrafo '4.', tolgo gli spazi e verifico sia numerico
                if ((line[:p].split('4.')[1]).strip()).isdigit():
                    subRow_ar.append(start + r)

        if len(subRow_ar) == 0:
            self.elab.cfg.Log.AddLog('\nErrore: Paragrafo 4 non trovato', False)
            return None

        LPar = len(Log_ob.p4[language]) + 4  # limito la ricerca dei parametri

        for r in range(len(subRow_ar)):
            Log_ob.p4_val = self.getVal(Log_ar[subRow_ar[r]:subRow_ar[r]+ LPar], Log_ob.p4[language])
            if None in Log_ob.p4_val:
                self.elab.cfg.Log.AddLog('\nErrore: Paragrafo 4: campo non riconosciuto', False)
                return None     # segnalare e passare avanti
            else:
                Log_ob.p4_ar.append(Log_ob.p4_val)

        return Log_ob



#---
    def ConfrontLog(self, NewLog_ob, OldLog_ob, language):
        lField = 17
        sApp_ar = []
        sApp_ar.append('\n-----------\nConfronto New: %s\t<>\tOld: %s' % (NewLog_ob.nfile, OldLog_ob.nfile))

        #   confronto par 1
        i = 0
        par = 1
        while i < len(NewLog_ob.p1):
            if NewLog_ob.p1_val[i] <> OldLog_ob.p1_val[i]:
                sApp_ar.append('\nPar. %d - %s\t\told: %s \tnew: %s' %(par, NewLog_ob.p1[i], OldLog_ob.p1_val[i], NewLog_ob.p1_val[i]))
            i += 1

        # confronto par 3
        par = 3
        sub = 0
        while sub < min(len(NewLog_ob.p3_ar),len(OldLog_ob.p3_ar)):   #   verifico che i sub paragrafi in comune siano uguali
            i = 0
            while i < len(NewLog_ob.p3_ar[sub]):
                if NewLog_ob.p3_ar[sub][i] <> OldLog_ob.p3_ar[sub][i]:
                    sApp_ar.append('\nPar. %d.%d: %s ->\t\told: %s\t\t\tnew: %s' \
                           %(par, sub+1,
                             NewLog_ob.p3[language][i][:lField],
                             str(OldLog_ob.p3_ar[sub][i]),
                             str(NewLog_ob.p3_ar[sub][i])))
                i += 1
            sub += 1

        if len(NewLog_ob.p3_ar) > len(OldLog_ob.p3_ar):     #   nuovi paragrafi
            sApp_ar.append('\n\nAggiunto %d paragrafo' %(len(NewLog_ob.p3_ar) - len(OldLog_ob.p3_ar)))
            while sub < len(NewLog_ob.p3_ar):
                sApp_ar.append('\nNuovo paragrafo %s.%d' %(par, sub+1))
                i = 0
                while i < len(NewLog_ob.p3_ar[sub]):
                    if NewLog_ob.p3_ar[sub][i] <> NewLog_ob.p3_ar[sub-1][i]:
                        sApp_ar.append('\nPar. %d.%d: %s ->\t\told: %s\t\t\tnew: %s' \
                               %(par, sub+1,
                                 NewLog_ob.p3[language][i][:lField],
                                 NewLog_ob.p3_ar[sub-1][i],
                                 NewLog_ob.p3_ar[sub][i]))
                    i += 1
                sub += 1

        # confronto par 4
        par = 4
        sub = 0
        while sub < min(len(NewLog_ob.p4_ar),len(OldLog_ob.p4_ar)):   #   verifico che i sub paragrafi in comune siano uguali
            i = 0
            while i < len(NewLog_ob.p4_ar[sub]):
                if NewLog_ob.p4_ar[sub][i] <> OldLog_ob.p4_ar[sub][i]:
                    sApp_ar.append('\nPar. %d.%d: %s ->\t\told: %s\t\t\tnew: %s'
                                   %(par, sub+1, NewLog_ob.p4[language][i][:lField], str(OldLog_ob.p4_ar[sub][i]), str(NewLog_ob.p4_ar[sub][i])))
                i += 1
            sub += 1

        if len(NewLog_ob.p4_ar) > len(OldLog_ob.p4_ar):
            sApp_ar.append('\n\nAggiunto %d paragrafo' %(len(NewLog_ob.p4_ar) - len(OldLog_ob.p4_ar)))
            while sub < len(NewLog_ob.p4_ar):
                sApp_ar.append('\nNuovo paragrafo %d.%d' %(par , sub+1))
                i = 0
                while i < len(NewLog_ob.p4_ar[sub]):
                    if NewLog_ob.p4_ar[sub][i] <> NewLog_ob.p4_ar[sub-1][i]:
                        sApp_ar.append('\nPar. %d.%d : %s ->\t\told: %s\t\t\tnew: %s'
                                       %(par, sub+1, NewLog_ob.p4[language][i][:lField], NewLog_ob.p4_ar[sub-1][i], NewLog_ob.p4_ar[sub][i]))
                    i += 1
                sub += 1

        return sApp_ar


#---



    # Ciclo-Log-Compare
    def LogCompFTPnew_LogRepo(self, language):
        self.FtpNewLog_list = [f for f in listdir(self.elab.cfg.FTP_DIR_NewLog) if isfile(join(self.elab.cfg.FTP_DIR_NewLog, f))]
        self.FtpNewLog_list = self.elab.ftpConn.prendiUltimoLog(self.FtpNewLog_list)  # dopo DownLoad aggiorno la lista, formato [lowercase, nFile, DT, link]

        if len(self.FtpNewLog_list) > 0:
            for lineFTP in self.FtpNewLog_list:
                for j, lineRepo in enumerate(self.elab.RepoDir_ar):
                    if lineFTP[:4] == lineRepo[:4]: #   se vero -> questo station_id esiste nel RepoDir
                        #   carico su Log_object in Array le righe del Log
                        NewLog_ob = self.CaricaLog(self.elab.cfg.FTP_DIR_NewLog + '/' + lineFTP.split('\t')[1], language)  # carico le righe dei Log in modo ordinato nell'oggetto, come array, per facilitare confronto e crearae stationinfo
                        if not NewLog_ob:
                            self.elab.cfg.Log.AddLog('\nErrore nel CaricaLog: %s' % (lineFTP), False)
                            continue
                        NewLog_ob.nfile = lineFTP.split('\t')[1]

                        # carico su Array le righe del Log
                        nFileRepo = lineRepo.split('\t')[1]
                        OldLog_ob = self.CaricaLog(self.elab.cfg.DIR_Log_Repo + '/' + nFileRepo, language)
                        if not OldLog_ob:
                            self.elab.cfg.Log.AddLog('\nErrore nel CaricaLog: %s' % (lineRepo), False)
                            continue
                        OldLog_ob.nfile = lineFTP.split('\t')[1]


                        #**************** CONFRONTO LOG FILES *****************
                        sApp_ar = self.ConfrontLog(NewLog_ob, OldLog_ob, language)  #   aggiunge le differenze direttamente al Log che viene spedito per mail
                        if len(sApp_ar) > 1:
                            for row in sApp_ar:
                                self.elab.cfg.Log.AddLog(row, False)

                        #   Se esiste OldLog -> lo archivio insieme al suo file .stf
                        self.elab.spostaFile(nFileRepo, self.elab.cfg.DIR_Log_Repo, self.elab.cfg.DIR_OLD,True)  # sposta file da _Repo a _OLD
                        fname = OldLog_ob.p1_val[1].lower() + '.stf'
                        self.elab.spostaFile(fname, self.elab.cfg.DIR_stf, self.elab.cfg.DIR_OLD,True)  # sposta file da _Repo a _OLD
                        break
                #   in ogni caso sposto il NewLog nel RepoDir
                self.elab.spostaFile(lineFTP, self.elab.cfg.FTP_DIR_NewLog, self.elab.cfg.DIR_Log_Repo, False)  # sposta file da _Repo a _OLD

            dirAppCompleto = [f for f in listdir(self.elab.cfg.DIR_Log_Repo) if isfile(join(self.elab.cfg.DIR_Log_Repo, f))]  # directory originale, con caratteri upper e/o lower case
            self.elab.RepoDir_ar = list(self.elab.ftpConn.prendiUltimoLog(dirAppCompleto))  # directory formato [lower\tfname\t\t\n]


#------------------------------------------

class Log:
    def __init__(self):
        self.nfile = ''         #   nome del file

        self.stfTabName = ''    #   dal file .list prende la 3^ col e la usa come ID e nomeFile dello STF da processare

        self.FindRef = [['Site Identification', 'Site Location', 'Receiver Type','Antenna Type'],
                        ['Características da Monumentação', 'Localização Geográfica', 'Tipo de Receptor','Tipo de Antena']]

        self.p1 = [['Site Name','Four Character ID'],
                   ['Nome da Estação','Identificação 4 Caracteres']]
        self.p1_val = [None] * len(self.p1)


        self.p2 =[['X coordinate (m)',  #   Standard language
                    'Y coordinate (m)',
                    'Z coordinate (m)'],

                    ['X (m)',            #Portoghese
                    'Y (m)',
                    'Z (m)']]
        self.p2_val = [None] * len(self.p2)


        self.p3 = [['Receiver Type',
                   'Satellite System',
                   'Serial Number',
                   'Firmware Version',
                   'Elevation Cutoff Setting',
                   'Date Installed',
                   'Date Removed',
                   'Temperature Stabiliz',
                   'Additional Information'],

                   ['Tipo de Receptor',
                    'Sistema de Satélites',
                    'Número de Série',
                    'Versão do Firmware',
                    'Ângulo de Elevação',
                    'Data de Instalação',
                    'Data de Remoção',
                    'Informação Adicional']]
        self.p3_val = [None] * len(self.p3)
        self.p3_ar = []

        self.p4 = [['Antenna Type',
                   'Serial Number',
                   'Antenna Reference Point',
                   'Marker->ARP Up Ecc. (m)',
                   'Marker->ARP North Ecc(m)',
                   'Marker->ARP East Ecc(m)',
                   # 'Alignment from True N',
                   'Antenna Radome Type',
                   'Radome Serial Number',
                   'Antenna Cable Type',
                   'Antenna Cable Length',
                   'Date Installed',
                   'Date Removed',
                   'Additional Information'],

                   ['Tipo de Antena',
                    'Número de Série',
                    'Ponto de Referência',
                    'Marker->ARP Up Ecc. (m)',
                    'Marker->ARP North Ecc(m)',
                    'Marker->ARP East Ecc(m',
                    'Tipo de Protecção',
                    'Número Série da Protecção',
                    'Tipo de Cabo de Antena',
                    'Comprimento do cabo',
                    'Data de Instalação',
                    'Data de Remoção',
                    'Informação Adicional']]
        self.p4_val = [None] * len(self.p4)
        self.p4_ar = []


#------------------------------------------

