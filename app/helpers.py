def parse_traceback(traceback):
    """
    helper function that parses the traceback from stdout of subprocess.run and return line that is important to user
    return non-empty lines that mention "error" or entire traceback if none found
    """
    lines = traceback.split('\n')
    lines = list(filter(lambda line: len(line) > 0 and 'error' in line.lower(), lines))
    if(len(lines) > 0):
        return '\n'.join(lines)
    else:
        return traceback

def parse_response(inp):
    """
    Replace double quotes with single quotes. 
    If wrapped in single quotes (or otherwise e.g. wrapped in inconsistent quotes), return unchanged.
    """
    # case: user inputs float w/ zero or many trailing 0s
    if(is_number(inp)):
        return float(inp)

    # case: user inputs string wrapped in double quotes
    if inp[0]=='"' and inp[-1]=='"':
        return "'" + inp[1:-1] + "'"
    return inp

def is_number(input):
  try:
    num = float(input)
  except ValueError:
    return False
  return True