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