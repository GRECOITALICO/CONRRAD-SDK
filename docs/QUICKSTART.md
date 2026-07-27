# Quick Start

```bash
pip install conrrad-sdk
conrrad new hello
cd hello
conrrad run
```

Minimal API:
```python
from conrrad import Agent
print(Agent().run("Analyze inventory and propose next action."))
```

