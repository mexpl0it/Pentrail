---
name: ad-enum
description: Unauthenticated (and, with the tester's yes, credentialed) enumeration of an in-scope Active Directory domain controller through pentrail shot - domain and DC discovery, LDAP rootDSE and anonymous binds, SMB null sessions, RID cycling, Kerberos and DNS - and which steps are ask or deny. Use when ports 88, 389, 445 or 3268 point at a domain controller, or the tester asks about the domain.
---

# Active Directory enumeration

A host with 53, 88, 135, 389, 445, 464, 636, 3268 open is almost certainly a domain
controller. Rules: unauthenticated checks are `service_enum` (allow); anything with
credentials is `credentialed_enum` (ask); spraying or brute force deny; Kerberoasting,
AS-REP roasting and relaying are exploitation (deny, the tester's call).

## Unauthenticated (allow)

```bash
# domain, DC name, OS
pentrail shot -q --by pete --why "domain and DC name" -l ldap-rootdse -- nmap -p389 --script ldap-rootdse 10.10.10.5
pentrail shot -q --by pete --why "SMB: domain, signing, null session" -l nxc-smb -- netexec smb 10.10.10.5
pentrail shot -q --by pete --why "null session: shares" -l nxc-shares -- netexec smb 10.10.10.5 -u '' -p '' --shares
pentrail shot -q --by pete --why "users, groups, policy via null session" -l e4l -- enum4linux-ng -A 10.10.10.5
# anonymous LDAP bind: does it list objects?
pentrail shot -q --by pete --why "anonymous LDAP bind" -l ldap-anon -- \
  ldapsearch -x -H ldap://10.10.10.5 -b "DC=box,DC=htb" -s sub "(objectClass=user)" sAMAccountName
# DNS: SRV records name the DCs
pentrail shot -q --by pete --why "DC SRV records" -l dns-srv -- dig @10.10.10.5 _ldap._tcp.dc._msdcs.box.htb SRV
```

The domain from these steps belongs in the project facts: suggest `pentrail set domain
box.htb` (an ask step). Names like `dc01.box.htb` need `/etc/hosts` lines for Kerberos
tools: ask the tester (`pentrail hostfile add 10.10.10.5 dc01.box.htb box.htb`).

## With credentials (ask, and only the ones the tester hands you)

```bash
netexec smb 10.10.10.5 -u <user> -p <password> --users --shares --pass-pol
netexec ldap 10.10.10.5 -u <user> -p <password> --bloodhound -c All --dns-server 10.10.10.5
```

pentrail masks the password in every record and JSON. Ask before each, say what it
collects, and never reuse credentials on other hosts or services without a yes.

## Not yours

Password spraying (`netexec ... -p <list>`, kerbrute passwordspray), user enumeration with
big lists against Kerberos, Kerberoasting (`GetUserSPNs`), AS-REP roasting (`GetNPUsers`),
relaying (`ntlmrelayx`, responder), secretsdump. List them as possible next steps for the
tester when the evidence supports them (for example: "users without preauth exist (#22):
AS-REP roasting is a foothold option").

## What to look for

Null session or guest access, anonymous LDAP, the password policy (lockout threshold
before anyone sprays), users with descriptions holding passwords, SMB signing off, old
OS versions.

## Read more

- https://book.hacktricks.wiki/en/windows-hardening/active-directory-methodology/index.html
- https://www.netexec.wiki/
