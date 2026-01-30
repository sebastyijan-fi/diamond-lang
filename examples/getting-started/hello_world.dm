# Diamond Hello World example
# This minimal program demonstrates module imports, capability manifests,
# and writing output to the console.

import std/io requires { Console }

func main() -> Unit:
    Console.write_line("Hello, Diamond <> world!")

    # Return explicitly for clarity even though Unit is implicit.
    return ()
