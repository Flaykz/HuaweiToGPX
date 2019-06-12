#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import argparse
import time
import pandas as pd


NAME = 'exportGPX'
DESCRIPTION = 'a command line tool to export Huawei tracking \
files to GPX files'
DEBUG = False


def debug(message):
    """ Print debug message
    """
    if DEBUG:
        print(message)


def normalize_timestamp(timestamp):
    """ Normalize timestamp to seconces since epoch
    """
    if (str(timestamp).find('E12') >= 0 or
            len(str(int(float(timestamp)))) == 13):
        timestamp = int(float(timestamp) / 1000.0)
    else:
        timestamp = int(float(timestamp))
    return timestamp


def sec_to_datetime(timestamp):
    """ Convert secondes since epoch to a date and time
    """
    return time.strftime("%d/%m/%Y %H:%M:%S %Z", time.localtime(timestamp))


def sec_to_date(timestamp):
    """ Convert secondes since epoch to a date
    """
    return time.strftime("%d/%m/%Y", time.localtime(timestamp))


def sec_to_time(timestamp):
    """ Convert secondes since epoch to a time
    """
    return time.strftime("%H:%M:%S", time.localtime(timestamp))


def milli_to_datetime(timestamp):
    """ Convert millisecondes since epoch to a date and time
    """
    return sec_to_datetime(int(timestamp)/1000)


def milli_to_date(timestamp):
    """ Convert millisecondes since epoch to a date
    """
    return sec_to_date(int(timestamp)/1000)


def milli_to_time(timestamp):
    """ Convert millisecondes since epoch to a time
    """
    return sec_to_time(int(timestamp)/1000)


def gpx_header():
    """ Return gpx valid header
    """
    return """\
<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
<gpx xmlns="http://www.topografix.com/GPX/1/1" creator="byHand" version="1.1"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.topografix.com/GPX/1/1 \
    http://www.topografix.com/GPX/1/1/gpx.xsd">
    <trk>
        <trkseg>"""


def gpx_footer():
    """ Return gpx valid footer
    """
    return """\

        </trkseg>
    </trk>
</gpx>"""


def point(infos):
    """ Return gpx valid checkpoint with coordonates given
    """
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
                        <gpxtpx:hr>" + str(int(infos.get('heart_rate', 0)))\
                                     + "</gpxtpx:hr>\r\n\
                        <gpxtpx:cad>" + str(infos.get('vitesse', 0))\
                                      + "</gpxtpx:cad>\r\n\
                    </gpxtpx:TrackPointExtension>\r\n\
                </extensions>\r\n\
            </trkpt>"


def get_datas(file_in):
    """ Return pandas dataframe with all informations
    """
    debug('Opening ' + file_in + '...')
    with open(file_in, 'r') as f_in:
        debug('Reading datas...')
        lbs, heart_rate, cad, pace_minute = [], [], [], []
        speed_per_seconde, beat_per_minute, alt = [], [], []
        for line in f_in:
            dic = {}
            infos = line.split(';')
            type_data = infos[0].split('=')[1]
            k = int(infos[1].split('=')[1])
            if type_data == 'lbs':
                # Location per seconde
                dic['lat'] = float(infos[2].split('=')[1])
                dic['lon'] = float(infos[3].split('=')[1])
#                 dic['alt'] = float(infos[4].split('=')[1])
                dic['t'] = normalize_timestamp(infos[5].split('=')[1])
                lbs.append(dic)
            else:
                value = int(float(infos[2].split('=')[1]))
                if type_data == 'p-m':
                    # Pace / Minutes
                    dic['m'] = int(k) // 10000  # Nb meters since start
                    dic['s'] = value  # NB secondes to do 1000 meters
                    dic['pace'] = str(int(value) // 60) + "'"\
                    + str(int(value) % 60) + '"'
                    pace_minute.append(dic)
                elif type_data == 'b-p-m':
                    # Beat per minutes ?
                    dic['k'] = k
                    dic['value'] = value
                    beat_per_minute.append(dic)
                elif type_data == 'h-r':
                    # Heart Rate
                    dic['t'] = normalize_timestamp(k)
                    dic['heart_rate'] = value
                    heart_rate.append(dic)
                elif type_data == 's-r':
                    # Stride Rate
                    dic['t'] = normalize_timestamp(k)
                    dic['stride'] = value
                    cad.append(dic)
                elif type_data == 'rs':
                    # Speed per seconde
                    dic['s'] = k  # Nb secondes since start
                    dic['m'] = value  # Speed in nb decimeter per seconde
                    dic['speed'] = int(value) / 10 * 3600 / 1000
                    speed_per_seconde.append(dic)
                elif type_data == 'alti':
                    # Alt
                    dic['t'] = normalize_timestamp(k)
                    dic['alt'] = value
                    alt.append(dic)
                else:
                    debug('Data type unknown: ' + type_data)

        dataframe = pd.DataFrame(lbs).sort_values(by=['t'], ascending=True)
        dataframe = pd.merge(dataframe, pd.DataFrame(heart_rate), on='t', how='outer')
        dataframe = pd.merge(dataframe, pd.DataFrame(alt), on='t', how='outer')
        dataframe['s'] = dataframe.index
        dataframe = dataframe[dataframe['lat'].notnull()].sort_values(by=['t'], ascending=True)
        dataframe = dataframe[dataframe['lat'] != 90.0]
        dataframe = pd.merge(dataframe, pd.DataFrame(speed_per_seconde), on='s', how='outer')
        dataframe = dataframe.fillna(method='ffill')
        dataframe = dataframe.fillna(method='bfill')
    return dataframe


def process(file_in):
    """ Process files to get all geos and states informations
    """
    if file_in.find('HiTrack_') >= 0:
        info = file_in.split("_")[1]
        start = info[0:13]
        end = info[13:-5]
        date = milli_to_date(start).replace("/", "")
        start_time = milli_to_time(start).replace(':', "")
        end_time = milli_to_time(end).replace(':', "")
        file_out = date + "_" + start_time + "_" + end_time + ".gpx"
    else:
        print('You have to give a original HiTrack_ file in entry, not : '
              + file_in)
        return None

    dataframe = get_datas(file_in)

    text = gpx_header()
    for _, data in dataframe.iterrows():
        text += point(data)
    text += gpx_footer()
    text = text.replace("<trkseg>    \r\n        </trkseg>", "")

    with open(file_out, 'w') as fout:
        fout.write(text)
        print(file_out + ' processed')
    return text


def main():
    """ Get args and launch action to do over files
    """
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument(
        "input_file", nargs='*', default=os.getcwd(),
        help="HiTrack file to convert to GPX")
    parser.add_argument(
        '-d', '--debug', action='store_true', help="enable debug file_out")
    args = parser.parse_args()
    if args.debug:
        global DEBUG
        DEBUG = args.debug
    input_file = args.input_file

    if input_file == os.getcwd():
        for _, _, files in os.walk(input_file):
            for file_name in files:
                if file_name.find('HiTrack_') >= 0:
                    process(file_name)
    else:
        for file_name in input_file:
            process(file_name)


if __name__ == '__main__':
    main()
