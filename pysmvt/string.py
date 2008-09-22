
# capwords to underscore notation
# from : http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/66009
def camelToUnderscore(x): 
    return re.sub(r'(?<=[a-z])[A-Z]|(?<!^)[A-Z](?=[a-z])', r"_\g<0>", x).lower()