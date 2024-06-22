#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import io
import sys
import glob
import shutil
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
import re
from argparse import ArgumentParser

VERSION = '1.0.0'

sharpcap_file_re = re.compile('(\d\d_\d\d_\d\d)\.CameraSettings\.txt$', re.A)
start_capture_re = re.compile('StartCapture\s*=\s*(.+)$', re.A)
mid_capture_re = re.compile('MidCapture\s*=\s*(.+)$', re.A)
end_capture_re = re.compile('EndCapture\s*=\s*(.+)$', re.A)
sharpcap_time_re = re.compile('([^.]+\.\d{6})\d*(.+)', re.A)
frame_count_re = re.compile('FrameCount\s*=\s*(\d+)$', re.A)
camera_re = re.compile('\[(.+)\]$')
autostakkert_file_re = re.compile('(\d\d_\d\d_\d\d)_([^_]+).*\.(\w+)$', re.A)
autostakkert_limit_re = re.compile('.*_limit(\d+)-(\d+)[_.].*')
template_split_re = re.compile('(\{\w+\})')
template_token_re = re.compile('\{(\w+)\}$')
ng_field_search_re = re.compile('[-\\/:*?"><|&(){}^=;!\'+,`~]')

def get_user():
    user = None
    if 'USER' in os.environ:
        user = os.environ['USER']
    elif 'USERNAME' in os.environ:
        user = os.environ['USERNAME']
    return user

def test_directory(dir):
    if not os.path.exists(dir):
        sys.stderr.write("Directory not found: " + dir + "\n")
        sys.exit(1)
    if not os.path.isdir(dir):
        sys.stderr.write("Not a directory: " + dir + "\n")
        sys.exit(1)

def expand_imageinfo(imageinfo, params):
    expanded = ''
    for token in template_split_re.split(imageinfo, re.A):
        if (r :=  template_token_re.match(token)):
            name = r.group(1)
            if name in params:
                expanded += params[name]
            else:
                expanded += token
        else:
            expanded += token
    return expanded

def sharpcap_time_str_to_time(sharpcap_time_str):
    r = sharpcap_time_re.match(sharpcap_time_str)
    time_str = f"{r.group(1)}{r.group(2)}"
    time = datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%S.%f%z')
    return time

def time_to_winjupos_time_str(time):
    min = time.minute + (time.second + time.microsecond / 1000000.0)/ 60.0
    rmin = Decimal(str(min)).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
    return f"{str(time.date())}-{time.hour:02d}{rmin:04.1f}"

def error(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)

argparser = ArgumentParser(description='Create copies (or hardlinks) of stacked image files created using SharpCap 4 and AutoStakkert! 3 with filenames suitable for WinJUPOS'' Image Measurement.')
argparser.add_argument('sc_dir', help='directory where SharpCap''s CameraSettings files are saved.')
argparser.add_argument('as_dir', help='directory where stacked image files are saved.')
argparser.add_argument('target_dir', help='directory where renamed copies (or hardlinks) of stacked image files are saved.')
argparser.add_argument('-p', dest='pattern', default='*.tif', help='filename pattern of stacked image files.')
argparser.add_argument('-l', dest='link', action='store_true', help='create hardlinks instead of copies.')
argparser.add_argument('-o', dest='observer', default=get_user(), help='observer name. by default, value of USER or USERNAME environment variable is used.')
argparser.add_argument('-i', dest='imageinfo', help='image information. template {cam} is expanded to represent camera name. template {ff} is expended to free field value of AS!3.')
argparser.add_argument('--dry-run', dest='dry_run', action='store_true', help='do not copy (or hardlink) files.')
argparser.add_argument('--version', action='version', version=f'%(prog)s {VERSION}')
args = argparser.parse_args()

message_prefix = ''
if args.dry_run:
    message_prefix = '[dry-run] '

operation = 'copy'
if args.link:
    operation = 'link'

test_directory(args.sc_dir)
test_directory(args.as_dir)
if not os.path.exists(args.target_dir):
    if not args.dry_run:
        os.makedirs(args.target_dir)
    print(f"{message_prefix}create target directory: {args.target_dir}")

sc_files = {}
for cs in glob.glob(os.path.join(args.sc_dir, "*.CameraSettings.txt")):
    filename_time = sharpcap_file_re.match(os.path.basename(cs)).group(1)
    meta = {
        'camera': None,
        'start_capture': None,
        'mid_capture': None,
        'end_capture': None,
        'frame_count': None
    }
    with io.open(cs, mode='r', encoding='utf-8') as f:
        for line in f:
            if (line.startswith('#')
                or line.startswith('\n')
                or line.startswith('\r')):
                continue
            if (r := camera_re.match(line)) and not meta['camera']:
                camera = r.group(1)
                if camera:
                    camera = re.sub('\([^)]*\)', '', camera)
                    camera = camera.replace(' ', '').replace('-', '')
                meta['camera'] = camera
            elif (r := start_capture_re.match(line)):
                meta['start_capture'] = sharpcap_time_str_to_time(r.group(1))
            elif (r := mid_capture_re.match(line)):
                meta['mid_capture'] = sharpcap_time_str_to_time(r.group(1))
            elif (r := end_capture_re.match(line)):
                meta['end_capture'] = sharpcap_time_str_to_time(r.group(1))
            elif (r := frame_count_re.match(line)):
                meta['frame_count'] = int(r.group(1))
    # end reading .CameraSettings.txt
    sc_files[filename_time] = meta

for stacked_image_file in glob.glob(os.path.join(args.as_dir, args.pattern)):
    in_filename = os.path.basename(stacked_image_file)
    filename_time = None
    free_field = None
    frame_start = None
    frame_end = None
    ext = None
    if (r := autostakkert_file_re.match(in_filename)):
        filename_time = r.group(1)
        free_field = r.group(2)
        ext = r.group(3)
        if free_field:
            free_field = free_field.replace(' ', '')
        if (r := autostakkert_limit_re.match(in_filename)):
            frame_start = int(r.group(1))
            frame_end = int(r.group(2))
    else:
        continue
    
    if filename_time in sc_files:
        if not args.observer:
            error("observer is not specified.")
        elif not args.observer.isascii():
            error("observer contains non-ASCII character: '{args.observer}'")
        elif ng_field_search_re.search(args.observer):
            error("observer contains bad character: '{args.observer}'")
        
        meta = sc_files[filename_time]
        imageinfo_suffix = ''
        if args.imageinfo:
            params = { 'cam': meta['camera'], 'ff': free_field }
            if (imageinfo := expand_imageinfo(args.imageinfo, params)):
                if not imageinfo.isascii():
                    error("imageinfo contains non-ASCII character: "\
                          "'{args.imageinfo}' (expended:'{imageinfo}')")
                elif ng_field_search_re.search(imageinfo):
                    error("imageinfo contains bad character: "\
                          "'{args.imageinfo}' (expended:'{imageinfo}')")
                else:
                    imageinfo_suffix = f"-{imageinfo}"

        wj_time = None
        if frame_start == None:
            wj_time = time_to_winjupos_time_str(meta['mid_capture'])
        else:
            cap_delta = meta['end_capture'] - meta['start_capture']
            spf = cap_delta.total_seconds() / meta['frame_count']
            mid_delta = timedelta(seconds=((frame_start + frame_end) / 2 * spf))
            wj_time = time_to_winjupos_time_str(meta['start_capture'] + mid_delta)
        
        out_filename = f"{wj_time}-{args.observer}{imageinfo_suffix}.{ext}"
        print(f"{message_prefix}{operation}: {in_filename} -> {out_filename}")
        
        if not args.dry_run:
            dest = os.path.join(args.target_dir, out_filename)
            if args.link:
                os.link(stacked_image_file, dest)
            else:
                shutil.copy2(stacked_image_file, dest)
