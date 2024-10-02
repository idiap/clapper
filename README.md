# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/idiap/clapper/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                        |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|---------------------------- | -------: | -------: | -------: | -------: | ------: | --------: |
| src/clapper/\_\_init\_\_.py |        0 |        0 |        0 |        0 |    100% |           |
| src/clapper/click.py        |      281 |        0 |      161 |        7 |     98% |227->231, 254->257, 421->425, 713->712, 726->723, 810->800, 820->800 |
| src/clapper/config.py       |       82 |        0 |       28 |        0 |    100% |           |
| src/clapper/logging.py      |       29 |        0 |        6 |        2 |     94% |83->93, 97->106 |
| src/clapper/rc.py           |       96 |        0 |       40 |        2 |     99% |125->139, 169->184 |
|                   **TOTAL** |  **488** |    **0** |  **235** |   **11** | **98%** |           |


## Setup coverage badge

Below are examples of the badges you can use in your main branch `README` file.

### Direct image

[![Coverage badge](https://raw.githubusercontent.com/idiap/clapper/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/idiap/clapper/blob/python-coverage-comment-action-data/htmlcov/index.html)

This is the one to use if your repository is private or if you don't want to customize anything.

### [Shields.io](https://shields.io) Json Endpoint

[![Coverage badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/idiap/clapper/python-coverage-comment-action-data/endpoint.json)](https://htmlpreview.github.io/?https://github.com/idiap/clapper/blob/python-coverage-comment-action-data/htmlcov/index.html)

Using this one will allow you to [customize](https://shields.io/endpoint) the look of your badge.
It won't work with private repositories. It won't be refreshed more than once per five minutes.

### [Shields.io](https://shields.io) Dynamic Badge

[![Coverage badge](https://img.shields.io/badge/dynamic/json?color=brightgreen&label=coverage&query=%24.message&url=https%3A%2F%2Fraw.githubusercontent.com%2Fidiap%2Fclapper%2Fpython-coverage-comment-action-data%2Fendpoint.json)](https://htmlpreview.github.io/?https://github.com/idiap/clapper/blob/python-coverage-comment-action-data/htmlcov/index.html)

This one will always be the same color. It won't work for private repos. I'm not even sure why we included it.

## What is that?

This branch is part of the
[python-coverage-comment-action](https://github.com/marketplace/actions/python-coverage-comment)
GitHub Action. All the files in this branch are automatically generated and may be
overwritten at any moment.