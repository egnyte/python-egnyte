## Changelog

### Unreleased

* Fixed `cmd_test`. [PR #28](https://github.com/egnyte/python-egnyte/pull/28)

Thanks to [@cobyiv](https://github.com/cobyiv) for their contribution!

### 1.0.0 beta 1

* Drop Python 2 support (**breaking change**) [PR #26](https://github.com/egnyte/python-egnyte/pull/26)
* Revamped `egnyte.resources.Search` to use v2 API. [PR #23](https://github.com/egnyte/python-egnyte/pull/23)
* HTTP requests will be retried thrice on connection and timeout errors before giving up. [PR #22](https://github.com/egnyte/python-egnyte/pull/22)
* Get files versions information. [PR #11](https://github.com/egnyte/python-egnyte/pull/11)
* Fixed `get_permissions` from querying for users if groups is set. Now queries for groups if group is set. [PR #10](https://github.com/egnyte/python-egnyte/pull/10)
* Fixed `egnyte.base.get_access_token`. [PR #20](https://github.com/egnyte/python-egnyte/pull/20)

Thanks to [@jgvilly](https://github.com/jgvilly), [@vijayendra](https://github.com/vijayendra) and [@raees-khan](https://github.com/raees-khan) for their contributions!

### < 1.0.0

Please see the descriptions in [Github Releases's](https://github.com/egnyte/python-egnyte/releases).