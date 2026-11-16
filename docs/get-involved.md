---
layout: documentation
doctitle: Get involved
title: SirixDB - Get involved
description: Join the SirixDB community, report bugs, contribute code, and improve the documentation.
---

SirixDB is developed in the open. Whether you use the database, build tools around
it, or want to understand its internals, there are several ways to help.

## Join the conversation

Join [Discord](https://discord.gg/yC33wVpv7t) for quick questions and development
chat: get help, share what you're building, and discuss design ideas. Use the
[Discourse forum](https://sirix.discourse.group) for longer discussions that
others can return to. If you're unsure where to start, ask on Discord.

## Report bugs and request features

Open an issue in the [SirixDB issue tracker](https://github.com/sirixdb/sirix/issues).
For a bug, include the SirixDB version or commit, Java version and operating
system, storage backend and resource settings, and the smallest JSON or XML
input that reproduces the problem. Add the JSONiq/XQuery query or API calls you
ran, the expected and actual results, and the full error output or stack trace.
For a feature request, describe the use case and the behavior you need.

## Contribute code

Pull requests to [sirixdb/sirix](https://github.com/sirixdb/sirix) are welcome.
Start with the [contribution guide](https://github.com/sirixdb/sirix/blob/main/CONTRIBUTING.md)
for setup, the module map, and the development workflow. Read the
[architecture documentation](https://github.com/sirixdb/sirix/blob/main/docs/ARCHITECTURE.md)
and the [specification chapters](https://github.com/sirixdb/sirix/tree/main/spec)
for the area you want to change. The spec records intended behavior; check each
requirement's status and evidence before assuming it is implemented.

The project's testing standard is **spec first, mutation testing, and explorative
testing**: write behavior, invariants, and error cases, derive tests before
implementation, mutation-test changed logic, and explore beyond the happy path.
The contribution guide and [verification guide](https://github.com/sirixdb/sirix/blob/main/docs/VERIFICATION.md)
explain the required evidence. Browse issues labeled
[good first issue](https://github.com/sirixdb/sirix/labels/good%20first%20issue)
for starting points. For larger changes, ask on Discord and discuss the proposal
in an issue before starting work.

### Help with tools and clients

You can also contribute to the tools around the database. Read each project's
README and existing issues before choosing a change:

- [Python client](https://github.com/sirixdb/sirix-python-client) and
  [TypeScript client](https://github.com/sirixdb/sirix-typescript-client) — client libraries in their own repositories.
- [Kotlin API](https://github.com/sirixdb/sirix/tree/main/bundles/sirix-kotlin-api) — the coroutine-based API in the main repository.
- [MCP server](https://github.com/sirixdb/sirix/tree/main/bundles/sirix-mcp) — Model Context Protocol integration in the main repository.

## Improve the documentation

This website lives in [sirixdb/sirixdb.github.io](https://github.com/sirixdb/sirixdb.github.io).
Documentation pages are Markdown files under
[`docs/`](https://github.com/sirixdb/sirixdb.github.io/tree/master/docs).
Fix unclear explanations, add reproducible examples, or document a workflow that
helped you. To add a page, use the `documentation` layout and add its link to the
sidebar in `_layouts/documentation.html`. The shared header and footer live in
`_includes/`. Follow the [website README](https://github.com/sirixdb/sirixdb.github.io/blob/master/README.md)
to preview your changes and run the site's checks before opening a pull request.
