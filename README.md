# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/fetchai/uAgents/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                             |    Stmts |     Miss |   Cover |   Missing |
|--------------------------------- | -------: | -------: | ------: | --------: |
| src/uagents/agent.py             |      521 |      205 |     61% |106-117, 129, 174-176, 196, 334, 401-405, 431, 438, 450-452, 460-470, 484, 560-584, 601-608, 638, 658, 688, 698, 708, 724, 734, 746, 794, 804-806, 821-831, 868, 913, 929-932, 978-983, 1009, 1011, 1021, 1032, 1041-1058, 1087, 1098-1116, 1122-1127, 1133-1137, 1143, 1147-1156, 1160-1161, 1168-1178, 1182-1189, 1193-1211, 1219-1222, 1231, 1293-1302, 1311-1319, 1326, 1328, 1330, 1417-1425, 1450, 1488, 1494-1507, 1511-1534, 1538-1541 |
| src/uagents/asgi.py              |      178 |       25 |     86% |29-37, 71, 92-93, 173-193, 221-224, 283, 291-292, 394-398 |
| src/uagents/communication.py     |      111 |       34 |     69% |135-136, 140, 153, 187, 219-266, 296, 334 |
| src/uagents/config.py            |       75 |        2 |     97% |   91, 127 |
| src/uagents/context.py           |      182 |       33 |     82% |301, 305, 329, 338-341, 349-368, 377-401, 487-491, 683-686, 744 |
| src/uagents/dispatch.py          |       61 |        2 |     97% |    43, 90 |
| src/uagents/mailbox.py           |      156 |       99 |     37% |98-142, 161-176, 194-209, 229-231, 235-265, 275-303, 312-329, 333-368 |
| src/uagents/network.py           |      303 |      116 |     62% |59, 67-68, 118, 128, 142-153, 183, 220-231, 250, 252-255, 288, 330-333, 353-375, 387, 399, 411, 474, 531, 568, 574, 577, 632, 648-651, 673, 676, 704, 706-709, 712-713, 743-750, 762-767, 781-785, 843-844, 897-964, 980-993, 1015 |
| src/uagents/protocol.py          |      142 |       14 |     90% |187, 200, 202, 210, 255, 282-286, 306, 333, 342, 435 |
| src/uagents/query.py             |       13 |       13 |      0% |      3-45 |
| src/uagents/registration.py      |      297 |       86 |     71% |72, 101-102, 154, 176, 179-186, 189-208, 243, 251, 259, 267, 295-307, 338-345, 408, 416, 424, 432, 459-470, 493-497, 516, 531-562, 566-569, 599-601, 605-629 |
| src/uagents/resolver.py          |      122 |       69 |     43% |54-58, 73-80, 94-106, 154-162, 185-203, 233-270, 283-284, 312-317, 344, 348 |
| src/uagents/setup.py             |       19 |       19 |      0% |      3-37 |
| src/uagents/types.py             |      126 |        1 |     99% |        65 |
| src/uagents/utils.py             |       21 |        4 |     81% | 34, 44-46 |
| src/uagents/wallet\_messaging.py |       55 |       55 |      0% |      1-84 |
|                        **TOTAL** | **2382** |  **777** | **67%** |           |


## Setup coverage badge

Below are examples of the badges you can use in your main branch `README` file.

### Direct image

[![Coverage badge](https://raw.githubusercontent.com/fetchai/uAgents/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/fetchai/uAgents/blob/python-coverage-comment-action-data/htmlcov/index.html)

This is the one to use if your repository is private or if you don't want to customize anything.

### [Shields.io](https://shields.io) Json Endpoint

[![Coverage badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/fetchai/uAgents/python-coverage-comment-action-data/endpoint.json)](https://htmlpreview.github.io/?https://github.com/fetchai/uAgents/blob/python-coverage-comment-action-data/htmlcov/index.html)

Using this one will allow you to [customize](https://shields.io/endpoint) the look of your badge.
It won't work with private repositories. It won't be refreshed more than once per five minutes.

### [Shields.io](https://shields.io) Dynamic Badge

[![Coverage badge](https://img.shields.io/badge/dynamic/json?color=brightgreen&label=coverage&query=%24.message&url=https%3A%2F%2Fraw.githubusercontent.com%2Ffetchai%2FuAgents%2Fpython-coverage-comment-action-data%2Fendpoint.json)](https://htmlpreview.github.io/?https://github.com/fetchai/uAgents/blob/python-coverage-comment-action-data/htmlcov/index.html)

This one will always be the same color. It won't work for private repos. I'm not even sure why we included it.

## What is that?

This branch is part of the
[python-coverage-comment-action](https://github.com/marketplace/actions/python-coverage-comment)
GitHub Action. All the files in this branch are automatically generated and may be
overwritten at any moment.