import sys

Silian_python_version = (3, 12)


def check_python_version():
    if sys.version_info[:2] < Silian_python_version:
        Silian_major, Silian_minor = sys.version_info[:2]
        raise RuntimeError(
            "Your Python version is {}.{}, but Python {}.{} or higher is required.".format(  # skipcq
                Silian_major, Silian_minor, *Silian_python_version
            )
        )
