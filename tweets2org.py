#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Time-stamp: <2013-05-19 16:15:48 vk>

## TODO:
## * fix parts marked with «FIXXME»



## ===================================================================== ##
##  You might not want to modify anything below this line if you do not  ##
##  know, what you are doing :-)                                         ##
## ===================================================================== ##

import re
#import sys
#import os
#import time
import logging
from optparse import OptionParser

## debugging:   for setting a breakpoint:  pdb.set_trace()
import pdb

PROG_VERSION_NUMBER = u"0.1"
PROG_VERSION_DATE = u"2013-05-19"
INVOCATION_TIME = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())

USAGE = u"\n\
    " + sys.argv[0] + u" [<options>] <list of JSON files>\n\
\n\
This tool FIXXME\n\
\n\
\n\
Example usages:\n\
  " + sys.argv[0] + u" --tags=\"presentation projectA\" *.pptx\n\
      ... adds the tags \"presentation\" and \"projectA\" to all PPTX-files\n\
  " + sys.argv[0] + u" -i *\n\
      ... ask for tag(s) and add them to all files in current folder\n\
  " + sys.argv[0] + u" -r draft *report*\n\
      ... removes the tag \"draft\" from all files containing the word \"report\"\n\
\n\
\n\
:copyright: (c) 2013 by Karl Voit <tools@Karl-Voit.at>\n\
:license: GPL v3 or any later version\n\
:URL: https://github.com/novoid/twitter-json_to_orgmode\n\
:bugreports: via github or <tools@Karl-Voit.at>\n\
:version: " + PROG_VERSION_NUMBER + " from " + PROG_VERSION_DATE + "\n"


## file names containing tags matches following regular expression
MENTIONS_REGEX = re.compile(r'^(\w+):\s*(.+)$', re.M)





parser = OptionParser(usage=USAGE)

parser.add_option("-o", "--outputfile", dest="outfile",
                  help="file in Org-mode format that will be generated")

parser.add_option("--overwrite", action="store_true",
                  help="overwrite outputfile (if found)")

parser.add_option("-v", "--verbose", dest="verbose", action="store_true",
                  help="enable verbose mode")

parser.add_option("-q", "--quiet", dest="quiet", action="store_true",
                  help="enable quiet mode")

parser.add_option("--version", dest="version", action="store_true",
                  help="display version and exit")

(options, args) = parser.parse_args()


def handle_logging():
    """Log handling and configuration"""

    if options.verbose:
        FORMAT = "%(levelname)-8s %(asctime)-15s %(message)s"
        logging.basicConfig(level=logging.DEBUG, format=FORMAT)
    elif options.quiet:
        FORMAT = "%(levelname)-8s %(message)s"
        logging.basicConfig(level=logging.ERROR, format=FORMAT)
    else:
        FORMAT = "%(levelname)-8s %(message)s"
        logging.basicConfig(level=logging.INFO, format=FORMAT)


def error_exit(errorcode, text):
    """
    Exits with return value of errorcode and prints to stderr.

    @param errorcode: integer that will be reported as return value.
    @param text: string with descriptive error message.
    """

    sys.stdout.flush()
    logging.error(text)

    sys.exit(errorcode)


def handle_file(filename, outputhandle):
    """
    @param filename: string containing one file name
    @param outputhandle: file handle to write output strings to
    @param return: error value
    """

    if os.path.isdir(filename):
        logging.warning("Skipping directory \"%s\" because this tool only parses files." % filename)
        return
    elif not os.path.isfile(filename):
        logging.error("Skipping non-file \"%s\" because this tool only parses files." % filename)
        return

    ## FIXXME: loop over entries


def main():
    """Main function"""

    if options.version:
        print os.path.basename(sys.argv[0]) + " version " + PROG_VERSION_NUMBER + \
            " from " + PROG_VERSION_DATE
        sys.exit(0)

    handle_logging()

    if options.verbose and options.quiet:
        error_exit(1, "Options \"--verbose\" and \"--quiet\" found. " +
                   "This does not make any sense, you silly fool :-)")

    if not options.outfile:
        error_exit(2, "Please give me a file I can write to with option \"--outputfile\".")

    if os.path.isfile(options.outputfile):
        if not options.overwrite:
            error_exit(3, "Outputfile found but option \"--overwrite\" not given. Aborting.")
        else:
            logging.debug("removing old outfile \"%s\"." % options.outputfile)
            os.remove(options.outputfile)


    logging.debug("extracting list of files ...")
    logging.debug("len(args) [%s]" % str(len(args)))
    if len(args)<1:
        error_exit(4, "Please add at least one file name as argument")

    files = args

    ## print file names if less than 10:
    if len(files) < 10:
        logging.debug("%s filenames found: [%s]" % (str(len(files)), '], ['.join(files)))
    else:
        logging.debug("%s filenames found")

    logging.debug("opening outfile \"%s\" for writing ..." % options.outputfile)
    with open(options.outputfile, 'w') as outputhandle:

        ## FIXXME: write Org-mode header

        logging.debug("iterate over files ...")
        for filename in files:
            handle_file(filename, outputhandle)

        ## FIXXME: write Org-mode footer

    logging.debug("closed outfile \"%s\"" % options.outputfile)

    logging.debug("successfully finished.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:

        logging.info("Received KeyboardInterrupt")

## END OF FILE #################################################################

#end
