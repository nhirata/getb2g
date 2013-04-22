import os
import shutil
import tempfile
import urllib2

from bs4 import BeautifulSoup
from ..base import (Base, TestBase, B2GDesktopBase)
from ..mixins import TinderboxMixin, DateMixin

import mozfile
import mozinfo
import mozinstall

__all__ = ['NightlyFtpMOHandler']

class NightlyFtpMOHandler(Base, B2GDesktopBase, TestBase, TinderboxMixin, DateMixin):
    """
    Handles nightly builds from ftp.m.o/pub/mozilla.org/b2g/nightly
    """
    _base_url = 'http://ftp.mozilla.org/pub/mozilla.org/b2g/nightly'
    _device_names = { 'b2g_desktop' : 'b2g' }
    _platform = None
    suffix = 'tar.bz2'

    @property
    def url(self):
        if self._url:
            return self._url
        url = '%s/%s-%s/' % (self._base_url, '%s', self.branch)
        self._url = self.get_date_url(url)
        return self._url

    @property
    def platform(self):
        if not self._platform:
            self._platform = self.metadata.get('platform')
            if self._platform:
                return self._platform

            if mozinfo.isLinux:
                self._platform = 'linux-%s' % 'x86_64' if mozinfo.bits == 64 else 'i686'
                self.suffix = 'tar.bz2'
            elif mozinfo.isMac:
                self._platform = 'mac%s' % mozinfo.bits
                self.suffix = 'dmg'
            elif mozinfo.isWin:
                self._platform = 'win32'
                suffix = 'zip'
        return self._platform

    def prepare_b2g_desktop(self):
        url = self.get_resource_url(lambda x: x.string.startswith(self.device) and
                                                x.string.endswith('%s.%s' % (self.platform, self.suffix)))
        file_name = self.download_file(url)
        mozinstall.install(file_name, self.metadata['workdir'])
        os.remove(file_name)


    def prepare_tests(self):
        url = self.get_resource_url(lambda x: x.string.startswith(self.device) and
                                                x.string.endswith('%s.tests.zip' % self.platform))
        file_name = self.download_file(url)
        path = os.path.join(self.metadata['workdir'], 'tests')
        if os.path.isdir(path):
            shutil.rmtree(path)
        mozfile.extract(file_name, path)
        os.remove(file_name)
