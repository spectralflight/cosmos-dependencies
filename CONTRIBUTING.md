# Contributing

## Wheels

Unfortunately, we cannot accept externally built wheels. Forking the repository will allow you to host your own index.

To copy over existing wheels:

```shell
gh release download --repo nvidia-cosmos/cosmos-dependencies v$(uv version --short) -D tmp/assets --pattern '*.whl'
gh release upload --repo <username>/cosmos-dependencies v$(uv version --short) tmp/assets/*.whl
```

## Code

Run linting/formatting:

```shell
just lint
```

Run testing:

```shell
just test
```

Check licenses:

```shell
just license
```
