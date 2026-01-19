Every project in the [Some Repo repo](https://github.com/some-user/some-repo) should be tested.
In this section, we specify the set of tests specific to Rot13.
In order to keep things simple, we split up the testing as follows:

- Rot13 Valid Tests
- Rot13 Invalid Tests

### Rot13 Valid Tests

| Description | Input | Output |
| ----------- | ----- | ------ |
| Sample Input Lower Case | "the quick brown fox jumped over the lazy dog" | "gur dhvpx oebja sbk whzcrq bire gur ynml qbt" |
| Sample Input Upper Case | "THE QUICK BROWN FOX JUMPED OVER THE LAZY DOG" | "GUR DHVPX OEBJA SBK WHZCRQ BIRE GUR YNML QBT" |

### Rot13 Invalid Tests

| Description | Input |
| ----------- | ----- |
| No Input |  |
| Empty Input | "" |

All of these tests should output the following:

```
Usage: please provide a string to encrypt
```
