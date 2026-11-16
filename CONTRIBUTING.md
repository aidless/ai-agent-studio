# Contributing

Thanks for your interest in improving this repository.

## Getting set up

```bash
git clone https://github.com/aidless/ai-agent-studio.git
cd ai-agent-studio
pip install -r requirements-dev.txt
```

## Verifying your change

```bash
make check
```

`make check` is the same offline gate as the CI workflow: hash negative probe,
eval cases, the eval selftest, and pytest. It does not call DeepSeek and does
not download an embedding model. Please run it before opening a pull request.

## Pull requests

- One logical change per pull request.
- Explain what breaks or is missing without the change.
- State how you verified it, and paste the command output.
- Keep unrelated reformatting out of the diff.

## Security

Do not open a public issue for a security problem. Use the private channel described
in [SECURITY.md](SECURITY.md).

## Code of conduct

Participation is governed by [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
