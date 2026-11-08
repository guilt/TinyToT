# 13 — Security and Hardening

TinyToT is a local inference server that can execute tools. From 0.6.0 it ships
**closed by default**: it binds to loopback, refuses to expose itself without a
token, disables shell execution, and rejects oversized request bodies. This page
documents every knob and the residual risks you should understand before
exposing the server beyond your machine.

This release closes
[GHSA-2f6r-9rrh-wvq9](https://github.com/guilt/TinyToT/security/advisories/GHSA-2f6r-9rrh-wvq9)
(unauthenticated remote code execution through `shell_run`).

---

## Default posture

| Control | Default | How to change |
|---|---|---|
| Bind address | `127.0.0.1` (loopback only) | `TINYTOT_HOST_ADDR`, or `--host 0.0.0.0` **plus** a token |
| Authentication | Token required for non-loopback clients | `TINYTOT_API_TOKEN` |
| Shell tool | Disabled | `TINYTOT_ENABLE_SHELL=1` |
| Shell allowlist | Small fixed set of binaries | `TINYTOT_SHELL_ALLOWLIST` |
| Filesystem scope | Whole filesystem (legacy behaviour) | `TINYTOT_FILE_ROOT` |
| Private-network fetches | Blocked | `TINYTOT_ALLOW_PRIVATE_URLS=1` |
| Maximum request body | 32 MiB | `TINYTOT_MAX_REQUEST_BYTES` |
| Log level | `INFO` | `TINYTOT_LOG_LEVEL` |

The built-in startup guard refuses to start on a non-loopback host when
`TINYTOT_API_TOKEN` is unset:

```text
Refusing to bind to 0.0.0.0 without authentication.
Set TINYTOT_API_TOKEN or use --host 127.0.0.1.
```

---

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `TINYTOT_HOST_ADDR` | `127.0.0.1` | Default bind address used when `--host` is not supplied. Overridden by `--host`. |
| `TINYTOT_API_TOKEN` | *(unset)* | Bearer token required on `/api/agent`, `/api/agent/tool`, `/api/agent/learn`, `/v1/chat/completions`, `/api/reload`, and `/api/quit`. When unset, only loopback clients are allowed. |
| `TINYTOT_MAX_REQUEST_BYTES` | `33554432` (32 MiB) | Maximum request body size. `0` disables the limit. Bodies over the limit receive `413` with a JSON error. |
| `TINYTOT_ENABLE_SHELL` | *(unset)* | Set to `1`, `true`, `yes`, or `on` to enable `shell_run`. |
| `TINYTOT_SHELL_ALLOWLIST` | see below | Comma- or whitespace-separated executable names that `shell_run` may invoke. Replaces the default list. |
| `TINYTOT_FILE_ROOT` | *(unset)* | When set, `file_explore` resolves paths (including symlinks) and rejects anything outside this directory. |
| `TINYTOT_ALLOW_PRIVATE_URLS` | *(unset)* | Set to `1` to allow `web_fetch` / remote `document_extract` to reach loopback, private, link-local, and reserved addresses. |
| `TINYTOT_LOG_LEVEL` | `INFO` | Standard logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`). |
| `PORT` | `11434` | Server port (also settable with `--port`). |

The default shell allowlist is:
`python`, `python3`, `py`, `pip`, `pip3`, `pytest`, `ruff`, `git`, `echo`,
`ls`, `cat`, `pwd`, `find`, `grep`, `rg`, `wc`, `head`, `tail`, `date`.

---

## Exposing the server over the network

The server is local-only unless you opt in. To expose it, set a strong token and
bind explicitly:

```bash
export TINYTOT_API_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
tinytot --host 0.0.0.0 --port 11434
```

You can also make the bind address persistent with `TINYTOT_HOST_ADDR`
(`--host` still wins on the command line):

```bash
TINYTOT_HOST_ADDR=0.0.0.0 tinytot
```

Every authenticated request must include the token:

```bash
curl http://TARGET:11434/api/generate \
  -H "Authorization: Bearer $TINYTOT_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model":"tinytot","prompt":"What is the capital of France?","stream":false}'
```

Authentication uses a constant-time comparison and never logs the token. When a
token is configured it is required on **all** tool-invoking and administrative
routes, regardless of the client's address.

> **Reverse proxies:** if you place TinyToT behind a proxy, requests arrive from
> loopback. Set `TINYTOT_API_TOKEN` anyway; otherwise the loopback allowance
> applies to proxied traffic.

---

## Request size limits

Long-context prompts are first-class, so the default limit is intentionally
generous: **32 MiB**, roughly several million tokens of JSON body. Override it
when you need more (or to tighten it):

```bash
TINYTOT_MAX_REQUEST_BYTES=134217728 tinytot   # 128 MiB
TINYTOT_MAX_REQUEST_BYTES=0 tinytot           # disable the limit (not recommended)
```

The limit is enforced against `Content-Length` and while streaming the body, so
chunked requests cannot bypass it. Rejections are logged as
`request_too_large` and return:

```json
{"detail": "request body too large (max 33554432 bytes)"}
```

---

## Shell execution

`shell_run` is **off by default**. Enable it only on hosts where you trust every
authenticated caller:

```bash
TINYTOT_ENABLE_SHELL=1 tinytot
```

When enabled:

- The command is parsed with `shlex` and executed as an **argv list** with
  `shell=False`; shell metacharacters are not interpreted.
- The executable must be a **bare name** (no paths) and must appear in the
  allowlist. Deny-by-default, not a blocklist.
- `echo` is handled natively for cross-platform use and is still subject to the
  allowlist.
- Commands time out after 30 seconds (capped at 120).
- Interpreters such as `python` are intentionally allowlisted for developer
  workflows. Enabling the shell tool therefore still grants code execution to
  authenticated callers; the token is the security boundary.

Restrict it further, for example to read-only inspection:

```bash
TINYTOT_ENABLE_SHELL=1 \
TINYTOT_SHELL_ALLOWLIST="git,ls,cat,grep,rg" \
tinytot
```

Denied calls are logged as `tool_denied` and return a plain-text error such as
`[shell_run] command not allowlisted: 'sh'`.

---

## Filesystem access

`file_explore` can list, read, search, and stat files. To confine it to a
workspace:

```bash
TINYTOT_FILE_ROOT=/srv/tinytot-workspace tinytot
```

Paths are resolved (following symlinks) before the containment check, so `..`
and symlink escapes are rejected with
`[file_explore] path escapes configured root (TINYTOT_FILE_ROOT)`.

The built-in deny-list for obvious secret filenames (`.env`, `.ssh`, private
keys, cloud credential files) remains a best-effort convenience, **not** a
security boundary. Use `TINYTOT_FILE_ROOT` and OS-level permissions instead.

---

## Outbound fetches (SSRF)

`web_fetch` and remote `document_extract` accept only `http` and `https`, reject
embedded credentials, and refuse loopback, private, link-local, multicast,
reserved, and unspecified IP literals plus `localhost` and
`metadata.google.internal`.

```bash
TINYTOT_ALLOW_PRIVATE_URLS=1 tinytot   # opt in to local/intranet fetches
```

Residual risks remain: hostnames that resolve to private addresses (DNS
rebinding) and HTTP redirects to internal hosts are not fully resolved at the
socket layer. Do not run TinyToT on an untrusted network while the web tools are
reachable by untrusted callers.

---

## Security logging

Security-relevant events are emitted on the `tinytot.security` logger:

| Event | Level | Fields |
|---|---|---|
| `auth_failed` | WARNING | client, path, reason |
| `tool_denied` | WARNING | client, tool |
| `request_too_large` | WARNING | client, path, limit |
| `startup_refused` | WARNING | host, reason |

Successful tool invocations are logged at `INFO` as `tool_run` with the client
and tool name. Request bodies, prompts, tool arguments, and tokens are never
logged.

```bash
TINYTOT_LOG_LEVEL=DEBUG tinytot
```

---

## Deployment checklist

- [ ] Keep the default `127.0.0.1` bind unless remote access is required.
- [ ] Set a random `TINYTOT_API_TOKEN` before using `--host 0.0.0.0`.
- [ ] Leave `TINYTOT_ENABLE_SHELL` unset unless shell execution is needed.
- [ ] Restrict `TINYTOT_SHELL_ALLOWLIST` to the binaries you actually use.
- [ ] Set `TINYTOT_FILE_ROOT` to a dedicated workspace.
- [ ] Keep `TINYTOT_ALLOW_PRIVATE_URLS` unset on shared networks.
- [ ] Choose `TINYTOT_MAX_REQUEST_BYTES` based on your longest expected context.
- [ ] Run the server as an unprivileged user with OS-level filesystem limits.
- [ ] Monitor the `tinytot.security` logger.
