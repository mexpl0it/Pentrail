---
name: service-enum
description: Safe per-service enumeration of open ports through pentrail shot - FTP, SSH, SMTP, DNS, SMB, SNMP, LDAP, NFS, RPC, databases, RDP/WinRM, Redis - with what each step tells you and which steps are ask or deny under the PeTe rules. Use after ports are known, for the per-port steps in pentrail next, or when the tester asks to look at one service.
---

# Service enumeration

Rule: `service_enum` (allow): versions, banners, safe NSE scripts (`*-info`, `*-enum-*`,
`*-capabilities`), anonymous and null-session checks. `pentrail next <host> --json` holds
the per-port playbook; dedupe with `pentrail seen` first.

Every row runs as `pentrail shot -q --by pete --why "<why>" -l <label> -- <command>`.

| Service | Steps (allow) | Look for | Not yours |
|---|---|---|---|
| ftp 21 | `nmap -p21 --script ftp-anon,ftp-syst <t>` | anonymous login, writable dirs, files | logging in with guessed creds |
| ssh 22 | `nmap -p22 --script ssh2-enum-algos,ssh-auth-methods <t>`, `ssh-audit <t>` | password auth on, old algorithms, version | any login attempt |
| smtp 25 | `nmap -p25 --script smtp-commands <t>` | VRFY/EXPN enabled, open relay hints | user enumeration with a list: ask |
| dns 53 | `dig axfr @<t> <domain>`, `dig @<t> <domain> ANY` | zone transfer, internal names | |
| smb 139/445 | `smbclient -L //<t>/ -N`, `enum4linux-ng -A <t>`, `nmap -p445 --script smb-enum-shares,smb-os-discovery,smb2-security-mode <t>` | guest/null access, readable shares, signing off, users | `smb-vuln-*`: vuln_scripts (ask) |
| snmp 161/udp | `snmpwalk -v2c -c public <t>`, `onesixtyone <t> public` | community `public`, processes, users, routes | community wordlists: brute_force |
| ldap 389/636 | `nmap -p389 --script ldap-rootdse <t>`, `ldapsearch -x -H ldap://<t> -s base namingcontexts` | naming contexts, domain, anonymous bind | binds with credentials: ask |
| nfs 2049 | `showmount -e <t>`, `nmap -p2049 --script nfs-ls,nfs-showmount <t>` | exports to `*`, readable files | mounting and writing |
| rpc 111 | `rpcinfo -p <t>` | nfs, mountd, nis | |
| mysql 3306 | `nmap -p3306 --script mysql-info <t>` | version, auth plugin | `mysql -u root`, `mysql-empty-password`: guessed logins = brute_force |
| mssql 1433 | `nmap -p1433 --script ms-sql-info,ms-sql-ntlm-info <t>` | instance, domain | logins |
| postgres 5432 | `nmap -p5432 -sV <t>` | version | `pgsql-brute`: brute_force (deny) |
| rdp 3389 | `nmap -p3389 --script rdp-ntlm-info,rdp-enum-encryption <t>` | hostname, domain, NLA | connecting |
| winrm 5985/6 | `nmap -p5985 --script http-title <t>` | WinRM up (a later foothold path) | evil-winrm: exploitation |
| redis 6379 | `nmap -p6379 --script redis-info <t>` | no auth, version | writing keys |

Notes:

- The playbook in `pentrail next --json` lists some steps that are not allow for you (marked in
  the last column). Classify, list them for the tester, do not run them.
- Interactive clients (`ftp`, `smbclient` without `-L`/`-c`, `mysql`) need a shell; use the
  NSE script or a one-shot form (`smbclient //<t>/share -N -c 'ls'`).
- Each readable share, anonymous login or exposed list is a lead:
  `pentrail vector add "guest read on \\<t>\backups (#id)" -t smb`.

## Read more

- https://book.hacktricks.wiki/en/network-services-pentesting/index.html (one page per service)
