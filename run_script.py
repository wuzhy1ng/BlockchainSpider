import argparse
import importlib
import os
import sys


def main():
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_root)

    parser = argparse.ArgumentParser(description="Run a function from the scripts module with arguments.")
    parser.add_argument("-m", "--module", required=True, help="The function to call in the scripts module.")
    parser.add_argument("-a", "--args", action="append",
                        help="Key-value pairs for function arguments (e.g., -a key=value).")
    args = parser.parse_args()

    # lazy import functions
    try:
        module = importlib.import_module("scripts")
    except ModuleNotFoundError:
        print("Module 'scripts' not found.")
        sys.exit(1)

    # load functions
    try:
        func = getattr(module, args.module)
    except AttributeError:
        print(f"Function '{args.module}' not found in module 'scripts'.")
        sys.exit(1)

    # parse arguments
    kwargs = {}
    if args.args:
        for pair in args.args:
            if "=" not in pair:
                print(f"Invalid key-value pair: {pair}. Use -a key=value format.")
                sys.exit(1)
            key, value = pair.split("=", 1)
            kwargs[key] = value

    # call functions
    try:
        func(**kwargs)
    except TypeError as e:
        print(f"Error calling function '{args.module}': {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
