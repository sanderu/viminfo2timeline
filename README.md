# viminfo2timeline

Creates a body-file to be used for Sleuthkits mactime.

## Usage:

    python3 viminfo2timeline.py <VIMINFO-FILENAME> > /tmp/viminfo.body

## Viminfo file:

Most of the files parts are in the newest to oldest order - only changes to a file (marked with '+') are oldest to newest.
To ensure to get the output order right, I have chosen to prepend a 4-digit number which when body-file is being used by mactime causes the output to be in "correct" order making it easier to read what happened.

File Changes that happened before the last change may be from earlier time, as change only has 1 timestamp. Also changes (marked with '+') are listed oldest to newest. Rest of viminfo file is newest to oldest.

The script parses viminfo files for:

- searches
- most used commands
- command history
- registers
- file marks/jumplists/changes

## Example (History of marks within files):

    > /tmp/test.txt				<- relative/full path to file opened/edited in vim
       *   1656360317  0        <- time in epoch
       "   6   3				<- last cursor position before file was exited (line 6, char pos 3)
       ^   6   4				<- last Insert-mode cursor position (line 6, char pos 4)
       .   6   3				<- last change occurred on (line 6, char pos 3)
       +   6   21				<- earlier 1st change (line 6, char pos 21) - change at unknown time
       +   2   1				<- earlier 2nd change (line 2, char pos 1) - change at unknown time
       +   3   1				<- earlier 3rd change (line 3, char pos 1) - change at unknown time
       +   4   1				<- earlier 4th change (line 4, char pos 1) - change at unknown time
       +   6   3				<- latest 5th change (line 6, char pos 3) - change at 1656360317
