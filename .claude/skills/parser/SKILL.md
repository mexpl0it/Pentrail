---
name: parser
description: Teaching pentrail to read a tool's output - where analyze() turns one command's output into ports, web paths, hostnames, leads, credentials and facts, how apply_findings() keeps only what is in scope and credits the command, and how to test a parser with a stand-in tool. Use when a tool's results do not show up in pentrail hosts/next/enum.md, or when adding support for a new tool's output format.
---

# Reading a tool's output

## The path of one command's output

```
capture / shot / ingest
  -> _cmd_context(cmd, scope)   program (prog_of), target hosts, URL template, Host header
  -> analyze(text, ctx)         F = {"ports", "web", "names", "hosts", "vulns", "creds", "facts"}
  -> apply_findings(...)        keep what is in scope, credit the command (add_command), count news
  -> save_state -> sync_docs    enum.md, phase docs, notes
```

`analyze()` walks the output line by line; `ctx["prog"]` lets a parser apply only to its
tool (`if prog in ("rustscan", "naabu")`). Hosts it cannot read from the output come from
the command line's targets in `apply_findings`.

## Adding a format

1. Get a real, harmless sample of the tool's output (from the user, or the tool's docs).
   Strip anything that identifies a client.
2. Add a compiled regex next to the others (`NMAP_PORT`, `URL_ANY`, ...), and the branch in
   `analyze()`, keyed on `prog` when the line format is not unique to the tool.
3. Append the right tuple shape (see existing appends): ports
   `(host, port, proto, service, version)`, names `(name, ip)`, hosts `(ip, name, os)`.
4. A tool that writes files: make sure `ingest_file()` / `_nmap_xml_as_text()` style
   conversion handles its file format, and that it lands in `1-enum/scans/`.
5. Tools that count as one for `seen` (dirbusters, netexec/crackmapexec): `TOOL_GROUPS`.

## Test it

A stand-in tool in the sandbox that prints the sample (`Sandbox` in tests, or the
`sandbox-test` skill), then:

```python
sb.run("shot", "-q", "-l", "x", "--", "mytool", "10.10.10.5", check=True, cwd=sb.project)
self.assertEqual(sorted(p["port"] for h in sb.state()["hosts"] for p in h["ports"]), [...])
```

Also check a line from a host **outside** the scope is dropped (counted as skipped), and that
credentials in the output never reach JSON (`pentrail hosts --json`).
