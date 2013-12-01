#!/usr/bin/python
# -*- encoding: utf-8 -*-
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import logging
import argparse
import os.path
from xml.etree import ElementTree
import MySQLdb as mdb
import re

class MagentoImageCleanup:

    LOCAL_XML = "app/etc/local.xml"
    MEDIA_PRODUCT = "media/catalog/product"
    log = logging.getLogger("ImageCleanup")

    EXTENSIONS = re.compile(r'.+\.(jpe?g|gif|png)$')

    def __init__(self):
        pass

    def parse(self):
        parser = argparse.ArgumentParser(description='magentoimagecleanup')
        parser.add_argument('--dry-run', action='store_true', default=False,
                            help='dry run')
        parser.add_argument('-v', '--verbose', action='store_true', default=False)
        parser.add_argument('magentoPath', metavar='MAGENTOPATH',
                            help='base path of magento')
        parser.add_argument('--force-host', metavar='HOST', help="force this host")
        args = parser.parse_args()
        self.magentoPath = args.magentoPath
        self.really = not args.dry_run
        self.force_host = args.force_host
        logging.basicConfig(level=(logging.DEBUG if args.verbose else logging.INFO))

    @staticmethod
    def sizeof_fmt(num):
        for x in ['bytes','KB','MB','GB']:
            if num < 1024.0 and num > -1024.0:
                return "%3.1f %s" % (num, x)
            num /= 1024.0
        return "%3.1f %s" % (num, 'TB')

    def getAllImagePath(self):
        tree = ElementTree.parse(os.path.join(self.magentoPath, self.LOCAL_XML))
        username = tree.find(".//connection/username").text
        password = tree.find(".//connection/password").text
        database = tree.find(".//connection/dbname").text
        hostname = tree.find(".//connection/host").text
        prefix = tree.find(".//db/table_prefix").text

        # fixes
        prefix = prefix if prefix else ''
        if self.force_host:
            hostname = self.force_host

        self.log.info("connect to mysql(host=%s, db=%s, user=%s)",
                      hostname, database, username)
        conn = mdb.connect(host=hostname, user=username, passwd=password, db=database)

        cur = conn.cursor()
        cur.execute("SELECT value FROM %(prefix)scatalog_product_entity_media_gallery"
                    % {'prefix':prefix})
        images = {}
        for v in cur.fetchall():
            images[v[0]] = True
        cur.close()
        conn.close()
        self.log.info("fetched %d image paths" % (len(images), ))
        return images

    def run(self):
        images = self.getAllImagePath()

        productsPath = os.path.join(self.magentoPath, self.MEDIA_PRODUCT)
        index = len(productsPath)

        size = 0
        removed = 0
        for dirname, dirnames, filenames in os.walk(productsPath):
            for filename in filenames:
                if self.EXTENSIONS.match(filename):
                    path =  os.path.join(dirname, filename)
                    value = path[index:]
                    if not images.has_key(value):
                        filesize = os.path.getsize(path)
                        if self.really:
                            self.log.debug('remove %s', path)
                            try:
                                os.unlink(path)
                            except OSError, e:
                                self.log.error("error %s", e)
                                continue
                        else:
                            self.log.debug('don\'t remove %s (dry-run)', path)
                        size += filesize
                        removed += 1
                else:
                    self.log.warn("unknown file type: %s", os.path.join(dirname, filename))

            for name in dirnames:
                if 'cache' in name or 'google' in name:
                    self.log.debug("skip %s", os.path.join(dirname, name))
                    dirnames.remove(name)
        self.log.info("removed %d files, saved %s", removed, self.sizeof_fmt(size))

if __name__ == "__main__":
    cleanup = MagentoImageCleanup()
    cleanup.parse()
    cleanup.run()
