
url = "http://rgp.ign.fr/logsheet/index.html"
urlFile = 'abmf_20081107.log'
path = '/home/danielerandazzo/PycharmProjects/003_CGPSmetadata_ES/SRC/DatiNet/RGP/RGP_Log_Repo/'
dskFile = 'abmf_20161114.log'



import urllib2
response = urllib2.urlopen(url)
html = response.read()
with open(path+dskFile, 'w') as file:
    file.writelines(html)
    file.close()
pass





import urllib2
file_name = url.split('/')[-1]
u = urllib2.urlopen(url)
f = open(file_name, 'wb')
meta = u.info()
file_size = int(meta.getheaders("Content-Length")[0])
print "Downloading: %s Bytes: %s" % (file_name, file_size)

file_size_dl = 0
block_sz = 8192
while True:
    buffer = u.read(block_sz)
    if not buffer:
        break

    file_size_dl += len(buffer)
    f.write(buffer)
    status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
    status = status + chr(8)*(len(status)+1)
    print status,

f.close()