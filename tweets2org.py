#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Time-stamp: <2013-05-20 01:40:33 vk>

## TODO:
## * fix parts marked with «FIXXME»

## ===================================================================== ##
##  You might not want to modify anything below this line if you do not  ##
##  know, what you are doing :-)                                         ##
## ===================================================================== ##

import re
import os
import json
import logging
import datetime
import sys
import codecs
from optparse import OptionParser

## debugging:   for setting a breakpoint:  pdb.set_trace()
#import pdb

PROG_VERSION_NUMBER = u"0.1"
PROG_VERSION_DATE = u"2013-05-20"
INVOCATION_TIME = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

USAGE = u"\n\
    " + sys.argv[0] + u" [<options>] <list of JSON files>\n\
\n\
This python script converts the Twitter export files (JSON format) into\n\
an Org-mode file.\n\
\n\
Short URLs are replaced with their expanded URLs, many things are turned\n\
into meaningful links where possible.\n\
\n\
Example usage:\n\
  " + sys.argv[0] + u" -o tweets.org ~/Twitter_export_USER.json/*.js --add-to-time-stamps=\"+1\"\n\
      ... converts the Twitter export files and adds one hour to time stamps\n\
\n\
For all command line options, please call: " + sys.argv[0] + u" --help\n\
\n\
\n\
:copyright: (c) 2013 by Karl Voit <tools@Karl-Voit.at>\n\
:license: GPL v3 or any later version\n\
:URL: https://github.com/novoid/twitter-json_to_orgmode\n\
:bugreports: via github or <tools@Karl-Voit.at>\n\
:version: " + PROG_VERSION_NUMBER + " from " + PROG_VERSION_DATE + "\n"


## file names containing tags matches following regular expression
MENTIONS_REGEX = re.compile(r'(^|\W)@(\w+)', re.M)

TIME_REGEX = re.compile('^(\w+) (\w+) (\d+) (\d\d):(\d\d):(\d\d) \+\d+ (\d\d\d\d)$')
TIME_DOW_IDX = 1
TIME_MON_IDX = 2
TIME_DAY_IDX = 3
TIME_H_IDX = 4
TIME_M_IDX = 5
TIME_S_IDX = 6
TIME_YEAR_IDX = 7

MONTHS = {'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05',
          'Jun': '06', 'Jul': '07', 'Aug': '08', 'Sep': '09',
          'Oct': '10', 'Nov': '11', 'Dec': '12'}

ORGMODE_HEADER = """## -*- coding: utf-8 mode: org -*-
## This file is generated by """ + sys.argv[0] + """. Any modifications will be overwritten upon next invocation!
## This file is best viewed with Emacs and Org-mode http://orgmode.org
## To add this file to your Emacs org-agenda, do following: M-x org-agenda-file-to-front
* Twitter                                                     :twitter:\n"""

ORGMODE_FOOTER = "* this file is successfully generated by " + sys.argv[0] + " at " + INVOCATION_TIME + "\n"

parser = OptionParser(usage=USAGE)

parser.add_option("-o", "--outputfile", dest="outputfile",
                  help="file in Org-mode format that will be generated")

parser.add_option("--overwrite", action="store_true",
                  help="overwrite outputfile (if found)")

parser.add_option("--add-to-time-stamps", dest="timestamp_delta",
                  help="if data is off by, e.g., two hours, you can specify \"+2\" " +
                  "or \"-2\" here to correct it with plus/minus two hours",
                  metavar="STRING")

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


def convert_twitter_time_to_orgmode_timestamp(twitter_time, timestamp_delta):
    """
    @param twitter_time: string containing the time stamp in Twitter format
    @param timestamp_delta: time delta in hours to fix time stamps (or False)
    @param return: string with Org-mode time stamp
    """

    components = TIME_REGEX.match(twitter_time)

    datetimestamp = datetime.datetime(int(components.group(TIME_YEAR_IDX)),
                                      int(MONTHS[components.group(TIME_MON_IDX)]),
                                      int(components.group(TIME_DAY_IDX)),
                                      int(components.group(TIME_H_IDX)),
                                      int(components.group(TIME_M_IDX)),
                                      int(components.group(TIME_S_IDX)))

    if timestamp_delta:
        datetimestamp += datetime.timedelta(0, 0, 0, 0, 0, timestamp_delta)

    return datetimestamp.strftime('<%Y-%m-%d %a %H:%M>')


def format_entry(time_stamp, tweetid, name, reply_to, text):
    """
    @param time_stamp: string with (corrected) Org-mode time stamp of tweet
    @param tweetid: string with ID of tweet
    @param name: string with twitter name of poster
    @param reply_to: FALSE or the string of the ID of the replied tweet
    @param text: string containing the tweet text
    @param return: string containing the Org-mode entry of a tweet
    """

    if reply_to:
        ## NOTE: I can not easily get the tweet URL only with the tweet ID and without user name:
        ## https://dev.twitter.com/docs/api/1.1/get/statuses/show/%3Aid
        reply_to_string = " a reply to [[id:tweet" + reply_to + "][tweet]]"
    else:
        reply_to_string = u''

    return u"** " + time_stamp + \
        " [[http://twitter.com/n0v0id/statuses/" + tweetid + "][" + name + " wrote]]" + \
        reply_to_string + ": " + text + "\n" + \
        ":PROPERTIES:\n:ID:  tweet" + tweetid + "\n:END:\n"


def handle_file(filename, outputhandle, timestamp_delta):
    """
    @param filename: string containing one file name
    @param outputhandle: file handle to write output strings to
    @param timestamp_delta: time delta in hours to fix time stamps (or False)
    @param return: error value
    """

    if os.path.isdir(filename):
        logging.warning("Skipping directory \"%s\" because this tool only parses files." % filename)
        return
    elif not os.path.isfile(filename):
        logging.error("Skipping non-file \"%s\" because this tool only parses files." % filename)
        return

    firstline = True
    json_string = u''

    logging.debug("reading JSON data from file: \"%s\" ..." % filename)
    for line in codecs.open(filename, 'r', encoding='utf-8'):

        ## read in every line except first line (Twitter data is JavaScript, not JSON.) to convert it to JSON
        if firstline:
            firstline = False
            next
        else:
            json_string += line

    logging.debug("reading file finished: \"%s\"" % filename)

    logging.debug("parsing JSON data ...")
    json_data = json.loads(json_string)
    logging.debug("parsing JSON data finished")

    for tweet in json_data:

        tweetid = str(tweet["id"])
        text = tweet["text"].replace("&amp;", u"&").replace("&gt;", u">").replace("&lt;", u"<").replace('\n', u"⏎")

        created_at = tweet["created_at"]
        name = tweet["user"]["name"]

        ## if it is an reply, get previous tweet ID
        if "in_reply_to_status_id" in tweet.keys():
            reply_to = str(tweet["in_reply_to_status_id"])
        else:
            reply_to = False

        ## expand short URLs to original URLs
        if "urls" in tweet["entities"].keys():
            for urlentry in tweet["entities"]["urls"]:
                text = text.replace(urlentry["url"], urlentry["expanded_url"])

        ## replace mentions with URLs to profile
        text = MENTIONS_REGEX.sub(r'\1[[http://twitter.com/\2][@\2]]', text, count=0)

        time_stamp = convert_twitter_time_to_orgmode_timestamp(created_at, timestamp_delta)

        outputhandle.write(format_entry(time_stamp, tweetid, name, reply_to, text))


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

    if not options.outputfile:
        error_exit(2, "Please give me a file I can write to with option \"--outputfile\".")

    if os.path.isfile(options.outputfile):
        if not options.overwrite:
            error_exit(3, "Outputfile found but option \"--overwrite\" not given. Aborting.")
        else:
            logging.debug("removing old outfile \"%s\"." % options.outputfile)
            os.remove(options.outputfile)

    logging.debug("extracting list of files ...")
    logging.debug("len(args) [%s]" % str(len(args)))
    if len(args) < 1:
        error_exit(4, "Please add at least one file name as argument")

    timestamp_delta = False
    if options.timestamp_delta:
        timestamp_components = re.match('[+-]\d\d?', options.timestamp_delta)
        if not timestamp_components:
            error_exit(5, "format of \"--add-to-time-stamps\" is not recognized. Should be similar " +
                       "to ,e.g., \"+1\" or \"-3\".")
        timestamp_delta = int(options.timestamp_delta)

    files = args

    ## print file names if less than 10:
    if len(files) < 10:
        logging.debug("%s filenames found: [%s]" % (str(len(files)), '], ['.join(files)))
    else:
        logging.debug("%s filenames found")

    logging.debug("opening outfile \"%s\" for writing ..." % options.outputfile)
    with codecs.open(options.outputfile, 'w', encoding='utf-8') as outputhandle:

        outputhandle.write(ORGMODE_HEADER)

        logging.debug("iterate over files ...")
        for filename in files:
            handle_file(filename, outputhandle, timestamp_delta)

        outputhandle.write(ORGMODE_FOOTER)

    logging.debug("closed outfile \"%s\"" % options.outputfile)

    logging.debug("successfully finished.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:

        logging.info("Received KeyboardInterrupt")

## END OF FILE #################################################################

#end
