# Authentication

Uniac credentials belong to an account and a platform. `UNIAC_PLATFORM_URL`
selects the platform API origin for `auth login` and `auth token`, with
`https://api.uniac.ai` as the default.

## Sign-in

```text
uniac auth login [--no-browser] [--manual] [--host <host>]
```

`login` obtains a token through browser sign-in, where account creation is
also available. Sign-in requires user interaction. The CLI prints the sign-in
URL and reports the browser-launch attempt.

| Option | Effect |
|---|---|
| `--no-browser` | Print the sign-in URL without trying to open a browser. |
| `--manual` | Skip the local callback listener and prompt for the complete redirected URL. This is independent of `--no-browser`. |
| `--host <host>` | Select the website serving sign-in, overriding `UNIAC_AUTH_HOST`. |

Without `--manual`, login receives the redirect through a listener on a random
localhost port and waits up to five minutes. The default platform uses
`uniac.ai` for sign-in. Another platform requires an explicit `--host` or
`UNIAC_AUTH_HOST`; the CLI does not infer a website from the platform origin.

Successful sign-in stores the returned token in `~/.uniac/auth.json`, with
file permissions `0600`. There is one stored session per platform; signing
in replaces that platform's session and preserves the others. The CLI does
not validate the token with the platform API before storing it.

## Credential selection and renewal

`project create`, `link`, `deploy`, `status` and `auth token` use a nonempty
`UNIAC_ACCESS_TOKEN` first, otherwise the stored session for the addressed
platform. Linked `deploy` and `status` use the binding's platform origin;
`auth token` uses `UNIAC_PLATFORM_URL`, independently of the directory binding.
The override receives no local expiry check. A stored token becomes unusable
60 seconds before its recorded expiry. Without an override, missing or
expired stored credentials stop deployment before a network call.

Deployment checks the selected credential with the platform before image
work and uses that credential throughout the operation. Local selection
alone does not establish server acceptance; `auth status` and `auth token`
perform no such check.

The CLI does not refresh tokens automatically. Another `auth login` obtains
and stores the token returned by sign-in; it does not guarantee a different
token or a later expiry.

## Stored sessions

| Invocation | Result |
|---|---|
| `uniac auth status` | Print stored identities and expiry times for every platform, including expired sessions; fail when none are stored. |
| `uniac auth token` | Print the selected credential; fail when none is locally usable. |
| `uniac auth logout` | Remove all locally stored platform sessions. |

`auth status`'s `Logged in.` message means stored sessions exist; it does not
inspect `UNIAC_ACCESS_TOKEN`. Logout does not clear that variable or revoke
tokens at the platform.

`uniac auth -h` lists subcommands; each subcommand's `-h` prints its usage.
`status`, `token` and `logout` accept no flags or arguments. Help and invalid
invocations perform no authentication operation. Only `login` uses the
network.
