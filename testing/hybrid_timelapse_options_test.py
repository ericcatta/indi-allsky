#!/usr/bin/env python3
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from indi_allsky.timelapse_options import deflicker_options, video_filter_arguments


def run():
    assert deflicker_options({}) == (True, 5)
    assert video_filter_arguments({}, '640:480', '-threads 1') == [
        '-vf', 'deflicker=size=5:mode=am,scale=640:480', '-threads', '1']
    assert video_filter_arguments({}, '640:480', '-vf hflip -threads 1') == [
        '-vf', 'deflicker=size=5:mode=am,hflip', '-threads', '1']
    assert video_filter_arguments({'TIMELAPSE': {'DEFLICKER': False}}, '640:480', '-vf hflip') == [
        '-vf', 'scale=640:480', '-vf', 'hflip']
    assert video_filter_arguments({'TIMELAPSE': {'DEFLICKER_WINDOW': 3}}, '', '') == [
        '-vf', 'deflicker=size=3:mode=am']
    for invalid in (True, 0, 4, 100, '5', None):
        try:
            deflicker_options({'TIMELAPSE': {'DEFLICKER_WINDOW': invalid}})
        except ValueError:
            pass
        else:
            raise AssertionError(invalid)
    print('Hybrid timelapse options: PASS')


if __name__ == '__main__':
    run()
