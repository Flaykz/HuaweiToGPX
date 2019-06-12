#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import time
import pandas as pd
import os

NAME = 'exportGPX'
DESCRIPTION = 'a command line tool to export Huawei tracking \
files to GPX files'
DEBUG = False


def debug(m):
    if DEBUG:
        print(m)


def normalize_timestamp(timestamp):
    if (str(timestamp).find('E12') >= 0 or
            len(str(int(float(timestamp)))) == 13):
        timestamp = int(float(timestamp) / 1000.0)
    else:
        timestamp = int(float(timestamp))
    return timestamp


def sec_to_datetime(t):
    return time.strftime("%d/%m/%Y %H:%M:%S %Z", time.localtime(t))


def sec_to_date(t):
    return time.strftime("%d/%m/%Y", time.localtime(t))


def sec_to_time(t):
    return time.strftime("%H:%M:%S", time.localtime(t))


def milli_to_datetime(t):
    return sec_to_datetime(int(t)/1000)


def milli_to_date(t):
    return sec_to_date(int(t)/1000)


def milli_to_time(t):
    return sec_to_time(int(t)/1000)


def gpx_header():
    return """\
<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
<gpx xmlns="http://www.topografix.com/GPX/1/1" creator="byHand" version="1.1"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.topografix.com/GPX/1/1 \
    http://www.topografix.com/GPX/1/1/gpx.xsd">
    <trk>
        <trkseg>"""


def gpx_footer():
    return """\

        </trkseg>
    </trk>
</gpx>"""


def point(infos):
    if (str(infos.get('lat', '0')) == "90.0" and
            str(infos.get('lon', '0')) == "-80.0"):
        return "\r\n\
        </trkseg>\r\n\
        <trkseg>"
    else:
        return "\r\n\
            <trkpt lat=\"" + str(infos.get('lat', '0')) + "\" lon=\""\
            + str(infos.get('lon', '0')) + "\">\r\n\
                <ele>" + str(infos.get('alt', '0')) + "</ele>\r\n\
                <time>" + str(sec_to_datetime(infos.get('t', 0)))\
                        + "</time>\r\n\
                <extensions>\r\n\
                    <gpxtpx:TrackPointExtension>\r\n\
                        <gpxtpx:hr>" + str(int(infos.get('hr', 0)))\
                                     + "</gpxtpx:hr>\r\n\
                        <gpxtpx:cad>" + str(infos.get('vitesse', 0))\
                                      + "</gpxtpx:cad>\r\n\
                    </gpxtpx:TrackPointExtension>\r\n\
                </extensions>\r\n\
            </trkpt>"


def process(fileIn):
    if fileIn.find('HiTrack_') >= 0:
        info = fileIn.split("_")[1]
        start = info[0:13]
        end = info[13:-5]
        date = milli_to_date(start).replace("/", "")
        startTime = milli_to_time(start).replace(':', "")
        endTime = milli_to_time(end).replace(':', "")
        OUTPUT = date + "_" + startTime + "_" + endTime + ".gpx"
    else:
        print('You have to give a original HiTrack_ file in entry, not : '
              + fileIn)
        return None

    debug('Opening ' + fileIn + '...')
    with open(fileIn, 'r') as f:
        debug('Reading datas...')
        lbs, hr, cad, pm, rs, bpm, alt = [], [], [], [], [], [], []
        for line in f:
            dic = {}
            infos = line.split(';')
            typeData = infos[0].split('=')[1]
            k = int(infos[1].split('=')[1])
            if typeData == 'lbs':
                # Location per seconde
                dic['lat'] = float(infos[2].split('=')[1])
                dic['lon'] = float(infos[3].split('=')[1])
#                 dic['alt'] = float(infos[4].split('=')[1])
                dic['t'] = normalize_timestamp(infos[5].split('=')[1])
                lbs.append(dic)
            else:
                v = int(float(infos[2].split('=')[1]))
                if typeData == 'p-m':
                    # Pace / Minutes
                    dic['m'] = int(k) // 10000  # Nb meters since start
                    dic['s'] = v  # NB secondes to do 1000 meters
                    dic['pace'] = str(int(v) // 60) + "'"
                    + str(int(v) % 60) + '"'
                    pm.append(dic)
                elif typeData == 'b-p-m':
                    # Beat per minutes ?
                    dic['k'] = k
                    dic['v'] = v
                    bpm.append(dic)
                elif typeData == 'h-r':
                    # Heart Rate
                    dic['t'] = normalize_timestamp(k)
                    dic['hr'] = v
                    hr.append(dic)
                elif typeData == 's-r':
                    # Stride Rate
                    dic['t'] = normalize_timestamp(k)
                    dic['stride'] = v
                    cad.append(dic)
                elif typeData == 'rs':
                    # Speed per seconde
                    dic['s'] = k  # Nb secondes since start
                    dic['m'] = v  # Speed in nb decimeter per seconde
                    dic['speed'] = int(v) / 10 * 3600 / 1000
                    rs.append(dic)
                elif typeData == 'alti':
                    # Alt
                    dic['t'] = normalize_timestamp(k)
                    dic['alt'] = v
                    alt.append(dic)
                else:
                    debug('Data type unknown: ' + typeData)

        df = pd.DataFrame(lbs).sort_values(by=['t'], ascending=True)
        df = pd.merge(df, pd.DataFrame(hr), on='t', how='outer')
        df = pd.merge(df, pd.DataFrame(alt), on='t', how='outer')
        df['s'] = df.index
        df = df[df['lat'].notnull()].sort_values(by=['t'], ascending=True)
        df = df[df['lat'] != 90.0]
        df = pd.merge(df, pd.DataFrame(rs), on='s', how='outer')
        df = df.fillna(method='ffill')
        df = df.fillna(method='bfill')

        text = gpx_header()
        for index, data in df.iterrows():
            text += point(data)
        text += gpx_footer()
        text = text.replace("<trkseg>    \r\n        </trkseg>", "")

        with open(OUTPUT, 'w') as fout:
            fout.write(text)
            print(OUTPUT + ' processed')


def main():
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument(
        "input_file", nargs='*', default=os.getcwd(),
        help="HiTrack file to convert to GPX")
    parser.add_argument(
        '-d', '--debug', action='store_true', help="enable debug output")
    args = parser.parse_args()
    if args.debug:
        global DEBUG
        DEBUG = args.debug
    INPUT = args.input_file

    if INPUT == os.getcwd():
        for root, dirs, files in os.walk(INPUT):
            for filename in files:
                if filename.find('HiTrack_') >= 0:
                    process(filename)
    else:
        for filename in INPUT:
            process(filename)


if __name__ == '__main__':
    main()
