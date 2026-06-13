"""
Test module for edit_file tool demonstration.
This file contains some basic functions and TODOs.
"""

def greet(name: str) -> str:
    """Return a greeting message."""
    return f"🐱 Meow~ Hello, {name}!!!"


def add(a: int, b: int) -> int:
    """Add two integers and return the result."""
    # TODO: add input validation
    return a + b


def multiply(a: int, b: int) -> int:
    """Multiply two integers."""
    if not isinstance(a, int) or not isinstance(b, int):
        raise TypeError("Both arguments must be integers")
    return a * b


def main():
    """Main entry point."""
    print(greet("World"))
    print(f"1 + 2 = {add(1, 2)}")
    print(f"3 × 4 = {multiply(3, 4)}")


if __name__ == "__main__":
    main()
