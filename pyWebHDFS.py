#!/usr/bin/env python
#-*- coding: utf-8 -*-
"""A wrapper library to access Hadoop HTTP REST API"""

__author__ = 'fsoutomoure@gmail.com'
__version__ = '0.2'

import requests
try:
    import json  # Python >= 2.6
except ImportError:
    try:
        import simplejson as json  # Python < 2.6
    except ImportError:
        try:
            from django.utils import simplejson as json
        except ImportError:
            raise ImportError("Unable to load a json library")

CONTEXT_ROOT = '/webhdfs/v1'
OFFSET = 32768  # Default offset in bytes


class pyWebHDFSException(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class pyWebHDFS(object):

    def __init__(self, host, port, username=None):
        self.host = host
        self.port = port
        self.user = username
        self.namenode_url = 'http://%s:%s%s' % (host, port, CONTEXT_ROOT)

    def _query(self, method, path, params, allow_redirects=False):
        """
        Make an HTTP request formatting the parameters as required
        """
        params['user.name'] = 'fabio'
        r = requests.request(method, "%s%s" % (self.namenode_url, path), params=params, allow_redirects=allow_redirects)
        r.raise_for_status()
        return r

    def listdir(self, path):
        """
        List all the contents of a directory

        :param path: path of the directory
        :returns: a list of fileStatusProperties:
        http://hadoop.apache.org/common/docs/r1.0.0/webhdfs.html#fileStatusProperties False on error
        """
        params = {'op': 'LISTSTATUS'}
        r = self._query(method='get', path=path, params=params)

        if r.status_code == 200:
            r_data = json.loads(r.text)
            return r_data['FileStatuses']['FileStatus']
        else:
            return False

    def mkdir(self, path, permission=None):
        """
        Create a directory hierarchy, like the unix command mkdir -p

        :param path: the path of the directory
        :param permission: dir permissions in octal (0-777)
        """
        params = {
            'op': 'MKDIRS',
            'permission': permission
        }
        self._query(method='put', path=path, params=params)

    def remove(self, path, recursive=False):
        """
        Delete a file o directory

        :param path: path of the file or dir to delete
        :param recursive: true to delete the content in subdirectories
        """
        params = {
            'op': 'DELETE',
            'recursive': recursive
        }
        r = self._query(method='delete', path=path, params=params)

    def rename(self, src, dst):
        """
        Rename a file or directory

        :param src: path of the file or dir to rename
        :param dst: path of the final file/dir
        """
        params = {
            'op': 'RENAME',
            'destination': dst
        }
        r = self._query(method='put', path=src, params=params)

    def environ_home(self):
        """
        :returns: the home directory of the user
        """
        params = {'op': 'GETHOMEDIRECTORY'}
        r = self._query(method='get', path='/', params=params)
        r_data = json.loads(r.text)
        return r_data['Path']

    def open(self, path, offset=None, length=None, buffersize=None):
        """
        Open a file to read

        Untested
        """
        params = {
            'op': 'OPEN',
            'offset': offset,
            'length': length,
            'buffersize': buffersize
        }
        r = self._query(method='get', path=path, params=params, allow_redirects=True)
        return r.text

    def status(self, path):
        """
        Returns the status of a file/dir

        :param path: path of the file/dir
        :returns: a FileStatus dictionary on success, false otherwise
        """
        params = {'op': 'GETFILESTATUS'}
        r = self._query(method='get', path=path, params=params, allow_redirects=True)

        if r.status_code == 200:
            r_data = json.loads(r.text)
            return r_data['FileStatus']
        return False

    def chmod(self, path, permission):
        """
        Set the permissions of a file or directory

        :param path: path of the file/dir
        :param permission: dir permissions in octal (0-777)
        """
        params = {
            'op': 'SETPERMISSION',
            'permission': permission
        }
        r = self._query(method='put', path=path, params=params)
        if r.status_code == 200:
            return True
        return False

    def create(self, path, file_data, overwrite=None):
        """
        Create a new file in HDFS with the content of file_data

        https://hadoop.apache.org/docs/r1.0.4/webhdfs.html#CREATE

        :param path: the file path to create the file
        :param data: the data to write to the
        """
        params = {
            'op': 'CREATE',
            'overwrite': overwrite
        }
        r = self._query(method='put', path=path, params=params, allow_redirects=False)
        datanode_url = r.headers['location']

        r = requests.put(datanode_url, data=file_data, headers={'content-type': 'application/octet-stream'})
        if r.status_code == 403:
            print "Launch exception 403: The file already exists"
            return False
        return True

    def append(self, path, file_data, buffersize=None):
        """
        Append file_data to a file

        To enable append on HDFS you need to configure your hdfs-site.xml as follows:
            <property>
                <name>dfs.support.append</name>
                <value>true</value>
            </property>
        """
        params = {'op': 'APPEND'}
        r = self._query(method='post', path=path, params=params)
        datanode_url = r.headers['location']

        r = requests.post(datanode_url, data=file_data, params=params)
        if r.status_code == 200:
            return True
        return False

if __name__ == "__main__":
    webHDFS = pyWebHDFS("localhost", 50070, "fabio")
    print webHDFS.environ_home()