from json import dump
from pprint import pprint


PASSAGE_TAG = "tw-passagedata"
MULTIPLE_TAG_ERROR = "Found multiple '{}' tags, not currently supported"


def write_passage(out_file, line):
    """Check how much of line is passage data and write it to out_file
    
    Returns what remains of the truncated line"""

    end_index = line.find('<')
    if end_index == -1:
        out_file.write(line)
        # Used up all the line as plain passage data.
        return ''
    else:
        # Need a newline so that the tag is separate from the passage data.
        out_file.write(line[:end_index] + '\n')
        # Remove the section of line that hasn't been written.
        return line[end_index:]


def next_quote(line, index):
    """Return the index of the next quote

    Catches a -1 result, not catching this causes infinite loops.
    Add 1 as that's needed for all future searches."""
    
    index += line[index:].find('"') if line[index:].find('"') != -1 else 0
    return index + 1
        
        
def find_closing_tag(line):
    """Returns the index of the closing tag in line.
    
    Ensures that it doesn't return a > enclosed in quotes. 
    This is because that may just be a character in a string value."""

    close_index = line.find('>')
    quote_index = line.find('"')
    # We need to ensure > isn't enclosed in quotes
    if quote_index != -1:
        # Keep searching until we find a valid closing tag
        while quote_index < close_index:
            quote_index = next_quote(line, quote_index)
            if quote_index > close_index:
                # Find the next > after "
                close_index = (quote_index + 
                               line[quote_index:].find('>'))
            # Find the next quote that opens a keyvalue
            quote_index = next_quote(line, quote_index)

            if close_index == -1:
                raise ValueError("Can't parse close tag in {}".
                                 format(line))

    return close_index


def reformat_html(filepath):
    """Read Twine2's HTML format and write it out in a tidier format.
    
    Writes to the same directoy as filepath, just with _temp in the name.
    Returns the filepath of the resulting file."""

    output_file = filepath.replace('.html', '_temp.html')
    with open(filepath) as in_file, open(output_file, 'w') as out_file:
        for line in in_file:
            # Get next line
            #try:
                #line = next(in_file)
            #except StopIteration:
                #break

            while line:
                # If it's a passage.
                if not line.startswith('<'):
                    line = write_passage(out_file, line)
                    continue
                    
                close_index = find_closing_tag(line)
                out_file.write(line[:close_index + 1] + '\n')
                line = line[close_index + 1:]
    return output_file


def read_as_json(filepath):
    """Return a dictionary of data from the parsed file at filepath.
    
    Reads whether a line is a tag, tag closer or text from a passage.
    Close tags are ignored, tag data and passages are parsed into data."""

    data = {}
    with open(filepath) as f:
        for line in f:
            if line.startswith('</'):
                # Closing tag, nothing to see here.
                continue
        
            if line.startswith('<'):
                # New tag, parse it into data then go to the next line
                parse_tag(line, data)
                continue

            # Anything else is passage data
            # Concatenate it to the current passage node.
            data[PASSAGE_TAG][-1]['text'] += line
            
    return data


def separate_tags(tag):
    """Takes a tag string and returns the key name and a dictof tag values.
    
    Tags are strings in the format:
    <tagname key="value" key="another value">
    
    They're parsed by stripping the <>, then splitting off the tagname.
    Then the rest of the string is read and removed one by one.
    Space and " characters need to be checked to determine whether a space is
    a new keyvalue pair or part of the current value in quotation marks."""

    tagdata = {}
    tag = tag.strip().strip('<>')
    tagname, pairs = tag.split(' ', 1)

    # Makes each loop the same ie always seeking a space character
    pairs += ' '
    while pairs:
        # Find the second quotation mark
        quote_index = pairs.find('"')
        quote_index = 1 + pairs[quote_index + 1:].find('"')

        
        # If there's no quote found, just find the next space.
        if quote_index == -1:
            space_index = pairs.find(' ')
        # Otherwise find the space after the second quote
        else:
            space_index = quote_index + pairs[quote_index:].find(' ')

        # Add the keyvalue pair that's 
        key, value = pairs[:space_index].split('=')
        tagdata[key] = value.strip('"')

        pairs = pairs[space_index + 1:]

    return tagname, tagdata
        

def parse_tag(tag, data):
    """Parse Twine tag into the data dictionary which is modified in place.
    
    The tag name is the key, it's value is a dictionary of the tag's key value
    pairs. Passage tags are stored in a list, as of now no other tag should 
    be stored this way, and having multiple tags raises a ValueError."""

    tagname, tagdata = separate_tags(tag)
    if tagname == PASSAGE_TAG:
        # Create text string to be available for concatenating to later.
        tagdata['text'] = ''
        try:
            data[tagname].append(tagdata)
        except KeyError:
            data[tagname] = [tagdata]
    else:
        if tagname in data:
            raise ValueError(MULTIPLE_TAG_ERROR.format(tagname))
        data[tagname] = tagdata
        

if __name__ == "__main__":
    # Sample test
    inpath = r'Sample Data\TwineInput.html'
    outpath = r'Sample Data\FinalOutput.json'
    result = reformat_html(inpath)
    data = read_as_json(result)
    with open(outpath, 'w') as f:
        dump(data, f, indent=4)
