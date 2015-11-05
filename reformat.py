from json import dump
from pprint import pprint


OPENTAG = '<'
CLOSETAG = '>'
QUOTE = '"'
PASSAGE_TAG = "tw-passagedata"
MULTIPLE_TAG_ERROR = "Found multiple '{}' tags, not currently supported"

def format_html(filepath):
    output_file = filepath.replace('.xml','_edited.xml')
    with open(filepath) as in_file, open(output_file, 'w') as out_file:
        while True:
            # Get next line
            try:
                line = next(in_file)
            except StopIteration:
                break

            while True:
                if not line.startswith(OPENTAG):
                    end_index = line.find(OPENTAG)
                    if end_index == -1:
                        out_file.write(line)
                        # Used up all the line
                        break
                    else:
                        out_file.write(line[:end_index] + '\n')
                        line = line[end_index:]

                if not line:
                    break

                close_index = line.find(CLOSETAG)
                quote_index = line.find(QUOTE)
                if quote_index != -1:
                    in_quotes = True
                    
                    while quote_index < close_index:
                        quote_index = next_quote(line, quote_index)
                        if quote_index > close_index:
                            # Find the next CLOSETAG outside quotes
                            close_index = (quote_index + 
                                           line[quote_index:].find(CLOSETAG))
                        # Find the next quote that opens a line
                        quote_index = next_quote(line, quote_index)

                        if close_index == -1:
                            raise ValueError("Can't parse close tag in {}".
                                             format(line))
                out_file.write(line[:close_index + 1] + '\n')
                line = line[close_index + 1:]

def next_quote(line, index):
    """Return the index of the next quote

    Catches a -1 result, not catching this causes infinite loops.
    Add 1 as that's needed for all future searches."""
    
    index += line[index:].find(QUOTE) if line[index:].find(QUOTE) != -1 else 0
    return index + 1

def read_as_json(filepath):
    """Return a dictionary of data from the parsed file at filepath"""

    data = {}
    with open(filepath) as f:
        for line in f:
            if line.startswith('</'):
                # Closing tag, nothing to see here.
                continue
        
            if line.startswith('<'):
                parse_tag(line, data)
                continue

            data[PASSAGE_TAG][-1]['text'] += line
    return data

def separate_tags(tag):
    """Takes a tag string and returns the key name and a dictof tag values."""

    tag = tag.strip().strip('<>')
    tagname, pairs = tag.split(' ', 1)

    tagdata = {}

    # Makes each loop the same ie always seeking a space character
    pairs += ' '
    while pairs:
        space_index = pairs.find(' ')
        quote_index = pairs.find('"')
        quote_index = 1 + pairs[quote_index + 1:].find('"')
        
        if quote_index == -1:
            quote_index = None

        if space_index < quote_index:
            space_index = quote_index + pairs[quote_index:].find(' ')

        # Add keyvalue pair
        key, value = pairs[:space_index].split('=')
        tagdata[key] = value.strip('"')

        pairs = pairs[space_index + 1:]


    return tagname, tagdata
        
    
    
def parse_tag(tag, data):
    """Parse Twine tag into data dictionary which is modified in place.
    
    The tag name is the key, it's value is a dictionary of the tag's key value
    pairs. Passage tags are stored in a list, """

    tagname, tagdata = separate_tags(tag)
    if tagname == PASSAGE_TAG:
        try:
            data[tagname].append(tagdata)
        except KeyError:
            data[tagname] = [tagdata]
        data[tagname][-1]['text'] = ''
    else:
        if tagname in data:
            raise ValueError(MULTIPLE_TAG_ERROR.format(tagname))
        data[tagname] = tagdata
        

# Main
#path = r'C:\Users\ntreanor\Documents\data.xml'
#format_html(path)
data = read_as_json("test.html")
pprint(data)
