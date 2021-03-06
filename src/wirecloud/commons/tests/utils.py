# -*- coding: utf-8 -*-

# Copyright (c) 2014-2015 CoNWeT Lab., Universidad Politécnica de Madrid

# This file is part of Wirecloud.

# Wirecloud is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Wirecloud is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with Wirecloud.  If not, see <http://www.gnu.org/licenses/>.

from io import BytesIO
import os
import zipfile

from django.http import Http404, UnreadablePostError
from django.test import TestCase
from mock import patch, Mock

from wirecloud.commons.utils.html import clean_html
from wirecloud.commons.utils.http import build_sendfile_response
from wirecloud.commons.utils.log import SkipUnreadablePosts
from wirecloud.commons.utils.mimeparser import best_match, parse_mime_type
from wirecloud.commons.utils.wgt import WgtFile


# Avoid nose to repeat these tests (they are run through wirecloud/commons/tests/__init__.py)
__test__ = False


class HTMLCleanupTestCase(TestCase):

    tags = ('wirecloud-html-cleanup',)

    def test_scripts_are_removed(self):
        self.assertEqual(clean_html('<script>asdfas</script>'), '')
        self.assertEqual(clean_html('start content <script>asdfas</script> valid content'), 'start content  valid content')

    def test_event_attributes_are_removed(self):
        self.assertEqual(clean_html('<div onclick="evil_script();" class="alert">content</div>'), '<div class="alert">content</div>')

    def test_processing_instructions_are_removed(self):
        self.assertEqual(clean_html('<div class="alert"><?php echo "<p>Hello World</p>"; ?>content</div>'), '<div class="alert">content</div>')

    def test_audio_elements_are_removed(self):
        initial_code = '<div class="alert"><audio controls="controls"><source src="sound.ogg" type="audio/ogg"/><source src="sound.mp3" type="audio/mpeg"/>Your browser does not support the audio tag.</audio>content</div>'
        self.assertEqual(clean_html(initial_code), '<div class="alert">content</div>')

    def test_video_elements_need_controls(self):
        initial_code = '<video><source src="movie.mp4" type="video/mp4"/><source src="movie.ogg" type="video/ogg"/>Your browser does not support the video tag.</video>content'
        expected_code = '<video controls="controls"><source src="movie.mp4" type="video/mp4"/><source src="movie.ogg" type="video/ogg"/>Your browser does not support the video tag.</video>content'
        self.assertEqual(clean_html(initial_code), expected_code)

    def test_links_are_forced_to_target_blank(self):
        self.assertEqual(clean_html('<div class="alert">Follow this <a href="http://example.com">link</a></div>'), '<div class="alert">Follow this <a href="http://example.com" target="_blank">link</a></div>')

    def test_relative_links_are_removed(self):
        initial_code = '<div class="alert">Follow this <a href="files/insecure_content.exe">link</a></div>'
        expected_code = '<div class="alert">Follow this link</div>'
        self.assertEqual(clean_html(initial_code), expected_code)

    def test_relative_image_urls(self):
        initial_code = 'Example image: <img src="images/example.png"/>'
        expected_code = 'Example image: <img src="http://example.com/images/example.png"/>'
        self.assertEqual(clean_html(initial_code, base_url='http://example.com'), expected_code)


class GeneralUtilsTestCase(TestCase):

    tags = ('wirecloud-general-utils',)

    def test_skipunreadableposts_filter(self):

        record = Mock()
        record.exc_info = (None, UnreadablePostError())
        filter = SkipUnreadablePosts()
        self.assertFalse(filter.filter(record))

    def test_skipunreadableposts_filter_should_ignore_general_exceptions(self):

        record = Mock()
        record.exc_info = (None, Exception())
        filter = SkipUnreadablePosts()
        self.assertTrue(filter.filter(record))

    def test_skipunreadableposts_filter_should_ignore_records_without_exc_info(self):

        record = Mock()
        record.exc_info = None
        filter = SkipUnreadablePosts()
        self.assertTrue(filter.filter(record))

    def test_mimeparser_parse_mime_type_should_accept_single_wildcard(self):

        self.assertEqual(parse_mime_type('*;q=0.5'), ('*', '*', {'q': '0.5'}))

    def test_mimeparser_best_match_should_ignore_blank_media_ranges(self):

        self.assertEqual(best_match(['application/xbel+xml', 'text/xml'], 'text/*;q=0.5, , */*; q=0.1'), 'text/xml')

    def test_mimeparser_best_match_should_ignore_blank_media_ranges(self):

        self.assertEqual(best_match(['application/xbel+xml; a=1; b=2', 'application/xml'], 'application/*, application/xbel+xml; a=1; b=2'), 'application/xbel+xml; a=1; b=2')


class WGTTestCase(TestCase):

    tags = ('wirecloud-wgt',)

    def build_simple_wgt(self, other_files=()):

        f = BytesIO()
        zf = zipfile.ZipFile(f, 'w')
        zf.writestr('config.xml', b'')
        zf.writestr('test.html', b'')
        for of in other_files:
            zf.writestr(of, b'')
        zf.close()
        return WgtFile(f)

    def test_extract_inexistent_dir(self):

        with patch('wirecloud.commons.utils.wgt.os', autospec=True) as os_mock:
            with patch('wirecloud.commons.utils.wgt.open', create=True) as open_mock:
                os_mock.path.normpath = os.path.normpath
                wgt_file = self.build_simple_wgt()
                self.assertRaises(KeyError, wgt_file.extract_dir, 'doc', '/tmp/test')
                self.assertEqual(os_mock.makedirs.call_count, 0)
                self.assertEqual(os_mock.mkdir.call_count, 0)
                self.assertEqual(open_mock.call_count, 0)

    def test_extract_empty_dir(self):

        with patch('wirecloud.commons.utils.wgt.os', autospec=True) as os_mock:
            with patch('wirecloud.commons.utils.wgt.open', create=True) as open_mock:
                os_mock.path.normpath = os.path.normpath
                os_mock.path.exists.return_value = False
                wgt_file = self.build_simple_wgt(other_files=('doc/',))
                wgt_file.extract_dir('doc', '/tmp/test')

                self.assertEqual(os_mock.makedirs.call_count, 1)
                self.assertEqual(os_mock.mkdir.call_count, 0)
                self.assertEqual(open_mock.call_count, 0)

    def test_extract_empty_dir_existing_output_dir(self):

        with patch('wirecloud.commons.utils.wgt.os', autospec=True) as os_mock:
            with patch('wirecloud.commons.utils.wgt.open', create=True) as open_mock:
                os_mock.path.normpath = os.path.normpath
                os_mock.path.exists.return_value = True
                wgt_file = self.build_simple_wgt(other_files=('doc/',))
                wgt_file.extract_dir('doc', '/tmp/test')

                self.assertEqual(os_mock.makedirs.call_count, 0)
                self.assertEqual(open_mock.call_count, 0)

    def test_extract_dir(self):

        def exists_side_effect(path):
            if path != '/tmp/test/folder1':
                return False
            else:
                result = not exists_side_effect.first_time
                exists_side_effect.first_time = False
                return result
        exists_side_effect.first_time = True

        with patch('wirecloud.commons.utils.wgt.os', autospec=True) as os_mock:
            with patch('wirecloud.commons.utils.wgt.open', create=True) as open_mock:

                os_mock.path.normpath = os.path.normpath
                os_mock.path.exists.side_effect = exists_side_effect
                os_mock.sep = '/'
                wgt_file = self.build_simple_wgt(other_files=('doc/folder1/', 'doc/folder1/file1', 'doc/folder1/file2', 'doc/folder2/folder3/file3'))
                wgt_file.extract_dir('doc/', '/tmp/test')

                self.assertEqual(os_mock.makedirs.call_count, 1)
                self.assertEqual(os_mock.mkdir.call_count, 3)
                self.assertEqual(open_mock.call_count, 3)

    def test_extract(self):

        with patch('wirecloud.commons.utils.wgt.os', autospec=True) as os_mock:
            with patch('wirecloud.commons.utils.wgt.open', create=True) as open_mock:
                os_mock.path.normpath = os.path.normpath
                os_mock.path.exists.return_value = False
                os_mock.sep = '/'
                wgt_file = self.build_simple_wgt(other_files=('folder1/', 'folder2/'))
                wgt_file.extract('/tmp/test')
                self.assertEqual(os_mock.mkdir.call_count, 3)
                self.assertEqual(open_mock.call_count, 2)

    def test_extract_inexistent_file(self):

        with patch('wirecloud.commons.utils.wgt.os', autospec=True) as os_mock:
            with patch('wirecloud.commons.utils.wgt.open', create=True) as open_mock:
                os_mock.path.normpath = os.path.normpath
                wgt_file = self.build_simple_wgt()
                self.assertRaises(KeyError, wgt_file.extract_file, 'doc/index.md', '/tmp/test')
                self.assertEqual(os_mock.makedirs.call_count, 0)
                self.assertEqual(os_mock.mkdir.call_count, 0)
                self.assertEqual(open_mock.call_count, 0)

    def test_invalid_file(self):

        with self.assertRaises(ValueError):
            self.build_simple_wgt(other_files=('../../invalid1.html',))

        with self.assertRaises(ValueError):
            self.build_simple_wgt(other_files=('folder1/../../invalid2.html',))

        with self.assertRaises(ValueError):
            self.build_simple_wgt(other_files=('/invalid3.html',))


class HTTPUtilsTestCase(TestCase):

    tags = ('wirecloud-http-utils',)

    def test_build_sendfile_response(self):

        with patch('wirecloud.commons.utils.http.os.path.isfile', return_value=True):
            response = build_sendfile_response('file.js', '/folder')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response['X-Sendfile'], '/folder/file.js')

    def test_build_sendfile_response_remove_extra_path_separators(self):

        with patch('wirecloud.commons.utils.http.os.path.isfile', return_value=True) as isfile_mock:
            response = build_sendfile_response('js///file.js', '/folder')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response['X-Sendfile'], '/folder/js/file.js')
            isfile_mock.assert_called_once_with('/folder/js/file.js')

    def test_build_sendfile_response_not_found(self):

        with patch('wirecloud.commons.utils.http.os.path.isfile', return_value=False) as isfile_mock:
            self.assertRaises(Http404, build_sendfile_response, 'js/notfound.js', '/folder')

    def test_build_sendfile_response_redirect_on_invalid_path(self):

        response = build_sendfile_response('../a/../file.js', '/folder')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], 'file.js')
