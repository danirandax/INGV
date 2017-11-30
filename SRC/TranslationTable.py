#!/usr/bin/python
from Elaborazione import *


class TranslationTable():

    def __init__(self, elab):
        self.elab = elab
        self.transTab_ar = []   # Array 3D: [[Rcv],[Ant],[Duo]]                         -> Translation Tab
        self.nuovaRiga = False
        self.getTransTab()



    def getTransTab(self):
        # carica i dato dalla TranslationTab
        if os.path.isfile(self.elab.ftpConn.conf.fTransTab):  # se non esiste,
            with open(self.elab.ftpConn.conf.fTransTab) as file:
                arApp = file.readlines()
                file.close()
            self.transTab_ar.append(self.getTTab(arApp, '#RCVCODE'))
            self.transTab_ar.append(self.getTTab(arApp, '#ANTCODE'))
            self.transTab_ar.append(self.getTTab(arApp, '#DUOCODE'))
        else:
            self.elab.cfg.Log.AddLog('Non esiste file Translation Table:\n%s\n-> creazione in corso\n' % self.elab.cfg.fTransTab, False)
            self.nuovaRiga = True
            self.transTab_ar.append([])
            self.transTab_ar.append([])
            self.transTab_ar.append([])
            self.AggiornaTTab()


#---


    def getTTab(self, arApp, startRif):
        transTab_ar = []
        for r, line in enumerate(arApp):
            if line[:len(startRif)] == startRif:
                break

        arApp = arApp[r+1:]
        endRif = '#END'
        for line in arApp:
            if line[:len(endRif)] != endRif:
                transTab_ar.append(line)
            else:
                break

        return transTab_ar



#---




    def verifCodTransTab(self, fakeCode, checkTab_ar, transTab_ar, rifTab):
        fakeCode = fakeCode.upper()

        trovato = False
        for row in checkTab_ar:
            if fakeCode in row:
                trovato = True
                break

        if trovato:
            return fakeCode, True

        for code in transTab_ar:
            arApp = code.split('\t')
            sFake = (arApp[0]).strip()
            sTrans = (arApp[1]).strip()
            if (fakeCode == sFake):
                # if (sTrans != '???'):
                if (sTrans.find('???') >= 0):
                    if (sTrans.find('#') >= 0): #   ignora la riga della TransTab e dai True
                        return '', True
                    else:
                        self.elab.cfg.Log.AddLog('\nAGGIORNARE TransTable del %s, codice: %s' %(rifTab, fakeCode), False)
                        return '', False
                else:                   # se non trova il fakeCode nella checkTab e neanche nella transTab, allora aggiunge una riga
                    return sTrans, True

        transTab_ar.append('%s\t%s\n' % (fakeCode, '???'))  #   se arriva qui, vuol dire che fakeCode non e' nella transTab
        self.elab.cfg.Log.AddLog('\nNUOVA RIGA nella TransTable del %s, codice: %s' % (rifTab, fakeCode), False)
        self.nuovaRiga = True
        return '', False


#---


    def verifCod(self, fakeCode, checkTab_ar):
        for row in checkTab_ar:
            if fakeCode in row:
                return fakeCode
        return ''





# Verifiche:
# 1) se ((A) e (R) e (D)) in rcvr_ant.tab
# 2) se ((A) e (R)) in rcvant.dat
# 3) se coppia [(A)_(D)] in antmod.dat


    def verifStfRow(self, stf):
        rcvrTT, rcvrFound = self.verifCodTransTab(stf.col_ar[8], self.elab.RcvrAntTab_ar[0], self.transTab_ar[0], 'Receiver')

        antFound = False
        duomoFound = False
        duomoTT = 'NONE'
        antDuo =stf.col_ar[12].split()
        if len(antDuo) == 1:
            duomoTT = 'NONE'
            duomoFound = True
            antTT, antFound = self.verifCodTransTab(stf.col_ar[12], self.elab.RcvrAntTab_ar[0], self.transTab_ar[1], 'Antenna')
        elif len(antDuo) > 1:   #   bisogna distinguere il Duomo
            if len(antDuo[-1:][0]) == 4:
                duomoTT, duomoFound = self.verifCodTransTab(antDuo[-1:][0], self.elab.RcvrAntTab_ar[1], self.transTab_ar[2], 'Dome')
                if (duomoFound):
                    if duomoTT == '':
                        duomoTT = 'NONE'
                        antCode = stf.col_ar[12]
                    else:
                        antCode = ''.join(antDuo[:-1])
                else:
                    antCode = stf.col_ar[12]
                antTT, antFound =  self.verifCodTransTab(antCode, self.elab.RcvrAntTab_ar[0], self.transTab_ar[1], 'Antenna')
                # antTT =  self.verifCodTransTab(stf.col_ar[12], self.RcvrAntTab_ar[0], self.transTab_ar[1], 'Antenna')
            else:
                duomoTT = 'NONE'
                duomoFound = True
                antTT, antFound = self.verifCodTransTab(stf.col_ar[12], self.elab.RcvrAntTab_ar[0], self.transTab_ar[1],'Antenna')


        if (not rcvrFound):
            self.elab.cfg.Log.AddLog('\n -> NON ESISTE (R): "%s" nel file RcvrAnt.tab e nella TransTable\n' % stf.col_ar[8], False)
            # return False
        if (not antFound):
            self.elab.cfg.Log.AddLog('\n -> NON ESISTE (A): "%s" nel file RcvrAnt.tab e nella TransTable\n' % stf.col_ar[12], False)
            # return False
        if (not duomoFound):
            self.elab.cfg.Log.AddLog('\n -> NON ESISTE (D): "%s" nel file RcvrAnt.tab e nella TransTable\n' % stf.col_ar[13], False)
            # return False
        if (not rcvrFound) or (not antFound) or (not duomoFound):
            return False

        rcvrTT, rcvrFound = self.verifCodTransTab(rcvrTT, self.elab.RcvAntDat_ar[0], self.transTab_ar[0], 'Receiver')
        antTT, antFound = self.verifCodTransTab(antTT, self.elab.RcvAntDat_ar[1], self.transTab_ar[1], 'Antenna')


        if (not rcvrFound):
            self.elab.cfg.Log.AddLog('\n -> NON ESISTE (R): "%s" nel file RcvAnt.dat\n' % stf.col_ar[8], False)
            return False

        if (not antFound):
            self.elab.cfg.Log.AddLog('\n -> NON ESISTE (A): "%s" nel file RcvAnt.dat\n' % stf.col_ar[12], False)
            return False

        coppia = '%-15s %4s'%(antTT, duomoTT)
        if (self.verifCod(coppia, self.elab.AntModDat_ar) == ''):
            duomoTT = 'NONE'

        stf.col_ar[8] = rcvrTT
        stf.col_ar[12] = antTT
        stf.col_ar[13] = duomoTT
        return True






    #---
    def AggiornaTTab(self):
        if not self.nuovaRiga:
            return

        arApp = []
        arApp.append('#Translation Table:\n1) "???" = replace equivalent code\n2) "???#" = ignore request, used for DUOCODE\n')
        arApp.append('#RCVCODE: format(FakeCode (tab) Translation) [20 char]\n')
        self.transTab_ar[0] = list(sorted(self.transTab_ar[0]))
        for line in self.transTab_ar[0]:
            arApp.append(line)
        arApp.append('#END\n---------\n\n')

        arApp.append('#ANTCODE: format(FakeCode (tab) Translation) [15 char]\n')
        self.transTab_ar[1] = list(sorted(self.transTab_ar[1]))
        for line in self.transTab_ar[1]:
            arApp.append(line)
        arApp.append('#END\n---------\n\n')

        arApp.append('#DUOCODE: format(FakeCode (tab) Translation) [4 char]\n')
        self.transTab_ar[2] = list(sorted(self.transTab_ar[2]))
        for line in self.transTab_ar[2]:
            arApp.append(line)
        arApp.append('#END')

        scritto = False
        while not scritto:
            try:
                file = open(self.elab.cfg.fTransTab, 'w')
                for line in arApp:
                    file.write(line)
                file.close()
                scritto = True
            except:
                time.sleep(2)
