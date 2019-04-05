import regex as re

patterns = [
    ('season', '(s?([0-9]{1,2}))[ex]'),
    ('episode', '([ex]([0-9]{2})(?:[^0-9]|$))'),
    ('year', '(?r)([\[\(]?((?:19[0-9]|20[0-9])[0-9])[\]\)]?)'),
    ('resolution', '([0-9]{3,4}p)'),
    ('quality', ('((?:PPV\.)?[HP]DTV|(?:HD)?CAM|B[DR]Rip|(?:HD-?)?TS|'
                 '(?:PPV )?WEB-?DL(?: DVDRip)?|HDRip|DVDRip|DVDRIP|'
                 'CamRip|W[EB]BRip|(?:UHD\.-?)?BluRay|DvDScr|hdtv|telesync)')),
    ('codec', '(HEVC|xvid|[hx]\.?26[45])'),
    ('audio', ('(MP3|DD(?:[P|\+]?)[2|5|7]\.?[0|1]|Dual[\- ]Audio|LiNE|DTS|'
               'AAC[.-]LC|AAC(?:\.?2\.0)?|'
               'AC3(?:\.5\.1)?)')),
    ('group', '(- ?([^-]+(?:-={[^-]+-?$)?))$'),
    ('region', 'R[0-9]'),
    ('extended', '(EXTENDED(:?.CUT)?)'),
    ('hardcoded', 'HC'),
    ('proper', 'PROPER'),
    ('repack', 'REPACK'),
    ('container', '(MKV|AVI|MP4)'),
    ('widescreen', 'WS'),
    ('website', '^(\[ ?([^\]]+?) ?\])'),
    ('language', '(rus\.eng|ita\.eng)'),
    ('sbs', '(?:Half-)?SBS'),
    ('unrated', 'UNRATED'),
    ('size', '(\d+(?:\.\d+)?(?:GB|MB))'),
    ('3d', '3[D|d]'),
    ('hdr', 'HDR')
]

types = {
    'season': 'integer',
    'episode': 'integer',
    'year': 'integer',
    'extended': 'boolean',
    'hardcoded': 'boolean',
    'proper': 'boolean',
    'repack': 'boolean',
    'widescreen': 'boolean',
    'unrated': 'boolean',
    '3d': 'boolean',
    'hdr': 'boolean'
}

class MediaParser(object):

    def _escape_regex(self, string):
        return re.sub('[\-\[\]{}()*+?.,\\\^$|#\s]', '\\$&', string)
    
    def __init__(self):
        self.torrent = None
        self.excess_raw = None
        self.group_raw = None
        self.start = None
        self.end = None
        self.title_raw = None
        self.parts = None

    def _part(self, name, match, raw, clean):
        # The main core instructuions
        self.parts[name] = clean

        if len(match) != 0:
            # The instructions for extracting title
            index = self.torrent['name'].find(match[0])
            if index == 0:
                self.start = len(match[0])
            elif self.end is None or index < self.end:
                self.end = index

        if name != 'excess':
            # The instructions for adding excess
            if name == 'group':
                self.group_raw = raw
            if raw is not None:
                self.excess_raw = self.excess_raw.replace(raw, '')

    def _late(self, name, clean):
        if name == 'group':
            self._part(name, [], None, clean)
        elif name == 'episodeName':
            clean = re.sub('[\._]', ' ', clean)
            clean = re.sub('_+$', '', clean)
            self._part(name, [], None, clean.strip())

    def parse(self, name):
        self.parts = {}
        self.torrent = {'name': name}
        self.excess_raw = name
        self.group_raw = ''
        self.start = 0
        self.end = None
        self.title_raw = None

        for key, pattern in patterns:
            if key not in ('season', 'episode', 'website'):
                pattern = r'\b%s\b' % pattern

            clean_name = re.sub('_', ' ', self.torrent['name'])
            match = re.findall(pattern, clean_name, re.I)
            if len(match) == 0:
                continue

            index = {}
            if isinstance(match[0], tuple):
                match = list(match[0])
            if len(match) > 1:
                index['raw'] = 0
                index['clean'] = 1
            else:
                index['raw'] = 0
                index['clean'] = 0

            if key in types.keys() and types[key] == 'boolean':
                clean = True
            else:
                clean = match[index['clean']]
                if key in types.keys() and types[key] == 'integer':
                    clean = int(clean)
            if key == 'group':
                if re.search(patterns[5][1], clean, re.I) \
                        or re.search(patterns[4][1], clean):
                    continue  # Codec and quality.
                if re.match('[^ ]+ [^ ]+ .+', clean):
                    key = 'episodeName'
            if key == 'episode':
                sub_pattern = self._escape_regex(match[index['raw']])
                self.torrent['map'] = re.sub(
                    sub_pattern, '{episode}', self.torrent['name']
                )
            self._part(key, match, match[index['raw']], clean)

        # Start process for title
        raw = self.torrent['name']
        if self.end is not None:
            raw = raw[self.start:self.end].split('(')[0]

        clean = re.sub('^ -', '', raw)
        if clean.find(' ') == -1 and clean.find('.') != -1:
            clean = re.sub('\.', ' ', clean)
        clean = re.sub('_', ' ', clean)
        clean = re.sub('([\[\(_]|- )$', '', clean).strip()

        self._part('title', [], raw, clean)

        # Start process for end
        clean = re.sub('(^[-\. ()]+)|([-\. ]+$)', '', self.excess_raw)
        clean = re.sub('[\(\)\/]', ' ', clean)
        match = re.split('\.\.+| +', clean)
        if len(match) > 0 and isinstance(match[0], tuple):
            match = list(match[0])

        clean = filter(bool, match)
        clean = [item for item in filter(lambda a: a != '-', clean)]
        clean = [item.strip('-') for item in clean]
        if len(clean) != 0:
            group_pattern = clean[-1] + self.group_raw
            if self.torrent['name'].find(group_pattern) == \
                    len(self.torrent['name']) - len(group_pattern):
                self._late('group', clean.pop() + self.group_raw)

            if 'map' in self.torrent.keys() and len(clean) != 0:
                episode_name_pattern = (
                    '{episode}'
                    '' + re.sub('_+$', '', clean[0])
                )
                if self.torrent['map'].find(episode_name_pattern) != -1:
                    self._late('episodeName', clean.pop(0))

        if len(clean) != 0:
            if len(clean) == 1:
                clean = clean[0]
            self._part('excess', [], self.excess_raw, clean)
        
        return self.parts


if __name__=="__main__":
    print(MediaParser().parse("2001.A.Space.Odyssey.(1968).1080p.UHD.BluRay.DD5.1.HDR.H.264-DON.mkv"))
    print(MediaParser().parse("Aquaman.2018.2160p.WEB-DL.DD+2.0.HDR.HEVC-MOMA.mkv"))
    print(MediaParser().parse("Future Boy Conan - 01 - Remnant Island.mkv"))
    print(MediaParser().parse("1985.2018.720p.BluRay.DTS.x264-HDS.mkv") )
    print(MediaParser().parse("Lift.2016.720p.WEB-DL.h264.AAC-DEEP.mkv"))
    print(MediaParser().parse("November.2017.720p.AMZN.WEB-DL.DDP2.0.H.264-NTG.mkv"))
    print(MediaParser().parse("Star.Wars.Episode.IV.A.New.Hope.1977.480p.BDRip.XviD.AC3.D-Z0N3.avi"))