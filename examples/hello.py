#!/usr/bin/env python3
"""Official CONRRAD hello world — no Docker or external services."""

from conrrad import Agent


def main() -> None:
    agent = Agent()
    result = agent.run("Analyze this inventory and find the cheapest supplier.")
    print(result)


if __name__ == "__main__":
    main()
