#!/usr/bin/env python

import os
import re
import sys

def escape(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace('\'', '&apos;')

def main(argv):

    if len(argv[1:]) != 2:
        sys.stderr.write('usage: {} report out-dir\n'.format(argv[0]))
        sys.stderr.write('reports come from running visualize.py on WMT results (see http://www.statmt.org/wmt13/results.html)\n')
        sys.exit(2)

    outdir = argv[2]
    report = argv[1]

    if os.path.exists(outdir):
        sys.stderr.write('{} exists, exiting.\n'.format(outdir))
        sys.exit(1)

    os.mkdir(outdir)

    ref = {}
    hyp = {}
    sites = set()

    rin = open(report)
    while True:
        line = rin.readline()
        # end of file
        if not line:
            break
        r = re.search('^\s*SENTENCE\s+([0-9]+)\s*$', line)
        if r:
            id = int(r.group(1))
            line = rin.readline().strip()
            r = re.search('^\s*SOURCE\s+', line)
            if not r:
                sys.stderr.write('Error: expected line starting with SOURCE, got: {}\n'.format(line))
                sys.exit(1)
            line = rin.readline().strip()
            r = re.search('^\s*REFERENCE\s+(.+)$', line)
            if not r:
                sys.stderr.write('Error: expected line starting with REFERENCE, got: {}\n'.format(line))
                sys.exit(1)
            ref[id] = r.group(1).strip()
            hyp[id] = []
            while True:
                line = rin.readline().strip()
                # end of block
                if not line:
                    break
                r = re.search('^\s*\[([\.0-9]+)\]\s+(.+)\s+\[(.+)\]\s*$', line)
                if not r:
                    sys.stderr.write('Error: expected line in form [SCORE] text [SYSTEM], got: {}\n'.format(line))
                    sys.exit(1)
                score = float(r.group(1))
                text = r.group(2)
                site = r.group(3)
                hyp[id].append((score, text, site))
                sites.add(site)

    # start files

    rankout = open(os.path.join(outdir, 'xx-xx.rank'), 'w')
    
    refout = open(os.path.join(outdir, 'xx-xx.ref.sgm'), 'w')
    refout.write('<refset trglang="xx" setid="xx" srclang="xx">\n')
    refout.write('<doc sysid="ref" docid="xx">\n')

    siteout = dict((site, open(os.path.join(outdir, 'xx-xx.{}.sgm'.format(site)), 'w')) for site in sites)
    for site in siteout:
        siteout[site].write('<tstset trglang="xx" setid="xx" srclang="xx">\n')
        siteout[site].write('<doc sysid="{}" docid="xx">\n'.format(site))

    # write data
    
    # reset seg ids
    new_id = 1
    for id in sorted(ref):
        refout.write('<seg id="{}"> {} </seg>\n'.format(new_id, escape(ref[id])))
        hyp_list = hyp[id]
        hyp_dict = {}
        for i in range(len(hyp_list)):
            hyp_dict[hyp_list[i][2]] = hyp_list[i][1]
            for j in range(i + 1, len(hyp_list)):
                # skip ties
                if hyp_list[i][0] > hyp_list[j][0]:
                    rankout.write('{}\txx-xx\t{}\txx-xx\t{}\n'.format(new_id, hyp_list[i][2], hyp_list[j][2]))
        for site in sites:
            # unranked sites get empty string for fast scoring since score never used
            siteout[site].write('<seg id="{}"> {} </seg>\n'.format(new_id, escape(hyp_dict.get(site, ''))))
        new_id += 1


    # end files

    rankout.close()
    
    refout.write('</doc>\n')
    refout.write('</refset>\n')
    refout.close()

    for site in siteout:
        siteout[site].write('</doc>\n')
        siteout[site].write('</tstset>\n')
        siteout[site].close()

if __name__ == '__main__':
    main(sys.argv)
