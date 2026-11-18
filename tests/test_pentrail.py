"""pentrail's tests: standard library only, under a throwaway $HOME, with no network
traffic and no sudo. Run from the repository root:

    python3 -m unittest discover -s tests -v

Stand-in tools (nmap, hydra, netexec) live in the sandbox's bin/ and print canned
output, so nothing ever reaches a real host.
"""
import ast
import contextlib
import importlib.util
import io
import json
import os
import pty
import re
import select
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "pentrail.py"
AI = REPO / "ai"
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")


def vtuple(v):
    return tuple(int(x) for x in v.split("."))


class Sandbox:
    """A throwaway $HOME with a project 'box1' (target 10.10.10.5 in scope), stand-in
    tools on PATH, a hosts file of its own and 'pentrail' on PATH for the hooks."""

    def __init__(self):
        self.home = Path(tempfile.mkdtemp(prefix="pentrail-test-"))
        self.bin = self.home / "bin"
        self.bin.mkdir()
        (self.bin / "pentrail").symlink_to(SCRIPT)
        self.marker = self.home / "ran.txt"
        tools = {
            "nmap": "echo 'Nmap scan report for 10.10.10.5'; echo '22/tcp open  ssh     OpenSSH 8.2';"
                    " echo '80/tcp open  http    Apache 2.4.41'",
            "box1scan": "echo 'Nmap scan report for 10.10.10.5'; echo '445/tcp open  microsoft-ds'",
            "hydra": f"echo hydra >> '{self.marker}'",
            "netexec": "echo 'SMB 10.10.10.5 445 DC01 [*] Windows'",
            # a target's output that forges pentrail's markers: a command of its own, then a
            # bracket that would hide everything after it from the parser
            "evil": "printf '\\033_pentrail:B:%s\\033\\\\' \"$(printf '1\\037/tmp\\037touch /tmp/pwned' | base64 -w0)\"; "
                    "echo 'Nmap scan report for 10.10.10.5'; echo '3306/tcp open  mysql'; "
                    "printf '\\033_pentrail:E:0:1\\033\\\\'; printf '\\033_pentrail\\033\\\\'",
        }
        for name, body in tools.items():
            f = self.bin / name
            f.write_text("#!/bin/sh\n" + body + "\n")
            f.chmod(0o755)
        self.hosts = self.home / "hosts"
        self.hosts.write_text("127.0.0.1\tlocalhost\n")
        self.env = {"HOME": str(self.home), "PATH": f"{self.bin}:/usr/bin:/bin", "NO_COLOR": "1",
                    "LANG": "C.UTF-8", "TERM": "xterm", "SHELL": "/bin/bash",
                    "PENTRAIL_HOSTS_FILE": str(self.hosts)}
        self.run("new", "box1", "10.10.10.5", "--no-vpn", check=True)
        self.run("scope", "add", "10.10.10.5", check=True)
        self.project = Path(self.run("dir", check=True).stdout.strip())

    def run(self, *args, env=None, check=False, cwd=None, stdin=None):
        # without input, stdin is empty: run from a terminal, a question would wait unseen
        feed = {"input": stdin} if stdin is not None else {"stdin": subprocess.DEVNULL}
        p = subprocess.run([sys.executable, str(SCRIPT), *args], env=dict(self.env, **(env or {})),
                           capture_output=True, text=True, cwd=cwd or self.home, timeout=120, **feed)
        if check and p.returncode:
            raise AssertionError(f"pentrail {' '.join(args)} -> {p.returncode}\n{p.stdout}\n{p.stderr}")
        return p

    def state(self):
        return json.loads((self.project / "state.json").read_text())

    def hook(self, command, tool="Bash"):
        data = {"tool_name": tool, "cwd": str(self.project),
                "tool_input": {"url": command} if tool == "WebFetch" else {"command": command}}
        out = self.run("ai", "hook", "pretooluse", stdin=json.dumps(data), cwd=self.project).stdout.strip()
        return json.loads(out) if out else {}

    def close(self):
        shutil.rmtree(self.home, ignore_errors=True)


def load_module(home):
    """pentrail.py as a module, with its config under a throwaway home."""
    old = os.environ.get("HOME")
    os.environ["HOME"] = str(home)
    try:
        spec = importlib.util.spec_from_file_location("pentrail_under_test", SCRIPT)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    finally:
        if old is not None:
            os.environ["HOME"] = old


class TestRepository(unittest.TestCase):
    """The shape of the repository: one file that compiles, versions that agree, an AI
    layer whose skills only name pentrail commands that exist."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="pentrail-mod-"))
        cls.pt = load_module(cls.tmp)
        cls.commands = set(cls.pt.build_parser()._subparsers._group_actions[0].choices)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_python38_syntax_and_no_duplicate_names(self):
        tree = ast.parse(SCRIPT.read_text(), feature_version=(3, 8))
        names = [n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))]
        dupes = sorted({n for n in names if names.count(n) > 1})
        self.assertEqual(dupes, [], "a top-level name is defined twice; the second silently wins")
        details = []
        for n in tree.body:                         # DETAILS = {...} and DETAILS.update({...})
            if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "DETAILS":
                details += [k.value for k in n.value.keys]
            if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call) \
                    and getattr(n.value.func, "attr", "") == "update" \
                    and getattr(n.value.func.value, "id", "") == "DETAILS":
                details += [k.value for k in n.value.args[0].keys]
        self.assertEqual(sorted({k for k in details if details.count(k) > 1}), [],
                         "a help entry is written twice; only the last one shows")

    def test_versions_agree(self):
        v = self.pt.VERSION
        self.assertRegex(v, SEMVER, "VERSION is MAJOR.MINOR.PATCH (see CONTRIBUTING.md)")
        top = re.search(r"^## (\S+)", (REPO / "CHANGELOG.md").read_text(), re.M).group(1)
        self.assertIn(top, (v, "Unreleased"), "the newest CHANGELOG heading is VERSION or Unreleased")
        if top == "Unreleased":
            self.assertRegex((REPO / "CHANGELOG.md").read_text(), rf"(?m)^## {re.escape(v)}\b")
        ai = (AI / "VERSION").read_text().strip()
        self.assertRegex(ai, SEMVER)
        self.assertLessEqual(vtuple(ai), vtuple(v), "ai/VERSION is the release that last changed ai/")

    def test_rules_md_matches_the_default_rules(self):
        block = self.pt.RULES_RE.search((AI / "claude" / "rules.md").read_text()).group(0)
        self.assertEqual(block.strip(), self.pt.RULES_BLOCK.strip(),
                         "ai/claude/rules.md and RULES_BLOCK in pentrail.py must hold the same rules")

    def test_settings_json(self):
        s = json.loads((AI / "claude" / "settings.json").read_text())
        self.assertEqual(s["env"]["PENTRAIL_ACTOR"], "pete")
        pre = s["hooks"]["PreToolUse"][0]
        self.assertEqual(pre["matcher"], "Bash|WebFetch")
        self.assertIn("ai hook pretooluse", pre["hooks"][0]["command"])
        self.assertEqual(pre["hooks"][0].get("onFailure"), "block", "a guard that fails must block")
        self.assertIn("ai hook sessionstart", json.dumps(s["hooks"]["SessionStart"]))
        deny = s["permissions"]["deny"]
        for cmd in ("scope add", "config", "capture", "ai install", "pete install", "pete remove"):
            self.assertIn(f"Bash(pentrail {cmd} *)", deny)
        for rule in sum(s["permissions"].values(), []):
            self.assertNotRegex(rule, r":\*\)$", "use the 'Bash(cmd *)' form")
            m = re.match(r"Bash\(pentrail (\S+)", rule)
            if m:
                self.assertIn(m.group(1).rstrip(")"), self.commands, rule)

    def test_skills_are_well_formed(self):
        skills = sorted(p for p in (AI / "claude" / "skills").iterdir() if p.is_dir())
        self.assertGreaterEqual(len(skills), 14)
        for d in skills:
            text = (d / "SKILL.md").read_text()
            m = re.match(r"^---\nname: (.+)\ndescription: (.+)\n---\n", text)
            self.assertTrue(m, f"{d.name}: frontmatter with name and description")
            self.assertEqual(m.group(1).strip(), d.name)
            self.assertLess(len(m.group(2)), 1024, f"{d.name}: description too long for the skill list")
        listed = re.findall(r"`([a-z-]+)`", (AI / "claude" / "CLAUDE.md").read_text().split("## Skills")[1])
        self.assertEqual(sorted(listed), [d.name for d in skills], "CLAUDE.md lists every skill")

    def test_ai_files_only_use_real_pentrail_commands(self):
        files = [AI / "claude" / "CLAUDE.md", AI / "README.md"] + list((AI / "claude" / "skills").rglob("SKILL.md"))
        for f in files:
            text = f.read_text()
            code = "\n".join(re.findall(r"```.*?```", text, re.S) + re.findall(r"`[^`\n]+`", text))
            for sub in re.findall(r"\bpentrail ([a-z][a-z-]+)", code):
                self.assertIn(sub, self.commands, f"{f.relative_to(REPO)}: 'pentrail {sub}' is not a command")
            self.assertNotRegex(text, r"`pete (plan|trace|seen|show|status)\b",
                                f"{f.relative_to(REPO)}: there is no 'pete' program; use 'pentrail ...'")

    def test_guard_knows_pete_and_why(self):
        pt = self.pt
        for cmd in ("ai install box1", "pete install", "pete remove x", "ai update --all", "scope add 1.2.3.4",
                    "config pete_rules off", "capture"):
            self.assertTrue(pt._GUARD_CMDS.match(cmd), cmd)
        self.assertFalse(pt._GUARD_CMDS.match("pete brief"))
        words = pt._words("pentrail shot -q --by pete --why 'two words' -l x -- nmap -sV 10.10.10.5")
        self.assertEqual(pt._shot_inner(words), ["nmap", "-sV", "10.10.10.5"])

    def test_only_the_captures_own_markers_count(self):
        pt, key = self.pt, "0123456789abcdef"
        mine = f"\x1b_pentrail:{key}:B:abc\x1b\\out\x1b_pentrail:{key}:E:0:1\x1b\\"
        forged = "\x1b_pentrail:B:xyz\x1b\\ \x1b_pentrail:fedcba9876543210:E:0:1\x1b\\"
        got = pt.trusted_markers(mine + forged, key)
        self.assertEqual(len(pt._MARK_RE.findall(got)), 2)
        self.assertEqual(pt._MARK_RE.findall(pt.trusted_markers(mine + forged, "")), [])
        self.assertEqual(pt.strip_markers(mine), "out")
        hidden = pt.cap_begin(key) + "pentrail's own output" + pt.cap_end(key) + pt.CAP_BEGIN + "a target's"
        self.assertEqual(pt._strip_capture_echo(hidden, key), "a target's")

    def test_tun_devices_are_parsed(self):
        pt = self.pt
        out = ("1: lo    inet 127.0.0.1/8 scope host lo\\       valid_lft forever\n"
               "2: eth0    inet 10.0.2.15/24 brd 10.0.2.255 scope global eth0\n"
               "5: tun0    inet 10.10.14.3/23 scope global tun0\\       valid_lft forever\n")
        real = pt._ip
        pt._ip = lambda args: out
        try:
            self.assertEqual(pt._tun_devs(), {"tun0": "10.10.14.3"})
        finally:
            pt._ip = real

    def test_vpn_up_is_seen_without_a_readable_log(self):
        """openvpn's log is 0600 (root's under sudo): a new tun address counts as connected."""
        pt = self.pt
        calls = {"n": 0}
        def devs():
            calls["n"] += 1
            return {"tun0": "10.10.14.3"} if calls["n"] > 1 else {}
        saved = (pt._read, pt._tun_devs, pt.vpn_running, pt.tun_ip, pt.time.sleep)
        pt._read, pt._tun_devs, pt.vpn_running = (lambda *a, **k: ""), devs, (lambda: True)
        pt.tun_ip, pt.time.sleep = (lambda dev=None: "10.10.14.3"), (lambda s: None)
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertTrue(pt.wait_for_tunnel({}))
        finally:
            pt._read, pt._tun_devs, pt.vpn_running, pt.tun_ip, pt.time.sleep = saved


class TestCommands(unittest.TestCase):
    def setUp(self):
        self.sb = Sandbox()

    def tearDown(self):
        self.sb.close()

    def test_new_asks_for_a_vpn_only_for_ips(self):
        sb = self.sb
        (sb.home / "vpn").mkdir()
        (sb.home / "vpn" / "lab.ovpn").write_text("client\n")
        sb.run("config", "vpn_dir", str(sb.home / "vpn"), check=True)
        p = sb.run("new", "acme", "*.acme.com", check=True)
        self.assertIn("No IP in the targets, so no VPN", p.stdout)
        p = sb.run("new", "box3", "10.10.10.7", check=True)         # no terminal: nothing starts unasked
        self.assertIn("VPN not started (no terminal to ask in; --vpn starts it)", p.stdout)
        self.assertNotIn("Connecting", p.stdout)

    def test_new_asks_nothing_when_its_output_is_not_a_terminal(self):
        # stdin a terminal, stdout captured (a pipe, a test, a script): the question would be
        # invisible and 'new' would wait for an answer forever
        master, slave = pty.openpty()
        try:
            p = subprocess.run([sys.executable, str(SCRIPT), "new", "box2", "10.10.10.6", "--no-vpn"],
                               env=self.sb.env, stdin=slave, capture_output=True, text=True, timeout=30)
        finally:
            os.close(master)
            os.close(slave)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertNotIn("Hostname(s)", p.stdout)

    def test_scope_check_exit_codes(self):
        self.assertEqual(self.sb.run("scope", "check", "10.10.10.5").returncode, 0)
        self.assertEqual(self.sb.run("scope", "check", "nmap", "8.8.8.8").returncode, 3)
        self.assertEqual(self.sb.run("scope", "check", "ls", "-la").returncode, 2)

    def test_shot_records_why_and_trace_filters_by_actor(self):
        sb = self.sb
        p = sb.run("shot", "-q", "--why", "versions on 22 and 80", "-l", "sv", "--", "nmap", "-sV", "10.10.10.5",
                   env={"PENTRAIL_ACTOR": "pete"}, cwd=sb.project)
        self.assertEqual(p.returncode, 0, p.stderr)
        sb.run("shot", "-q", "-l", "mine", "--", "nmap", "-p22", "10.10.10.5", check=True, cwd=sb.project)
        cmds = sb.state()["commands"]
        self.assertEqual([(c["via"], c.get("why", "")) for c in cmds],
                         [("pete", "versions on 22 and 80"), ("", "")])
        t = json.loads(sb.run("trace", "--by", "pete", "--json", check=True).stdout)
        got = [c for h in t["hosts"] for c in h["commands"]]
        self.assertEqual([(c["by"], c["why"]) for c in got], [("pete", "versions on 22 and 80")])
        t = json.loads(sb.run("trace", "--by", "you", "--json", check=True).stdout)
        self.assertEqual([c["by"] for h in t["hosts"] for c in h["commands"]], ["you"])
        self.assertIn("why: versions on 22 and 80", (sb.project / "logbook.md").read_text())

    def test_pete_rules_deny_inside_shot_for_an_actor(self):
        sb = self.sb
        p = sb.run("shot", "-q", "-l", "h", "--", "hydra", "-l", "root", "-P", "x.txt", "ssh://10.10.10.5",
                   env={"PENTRAIL_ACTOR": "pete"}, cwd=sb.project)
        self.assertEqual(p.returncode, 3)
        self.assertFalse(sb.marker.exists(), "a denied tool must not run")
        self.assertIn("PeTe rule brute_force: deny", (sb.project / "logbook.md").read_text())
        p = sb.run("shot", "-q", "-l", "h", "--", "hydra", "-l", "root", "-P", "x.txt", "ssh://10.10.10.5",
                   cwd=sb.project)
        self.assertEqual(p.returncode, 0, "the PeTe rules are for an assistant, not for you")

    def test_runbook(self):
        sb = self.sb
        sb.run("shot", "-q", "--why", "first look", "-l", "a", "--", "nmap", "-sV", "10.10.10.5",
               env={"PENTRAIL_ACTOR": "pete"}, check=True, cwd=sb.project)
        sb.run("shot", "-q", "-l", "nxc", "--", "netexec", "smb", "10.10.10.5", "-u", "admin", "-p", "Secret123",
               check=True, cwd=sb.project)
        sb.run("shot", "-q", "-l", "pipe", "--", "sh", "-c", "nmap -p80 10.10.10.5 | head -3",
               check=True, cwd=sb.project)
        text = sb.run("runbook", "-H", "10.10.10.5", check=True).stdout
        self.assertIn("--why 'rerun of #1: first look' -- nmap -sV 10.10.10.5", text)
        self.assertNotIn("Secret123", text)
        self.assertRegex(text, r"(?m)^# pentrail shot .*netexec .*-p \[secret\]$", "a step with a secret is commented out")
        self.assertIn("-- sh -c 'nmap -p80 10.10.10.5 | head -3'", text, "a shell line is kept quoted, not wrapped twice")
        self.assertIn("by pete", text)
        only = sb.run("runbook", "--by", "pete", check=True).stdout
        self.assertEqual(only.count("pentrail shot -q"), 1)
        out = sb.project / "rerun.sh"
        sb.run("runbook", "--ids", "1", "-o", str(out), check=True)
        time.sleep(1.1)                 # the same command in the same second counts as the same record
        p = subprocess.run(["sh", str(out)], env=sb.env, capture_output=True, text=True, timeout=60,
                           stdin=subprocess.DEVNULL)
        self.assertEqual(p.returncode, 0, p.stderr)
        last = sb.state()["commands"][-1]
        self.assertEqual((last["cmd"], last["why"]), ("nmap -sV 10.10.10.5", "rerun of #1: first look"))

    def test_enum_doc_holds_what_was_found_not_a_todo_list(self):
        sb = self.sb
        sb.run("shot", "-q", "-l", "sv", "--", "nmap", "-sV", "10.10.10.5", check=True, cwd=sb.project)
        doc = sb.project / "1-enum" / "enum.md"
        text = doc.read_text()
        self.assertIn("| 22/tcp | ssh | OpenSSH 8.2 |", text)
        self.assertNotIn("Checklist", text)
        self.assertNotIn("- [ ]", text)
        # a doc from before 1.10.0 loses its checklist section and keeps the rest
        old = text.replace("### Logged notes", "### Checklist\n<!-- pentrail:auto checklist 10.10.10.5 -->\n"
                           "- [ ] 22/ssh: ssh-audit 10.10.10.5\n<!-- pentrail:end checklist 10.10.10.5 -->\n\n"
                           "### Logged notes", 1).replace("## Notes\n", "## Notes\nmine\n", 1)
        doc.write_text(old)
        sb.run("shot", "-q", "-l", "p22", "--", "nmap", "-p22", "10.10.10.5", check=True, cwd=sb.project)
        text = doc.read_text()
        self.assertNotIn("Checklist", text)
        self.assertIn("## Notes\nmine\n", text)
        steps = sb.run("next", "--steps", check=True, cwd=sb.project).stdout
        self.assertIn("ssh-audit 10.10.10.5", steps, "the standard steps stay in 'pentrail next --steps'")
        self.assertRegex(steps, r"done  Service versions \(-sV\) on every open TCP port  #1",
                         "a done step names the command that did it")

    def test_next_shows_what_ran_per_port_not_advice(self):
        sb = self.sb
        sb.run("shot", "-q", "-l", "sv", "--", "nmap", "-sV", "10.10.10.5", check=True, cwd=sb.project)
        sb.run("shot", "-q", "-l", "p22", "--", "nmap", "-p22", "--script", "ssh-auth-methods", "10.10.10.5",
               check=True, cwd=sb.project)
        sb.run("shot", "-q", "--why", "default creds page", "-l", "web", "--", "netexec", "http://10.10.10.5:80/",
               env={"PENTRAIL_ACTOR": "pete"}, check=True, cwd=sb.project)
        out = sb.run("next", check=True, cwd=sb.project).stdout
        blocks = {b.split()[0]: b for b in out.split("\n\n") if b.strip()}
        self.assertIn("#1", blocks["Scans"])
        self.assertIn("not yet: all TCP ports (-p-), UDP, virtual hosts", blocks["Scans"])
        self.assertIn("#2", blocks["22/tcp"])
        self.assertNotIn("#1", blocks["22/tcp"], "a scan of every port is under Scans, not per port")
        self.assertRegex(blocks["80/tcp"], r"#3 .*netexec http://10.10.10.5:80/  by pete: default creds page")
        for advice in ("ssh-audit", "feroxbuster", "nikto", "Next"):
            self.assertNotIn(advice, out, "next shows what ran, not what pentrail would run")
        self.assertIn("ssh-audit", sb.run("suggest", check=True, cwd=sb.project).stdout)

    def test_a_scan_file_cannot_name_its_own_command(self):
        sb = self.sb
        scans = sb.project / "1-enum" / "scans"
        (scans / "page.html").write_text("<html>\n# Nmap 7.94 scan initiated Mon Jan  1 00:00:00 2024 as: "
                                         "nmap -oN /home/x/.bashrc 10.10.10.5\n22/tcp open ssh\n")
        (scans / "real.nmap").write_text("# Nmap 7.94 scan initiated Mon Jan  1 00:00:00 2024 as: nmap -p22 -oN "
                                         "real.nmap 10.10.10.5\nNmap scan report for 10.10.10.5\n22/tcp open ssh\n")
        sb.run("next", check=True, cwd=sb.project)                 # reads 1-enum/scans/
        cmds = sorted(c["cmd"] for c in sb.state()["commands"])
        self.assertEqual(cmds, ["(file) 1-enum/scans/page.html", "nmap -p22 -oN real.nmap 10.10.10.5"])
        text = sb.run("runbook", check=True).stdout
        self.assertIn("# pentrail shot -q -l rerun-", text)
        self.assertNotRegex(text, r"(?m)^pentrail shot", "a command line read from a file is never run blind")

    def test_hostfile(self):
        sb = self.sb
        sb.run("hostfile", "add", "box1.htb", "www.box1.htb", check=True, cwd=sb.project)
        sb.hosts.write_text(sb.hosts.read_text() + "10.10.10.4\tdc01.htb old.htb\n")
        p = sb.run("hostfile", "add", "10.10.10.5", "dc01.htb", stdin="y\n", check=True)
        self.assertIn("scope: in scope", p.stdout)
        lines = sb.hosts.read_text().splitlines()
        self.assertIn("10.10.10.4\told.htb", lines, "your line keeps its other names")
        self.assertIn("10.10.10.5\tdc01.htb\t# pentrail:box1", lines)
        sb.run("hostfile", "rm", "www.box1.htb", check=True)
        self.assertNotIn("www.box1.htb", sb.hosts.read_text())
        sb.run("hostfile", "clean", check=True)
        self.assertEqual(sb.hosts.read_text(), "127.0.0.1\tlocalhost\n10.10.10.4\told.htb\n")

    def test_pete_install_status_remove(self):
        sb = self.sb
        own = {"permissions": {"allow": ["Bash(ls *)"]}, "model": "mine"}
        (sb.project / ".claude").mkdir()
        (sb.project / ".claude" / "settings.json").write_text(json.dumps(own))
        p = sb.run("pete", "install", check=True)
        self.assertIn("wrote 14 skills", p.stdout)
        self.assertEqual(sb.run("pete", "install", check=True).stdout.count("nothing to change"), 1)
        s = json.loads((sb.project / ".claude" / "settings.json").read_text())
        self.assertEqual(s["model"], "mine")
        self.assertIn("Bash(ls *)", s["permissions"]["allow"])
        self.assertEqual(s["env"]["PENTRAIL_PROJECT"], str(sb.project))
        stamp = json.loads((sb.project / ".claude" / "pentrail-ai.json").read_text())
        self.assertEqual(stamp["version"], (AI / "VERSION").read_text().strip())
        self.assertEqual(sb.run("pete", "status").returncode, 0, sb.run("pete", "status").stdout)
        self.assertIn("pentrail trace --by pete", sb.run("pete").stdout)
        sb.run("pete", "remove", check=True)
        self.assertFalse((sb.project / "CLAUDE.md").exists())
        self.assertEqual(json.loads((sb.project / ".claude" / "settings.json").read_text()), own)

    def test_guardrail_hook(self):
        sb = self.sb
        sb.run("pete", "install", check=True)
        d = sb.hook("nmap -sV 10.10.10.5")["hookSpecificOutput"]
        self.assertEqual(d["permissionDecision"], "deny")
        self.assertIn("pentrail shot -q --by pete --why", d["permissionDecisionReason"])
        self.assertEqual(sb.hook("curl http://8.8.8.8/")["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertEqual(sb.hook("pentrail shot -q --by pete --why 'x y' -l a -- nmap 10.10.10.5"), {})
        self.assertEqual(sb.hook("pentrail pete install")["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertEqual(sb.hook("pentrail shot -q --by pete --why 'x' -l h -- hydra -P x ssh://10.10.10.5")
                         ["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertEqual(sb.hook("pentrail trace --by pete"), {})


class TestCapture(unittest.TestCase):
    """A capture typed into a real terminal: what you run is in state.json before you exit."""

    def drive(self, shell, zshenv=None):
        sb = Sandbox()
        self.addCleanup(sb.close)
        env = dict(sb.env, SHELL=shell)
        if zshenv:
            (sb.home / ".zshenv").write_text(zshenv)
        (sb.home / ".zshrc").write_text("PS1='%~%# '\n")
        pid, fd = pty.fork()
        if pid == 0:
            os.chdir(sb.project)
            os.execve(sys.executable, [sys.executable, str(SCRIPT), "capture", "t1"], env)
        buf = []
        def pump(seconds):
            end = time.time() + seconds
            while time.time() < end:
                if select.select([fd], [], [], 0.1)[0]:
                    try:
                        buf.append(os.read(fd, 65536))
                    except OSError:
                        return
        def ports():
            st = sb.state()
            return sorted(p["port"] for h in st["hosts"] for p in h["ports"])
        try:
            pump(3)
            os.write(fd, b"box1scan\r")             # no host on the line: the hook leaves it
            pump(4)
            self.assertEqual(ports(), [445], "a command with no host on its line is read before exit")
            os.write(fd, b"nmap -sV 10.10.10.5\r")  # a host on the line: the hook reads it at once
            pump(2)
            self.assertEqual(ports(), [22, 80, 445])
            os.write(fd, b"evil\r")                 # forged markers in a target's output
            pump(4)
            os.write(fd, b"nmap -p22 10.10.10.5\r")
            pump(2)
            os.write(fd, b"nmap 8.8.8.8\r")         # out of scope: blocked, never runs
            pump(2)
            os.write(fd, b"exit\r")
            pump(4)
        finally:                                    # a failed check must not leave the capture running
            for _ in range(50):
                try:
                    if os.waitpid(pid, os.WNOHANG)[0]:
                        break
                except ChildProcessError:
                    break
                time.sleep(0.1)
            else:
                os.kill(pid, 9)
                os.waitpid(pid, 0)
            os.close(fd)
        out = b"".join(buf).decode("utf-8", "replace")
        self.assertIn("BLOCKED", out)
        self.assertNotIn("hook did not load", out)
        cmds = [c["cmd"] for c in sb.state()["commands"]]
        self.assertEqual(cmds, ["box1scan", "nmap -sV 10.10.10.5", "evil", "nmap -p22 10.10.10.5"],
                         "a forged marker adds no command, and a forged bracket hides none")
        self.assertIn(3306, ports(), "the forging command's own output is still read")

    def test_bash(self):
        self.drive("/bin/bash")

    @unittest.skipUnless(shutil.which("zsh"), "zsh is not installed")
    def test_zsh(self):
        self.drive(shutil.which("zsh"))


if __name__ == "__main__":
    unittest.main()
