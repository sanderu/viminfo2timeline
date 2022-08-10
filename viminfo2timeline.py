#!/usr/bin/python3

# 2022 - Jesper Sander Lindgren

# viminfo2timeline
#
# Usage:
#   python3 viminfo2timeline.py <FILENAME> > /tmp/viminfo.body
# 
# Creates a body-file to be used for Sleuthkits mactime.

# Modules needed:
from sys import argv as sysargv, exit as sysexit
from re import match as rematch, compile as recompile

# Command-Line History - shows the most used commands and the last used date/time
# |2,0,1655640853,,"wq"
cli_history = recompile(r"\|2,0,")

# Search History
#|2,1,1656165977,47,"test"
search_history = recompile(r"\|2,1,")

# Registers - shows the type editing being done (2nd number):
# 0 = Char          - in number of lines
# 1 = Line          - in number of lines
# 2 = Visual block  - lines * chars
# |3,0,6,1,1,0,1655566954,"1"
registers = recompile(r"\|3,")

# File Marks
# Jumplist
# Both use same "syntax"
# If linenumber = 1 and columnnumber = 0:
#   indication of file opening
# Second number indicator:
#                  39 = cursor position
#   between 48 and 57 = indication of file closing
# |4,39,3,9,1656161664,"~/check_vulns.conf"
filemark_jump = recompile(r"\|4,")

# History of marks within files
# This describes filename, epochtime for last edit
# Also line/char pos for where cursor was last upon exit insert-mode, last insert, last change (all can be different)
# And also a list of different line/char pos where cursor was when changes were made (if delete: line {} char pos 0/insert: line {} char pos {} = last insert)
editfile = recompile(r"> .*")
editspattern = recompile(r"\\t([\.\^\"\+])\\t(\d+)\\t(\d+)")


def read_viminfo(filename):
    ''' Read file into a list '''
    try:
        with open(filename, 'r') as viminfo_file:
            viminfo = [line.rstrip() for line in viminfo_file]
            return viminfo
    except FileNotFoundError:
        print('You need to provide to correct filename.')
        sysexit(1)

def create_lists_of_list_for_filemarks(viminfo):
    '''
    Create list of lists for the file history-part of viminfo for easier parsing.
    Order for '+' entries are older to newest
    '''
    element = 0

    # First split list in 2 based on first occurence of '>'
    # This tells the rest of the file is file history
    for entry in viminfo:
        if rematch(editfile, entry):
            editslist = viminfo[element:]
            break
        element += 1

    # Create list of lists for each file - each '' indicates end of
    # current file history and next file begins = new list
    splitlist = [[]]
    for i in editslist:
        if not i:
            splitlist.append([])
        else:
            splitlist[-1].append(i)
    return splitlist


def print_hits(epochtime, message):
    ''' Output results in mactime format '''
    #   Remove any pipe from message as mactime is pipe-delimited
    # 0,message,0,'N/A         ',0,0,0,epoctime,epochtime,epochtime,epochtime,0
    print(0, message.replace('|',':'), 0, 'N/A         ', 0, 0, 0, epochtime, epochtime, epochtime, epochtime, 0, sep = '|')


def parse_cli_registers(viminfo):
    ''' Parse search history, command history, registers and file marks/jumplist '''
    epochtime = 0

    for entry in viminfo:
        message = ''
        if rematch(cli_history, entry):
            a, b, epochtime, c, command = entry.split(',', 4)
            message = '.viminfo - 8000 - Last time for command: {}'.format(command)
            print_hits(epochtime, message)
        elif rematch(search_history, entry):
            a, b, epochtime, direction, command = entry.split(',', 4)
            if direction == '47':
                search_direction = 'forward search (/)'
            elif direction == '63':
                search_direction = 'backward search (?)'
            else:
                search_direction = 'unknown search'
            message = '.viminfo - 5000 - Last search for: {} by using: {}'.format(command, search_direction)
            print_hits(epochtime, message)
        elif rematch(registers, entry):
            register_type = ''

            a, b, reg_name, reg_type, no_of_lines, chars, epochtime, register_content = entry.split(',', 7)
            if reg_type == '1':
                register_type = 'Line'
                size = '{} line(s)'.format(no_of_lines)
            elif reg_type == '2':
                register_type = 'Visual block'
                if int(no_of_lines) == 1:
                    line_word = 'line'
                else:
                    line_word = 'lines'
                if int(chars) == 0:
                    char_word = 'char'
                else:
                    char_word = 'chars'
                size = '{} {} * {} {}'.format(no_of_lines, line_word, int(chars)+1, char_word)
            else:
                register_type = 'Char'
                size = '{} line(s)'.format(no_of_lines)
            message = '.viminfo - 3000 - Register-name: {}. Contains type: {}. Size: {}. Content: {}'.format(reg_name, register_type, size, register_content)
            if reg_name == '36':
                reg_name = '-'
                message = '.viminfo - 4000 - Register-name: {}. Deleted text: {}'.format(reg_name, register_content)
            print_hits(epochtime, message)
        elif rematch(filemark_jump, entry):
            a, state, linenumber, chars, epochtime, filename = entry.split(',', 5)
            message = '.viminfo - 1000 - Vim cursor position on line: {}, char position: {} in file: {}'.format(linenumber, chars, filename)
            if int(state) >= 48:
                message = '.viminfo - 9000 - Indication of file write/closing: {} with cursor at line: {} column: {}'.format(filename, linenumber, chars)
            if linenumber == '1' and chars == '0':
                message = '.viminfo - 0000 - Indication of file opening: {}'.format(filename)
            print_hits(epochtime, message)


def parse_file_edits(splitlist):
    ''' Parse the list of lists regarding file history '''
    # Take each list in lists
    for element in range(len(splitlist)):
        epochtime = 0
        filename = ''
        message = ''
        add_message = ''
        no_of_elements = len(splitlist[element])
        # Parse each element
        for elementlength in range(no_of_elements):
            tmp_pos = f'{elementlength:03}'
            tag = ''
            line = 0
            char_pos = 0
            # Add more context based on number of elements in list
            if no_of_elements < 5:
                add_message = ' - File not changed.'
            elif no_of_elements == 5:
                add_message = ' - File could have been changed with paste/delete'

            # Try to split line by line to get filename, timestamp, line/cursor position
            try:
                tag, filename = splitlist[element][elementlength].split(' ', 1)
            except ValueError:
                tab,tag,line,char_pos=splitlist[element][elementlength].split('\t', 3)
                if tag == '*':
                    epochtime=line
                if tag == '"':
                    message = '.viminfo - 7999 - Cursor position on Line: {}, char pos: {} when exiting file: {}{}'.format(line, char_pos, filename, add_message)
                elif tag == '^':
                    message = '.viminfo - 7995 - Last "Insert"-mode cursor position on line: {}, char pos: {} in file: {}{}'.format(line, char_pos, filename, add_message)
                elif tag == '.':
                    message = '.viminfo - 7990 - Last change occurred on line: {}, char pos: {} in file: {}{}'.format(line, char_pos, filename, add_message)
                elif tag == '+':
                    # Last entry in file history is last edit. Else edits may be 
                    # historic and not necessarily related to same date/time edit
                    if elementlength == no_of_elements-1:
                        add_message = ' - File has been edited'
                    else:
                        add_message = ' - File has been edited, may be older edits'

                    message = '.viminfo - 7{} - Change cursor position on line: {}, char pos: {} in file: {}{}'.format(tmp_pos, line, char_pos, filename, add_message)
            else:
                pass

            if epochtime and message:
                print_hits(epochtime, message)


def main():
    ''' Main program '''
    if len(sysargv) == 1:
        print('Pls provide viminfo file to parse.')
        sysexit(1)
    else:
        filename=sysargv[1]
    viminfo = read_viminfo(filename)
    splitlist = create_lists_of_list_for_filemarks(viminfo)
    parse_cli_registers(viminfo)
    parse_file_edits(splitlist)


if __name__ == '__main__':
    main()
