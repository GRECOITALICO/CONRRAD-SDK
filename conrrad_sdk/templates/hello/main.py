#!/usr/bin/env python3
"""Hello project entrypoint — edit the task string to experiment."""

from conrrad import Agent


def main() -> None:
    agent = Agent()
    result = agent.run("Analyze this inventory and find the cheapest supplier.")
    print(result)


if __name__ == "__main__":
    main()
