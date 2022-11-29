"""Here lie the helper functions"""


def mutstr(base: str, ind: int, repr: str):
    if len(base) <= ind:
        raise ValueError(f"Asked to change the character nr. {ind} in a string of only {base.__len__()} chars.")
    return base[:ind] + repr + base[ind+1:]