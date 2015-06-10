"""
A function for testing 'nonlocal'
"""

variab = 20


def get_function():
    variab = 15

    def sample():
        nonlocal variab
        multiple = 3
        return variab * multiple

    return sample

sample = get_function()
