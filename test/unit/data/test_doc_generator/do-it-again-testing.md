Every project in the [Some Repo repo](https://github.com/some-user/some-repo) should be tested.
In this section, we specify the set of tests specific to Do It Again.
In order to keep things simple, we split up the testing as follows:

- Valid Do It Again Tests
- Invalid Do It Again Tests

### Valid Do It Again Tests

| Description | Input | Output |
| ----------- | ----- | ------ |
| Input1 | "123" | "234" |
| Input2 | "234" | "345" |

This test suite is repeated 3 times to ensure that the results are consistent.

### Invalid Do It Again Tests

| Description | Input | Output |
| ----------- | ----- | ------ |
| No Input |  | "No input" |
| Empty Input | "" | "Empty input" |
