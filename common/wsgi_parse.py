#!/usr/bin/env python3

''' The simplest web server, utilities module. This is where we parse the
    incoming (loaded) files for macros. The substitution occures in steps
    recursively.
'''

import sys, os, time, re, traceback
import wsgi_global, wsgi_util
#, wsgi_conf

_MAX_RECURSE = 10
_regex = "{ .*? }"
_regex2 = "\[ .*? \]"

# ------------------------------------------------------------------------

def _parse_items(item, context, table):

    cccc = ""

    #print("parse item", "'" + item + "\n'")
    item2 = item.split(" ")
    #print ("item2", item2)

    # Scan backwards so items can be overridden
    for ii in range(len(table)-1, -1, -1):
        aa = table[ii]
        #print("aa", aa)
        #if item2[1][2:-2] == aa[0]:
        if item2[1] == aa[0]:
            if type(aa[1]) == str:
                #print("item:", item, "str =", wsgi_util.unescape(aa[1][:24]))
                return aa[1]

            if type(aa[1]) == type(_parse_items):
                #print("item:", item, "func=", aa[1])
                try:
                    cccc = aa[1](item, context)
                except:
                    wsgi_util.put_exception("Cannot exec: " + str(item))
                    #print("item", item, "aa[1]", aa[1])
                    pass
                #print("cccc", cccc[:12])
                return cccc
    return item

# Parse buffer

def parse_buffer(buff, regex, context, table):

    count = 0; prog = 0
    rrr = re.compile(regex)
    arr = []
    while(True):
        frag = re.search(rrr, buff[prog:])
        if not frag:
            arr.append(buff[prog:])
            break
        #print ("match", frag)
        bbb = prog+frag.start()
        eee = prog+frag.end()
        arr.append(buff[prog:bbb])
        #print("match", buff[bbb:eee])
        conv = _parse_items(buff[bbb:eee], context, table)
        arr.append(conv)
        prog += frag.end()
        count += 1

    #print("parsed", count)
    #print ("arr", arr)
    return arr, count

# ------------------------------------------------------------------------

def _parse_one(buff, context, tablex, regex):

    # Recursively process
    content = buff
    cnt2 = 0; old_cnt = 0

    while(True):
        arr, cnt = parse_buffer(content, regex, context, tablex)
        content = ""
        for aa in arr:
            content += str(aa)
        #print("recursive", cnt)
        if cnt <= 1:
            break
        # Maximun recurse exceeded
        if cnt2 >= _MAX_RECURSE:
            break
        cnt2 += 1

        # No change, exit
        if old_cnt == cnt:
            break

        old_cnt = cnt

    return content

# ------------------------------------------------------------------------
# Parse buffer

def recursive_parse(buff, context, local_table):

    if Config.pgdebug > 3:
        print("recursive_parse() buff:", wsgi_util.unescape(buff[:12]))

    #if local_table:
    #    wsgi_util.dump_table("Local Table:", local_table)

    #if global_table:
    #wsgi_util.dump_table("Global Table:", wsgi_global.global_table)

    parsed2 = ""

    # Do local table first, so it overrides global
    if local_table:
        if Config.verbose:
            print("local_table: ", len(local_table))

        #print("LOCAL")
        try:
            parsed2 = _parse_one(buff, context,  local_table, _regex)
        except:
            wsgi_util.put_exception("exception in local parser", )
            parsed2 = buff
    else:
        parsed2 = buff

    # Recursively process
    #print("GLOBAL")
    try:
        parsed3 = _parse_one(parsed2, context,  wsgi_global.global_table, _regex)
    except:
        wsgi_util.put_exception("exception in global parser", )
        parsed3 = buff

    return parsed3

# EOF