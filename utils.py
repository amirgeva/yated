

class ExitException(Exception):
    pass


def count_leading_spaces(s):
    n=0
    for c in s:
        if c!=' ':
            break
        n+=1
    return n