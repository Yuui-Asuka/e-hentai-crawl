import sys
system = sys.platform
if system == 'linux':
    host_file = '/etc/hosts'
else:
    host_file = 'C:\Windows\System32\drivers\etc\hosts'
dns = {'104.20.26.25':'e-hentai.org',
       '94.100.29.73':'repo.e-hentai.org',
       '94.100.18.243':'forums.e-hentai.org',
       '81.171.14.118':'ehgt.org',
       '94.100.24.82':'ul.ehgt.org'}
with open(host_file,'a') as f:
    for key,values in dns.items():
        f.write(key + '  ' + values + '\n')
