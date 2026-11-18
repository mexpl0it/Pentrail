---
name: sandbox-test
description: Running and checking pentrail safely while developing it - a throwaway HOME with a project, stand-in tools instead of real scanners, a private hosts file, calling the Claude Code hooks by hand, and driving pentrail capture in a real pseudo-terminal (bash and zsh). Use before claiming a change works, to reproduce a bug the user reports, or to try a command without touching the user's real projects, config, /etc/hosts or any real host.
---

# Trying pentrail safely

Never run a change against the user's real `~/pentests`, `~/.config/pentrail`, `/etc/hosts`
or a real target. Everything below stays inside one temporary folder.

## A sandbox in four lines

```bash
H=$(mktemp -d); mkdir -p $H/bin; ln -s "$PWD/pentrail.py" $H/bin/pentrail
printf '#!/bin/sh\necho "Nmap scan report for 10.10.10.5"\necho "22/tcp open  ssh  OpenSSH 8.2"\n' > $H/bin/nmap; chmod +x $H/bin/nmap
export HOME=$H PATH=$H/bin:/usr/bin:/bin NO_COLOR=1 PENTRAIL_HOSTS_FILE=$H/hosts; echo "127.0.0.1 localhost" > $H/hosts
pentrail new box1 10.10.10.5 --no-vpn && pentrail scope add 10.10.10.5
```

- Stand-in tools in `$H/bin` print canned output (nmap, netexec, hydra writing a marker
  file to prove it did not run). pentrail parses them like the real thing.
- `PENTRAIL_HOSTS_FILE` points `hostfile`/`resolve` and the scope at a private hosts file;
  writing it then needs no sudo.
- `$H/bin/pentrail` on PATH lets the hooks and `pete status` find "the launcher".
- `tests/test_pentrail.py` has the same thing as `class Sandbox`; from Python:
  `import sys; sys.path.insert(0, "tests"); import test_pentrail as t; sb = t.Sandbox()`.

## The Claude Code hooks by hand

```bash
D=$(pentrail dir); pentrail pete install
echo '{"tool_name":"Bash","cwd":"'$D'","tool_input":{"command":"nmap -sV 10.10.10.5"}}' | pentrail ai hook pretooluse
echo '{"source":"startup","cwd":"'$D'"}' | pentrail ai hook sessionstart
echo '{"workspace":{"current_dir":"'$D'"}}' | pentrail ai statusline
```

An empty answer from `pretooluse` means "no decision" (Claude Code's permissions decide).

## A capture, typed like a person

`pentrail capture` needs a terminal. `TestCapture.drive()` in the tests forks a pty, starts
the capture, types commands with `os.write(fd, b"nmap -sV 10.10.10.5\r")`, and reads
`state.json` between commands: that is how "read only at exit" was found and is guarded.
Reuse it rather than writing a new driver.

zsh: the tests run the zsh variant when `zsh` is on PATH. Without root you can unpack it:
`apt-get download zsh zsh-common && for f in *.deb; do dpkg -x $f ./zsh-root; done`, then in
the sandbox's `.zshenv` set `module_path=(<root>/usr/lib/<arch>/zsh/5.9)` and
`fpath=(<root>/usr/share/zsh/functions/*(/) $fpath)`. A wrong fpath alone made the hook fail
to load once; the capture now says so at exit.

## Things that are not safe to try here

`pentrail up/down/restart` (real sudo openvpn), `setup`, `update`, `uninstall` without
`--dry-run`, and anything with `sudo`. Test VPN logic by replacing functions in a loaded
module (`load_module()` in the tests), as `test_vpn_up_is_seen_without_a_readable_log` does.
