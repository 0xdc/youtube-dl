# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import (
    compat_HTTPError,
    compat_str,
    compat_urllib_parse_urlencode,
    compat_urlparse,
)
from ..utils import (
    ExtractorError,
    int_or_none,
    str_or_none,
    urlencode_postdata,
)


class RoosterTeethIE(InfoExtractor):
    _VALID_URL = r'https?://(?:.+?\.)?roosterteeth\.com/(?:episode|watch)/(?P<id>[^/?#&]+)'
    _NETRC_MACHINE = 'roosterteeth'
    _TESTS = [{
        'url': 'http://roosterteeth.com/episode/million-dollars-but-season-2-million-dollars-but-the-game-announcement',
        'md5': 'e2bd7764732d785ef797700a2489f212',
        'info_dict': {
            'id': '9156',
            'display_id': 'million-dollars-but-season-2-million-dollars-but-the-game-announcement',
            'ext': 'mp4',
            'title': 'Million Dollars, But... The Game Announcement',
            'description': 'md5:168a54b40e228e79f4ddb141e89fe4f5',
            'thumbnail': r're:^https?://.*\.png$',
            'series': 'Million Dollars, But...',
            'episode': 'Million Dollars, But... The Game Announcement',
        },
    }, {
        'url': 'http://achievementhunter.roosterteeth.com/episode/off-topic-the-achievement-hunter-podcast-2016-i-didn-t-think-it-would-pass-31',
        'only_matching': True,
    }, {
        'url': 'http://funhaus.roosterteeth.com/episode/funhaus-shorts-2016-austin-sucks-funhaus-shorts',
        'only_matching': True,
    }, {
        'url': 'http://screwattack.roosterteeth.com/episode/death-battle-season-3-mewtwo-vs-shadow',
        'only_matching': True,
    }, {
        'url': 'http://theknow.roosterteeth.com/episode/the-know-game-news-season-1-boring-steam-sales-are-better',
        'only_matching': True,
    }, {
        # only available for FIRST members
        'url': 'http://roosterteeth.com/episode/rt-docs-the-world-s-greatest-head-massage-the-world-s-greatest-head-massage-an-asmr-journey-part-one',
        'only_matching': True,
    }, {
        'url': 'https://roosterteeth.com/watch/million-dollars-but-season-2-million-dollars-but-the-game-announcement',
        'only_matching': True,
    }]
    _EPISODE_BASE_URL = 'https://svod-be.roosterteeth.com/api/v1/episodes/'

    def _login(self):
        username, password = self._get_login_info()
        if username is None:
            return

        try:
            self._download_json(
                'https://auth.roosterteeth.com/oauth/token',
                None, 'Logging in', data=urlencode_postdata({
                    'client_id': '4338d2b4bdc8db1239360f28e72f0d9ddb1fd01e7a38fbb07b4b1f4ba4564cc5',
                    'grant_type': 'password',
                    'username': username,
                    'password': password,
                }))
        except ExtractorError as e:
            msg = 'Unable to login'
            if isinstance(e.cause, compat_HTTPError) and e.cause.code == 401:
                resp = self._parse_json(e.cause.read().decode(), None, fatal=False)
                if resp:
                    error = resp.get('extra_info') or resp.get('error_description') or resp.get('error')
                    if error:
                        msg += ': ' + error
            self.report_warning(msg)

    def _real_initialize(self):
        if self._get_cookies(self._EPISODE_BASE_URL).get('rt_access_token'):
            return
        self._login()

    def _real_extract(self, url):
        display_id = self._match_id(url)
        api_episode_url = self._EPISODE_BASE_URL + display_id

        try:
            m3u8_url = self._download_json(
                api_episode_url + '/videos', display_id,
                'Downloading video JSON metadata')['data'][0]['attributes']['url']
        except ExtractorError as e:
            if isinstance(e.cause, compat_HTTPError) and e.cause.code == 403:
                if self._parse_json(e.cause.read().decode(), display_id).get('access') is False:
                    self.raise_login_required(
                        '%s is only available for FIRST members' % display_id)
            raise

        formats = self._extract_m3u8_formats(
            m3u8_url, display_id, 'mp4', 'm3u8_native', m3u8_id='hls')
        self._sort_formats(formats)

        episode = self._download_json(
            api_episode_url, display_id,
            'Downloading episode JSON metadata')['data'][0]
        attributes = episode['attributes']
        title = attributes.get('title') or attributes['display_title']
        video_id = compat_str(episode['id'])

        thumbnails = []
        for image in episode.get('included', {}).get('images', []):
            if image.get('type') == 'episode_image':
                img_attributes = image.get('attributes') or {}
                for k in ('thumb', 'small', 'medium', 'large'):
                    img_url = img_attributes.get(k)
                    if img_url:
                        thumbnails.append({
                            'id': k,
                            'url': img_url,
                        })

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': attributes.get('description') or attributes.get('caption'),
            'thumbnails': thumbnails,
            'series': attributes.get('show_title'),
            'season_number': int_or_none(attributes.get('season_number')),
            'season_id': attributes.get('season_id'),
            'episode': title,
            'episode_number': int_or_none(attributes.get('number')),
            'episode_id': str_or_none(episode.get('uuid')),
            'formats': formats,
            'channel_id': attributes.get('channel_id'),
            'duration': int_or_none(attributes.get('length')),
        }


class RoosterTeethSeriesIE(RoosterTeethIE):
    _IE_NAME = 'roosterteeth:playlist'
    _VALID_URL = r'https://roosterteeth.com/series/(?P<id>[\w\d\-]+)'

    _TESTS = [
        {
            'url': 'https://roosterteeth.com/series/sunday-driving',
            'playlist_count': 3,
            'info_dict': {
                'id': 'sunday-driving',
                'title': 'Sunday Driving',
            }
        },
        {
            # One season public, season 2 is first-only
            'url': 'https://roosterteeth.com/series/achievement-haunter',
            'playlist_mincount': 18,
            'info_dict': {
                'id': 'achievement-haunter',
                'title': 'Haunter',
            }
        },
        {
            'url': 'https://roosterteeth.com/series/7-wonderings',
            'playlist_mincount': 7,
            'info_dict': {
                'id': '7-wonderings',
                'title': '7 Wonderings',
            },
        },
        {
            'url': 'https://roosterteeth.com/series/lets-play',
            'playlist_mincount': 205,
            'info_dict': {
                'id': 'lets-play',
                'title': "Let's Play",
            },
        },
        {
            'url': 'https://roosterteeth.com/series/let-s-play-live-life-on-tour',
            'playlist_count': 7,
            'info_dict': {
                'id': 'let-s-play-live-life-on-tour',
                'title': "Let's Play Live: Life on Tour",
            },
        },
    ]

    domain = 'https://roosterteeth.com'
    api_domain = 'https://svod-be.roosterteeth.com'

    @classmethod
    def _add_per_page(cls, url, count=None):
        """
        Add the query string per_page to increase the number of results from the API

        The API defaults to a per_page of 24, any series with more videos than this needs
        either pagination or a per_page increase
        """
        if count is None:
            count = 1000

        return cls._set_query_string(url, 'per_page', count)

    @staticmethod
    def _set_query_string(url, key, value):
        parsed_url = compat_urlparse.urlparse(url)
        qs = compat_urlparse.parse_qs(parsed_url.query)
        qs[key] = [value]
        return compat_urlparse.urlunparse(
            parsed_url._replace(query=compat_urllib_parse_urlencode(qs, True)))

    def get_season_episodes_pages(self, episode_link, season_slug, page=None):
        if page is None:
            page = 1

        entries = []

        se_page = self._download_json(
            self._add_per_page(self._set_query_string(episode_link, "page", page)),
            "_".join([season_slug, str(page)])
        )

        assert page == se_page['page']

        for link in se_page['data']:
            entries.append(self.domain + link['canonical_links']['self'])

        if se_page['page'] < se_page['total_pages']:
            entries.extend(
                self.get_season_episodes_pages(
                    episode_link,
                    season_slug,
                    page + 1,
                )
            )

        return entries

    def _real_extract(self, url):
        show_id = self._match_id(url)

        series = self._download_json(
            '{}/api/v1/shows/{}'.format(self.api_domain, show_id),
            show_id,
        )

        data0 = series['data'][0]
        seasons = self._download_json(
            self.api_domain + data0['links']['seasons'],
            '{}_seasons'.format(show_id)
        )

        entries = []
        for season in seasons['data']:
            ep_link = self.api_domain + season['links']['episodes']
            slug = season['attributes']['slug']
            entries.extend(
                self.get_season_episodes_pages(
                    ep_link,
                    slug,
                ))

        videos = [
            self.url_result(entry) for entry in entries
        ]

        return {
            '_type': 'playlist',
            'id': show_id,
            'title': data0['attributes']['title'],
            'entries': videos
        }
