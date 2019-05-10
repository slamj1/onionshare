import os
import sys
import tempfile
import mimetypes
from flask import Response, request, render_template, make_response, send_from_directory
from flask_httpauth import HTTPBasicAuth

from .. import strings


class WebsiteModeWeb(object):
    """
    All of the web logic for share mode
    """
    def __init__(self, common, web):
        self.common = common
        self.common.log('WebsiteModeWeb', '__init__')

        self.web = web
        self.auth = HTTPBasicAuth()

        # Dictionary mapping file paths to filenames on disk
        self.files = {}
        self.visit_count = 0

        # Reset assets path
        self.web.app.static_folder=self.common.get_resource_path('static')

        self.users = { }

        self.define_routes()

    def define_routes(self):
        """
        The web app routes for sharing a website
        """

        @self.auth.get_password
        def get_pw(username):
            self.users['onionshare'] = self.web.slug

            if username in self.users:
                return self.users.get(username)
            else:
                return None

        @self.web.app.before_request
        def conditional_auth_check():
            if not self.common.settings.get('public_mode'):
                @self.auth.login_required
                def _check_login():
                    return None

                return _check_login()

        @self.web.app.route('/<path:page_path>')
        def path_public(page_path):
            return path_logic(page_path)

        @self.web.app.route("/")
        def index_public():
            return path_logic('')

        def path_logic(path=''):
            """
            Render the onionshare website.
            """

            # Each download has a unique id
            visit_id = self.visit_count
            self.visit_count += 1

            # Tell GUI the page has been visited
            self.web.add_request(self.web.REQUEST_STARTED, path, {
                'id': visit_id,
                'action': 'visit'
            })

            # Removing trailing slashes, because self.files doesn't have them
            path = path.rstrip('/')

            if path in self.files:
                filesystem_path = self.files[path]

                # If it's a directory
                if os.path.isdir(filesystem_path):
                    # Is there an index.html?
                    index_path = os.path.join(path, 'index.html')
                    if index_path in self.files:
                        # Render it
                        dirname = os.path.dirname(self.files[index_path])
                        basename = os.path.basename(self.files[index_path])
                        return send_from_directory(dirname, basename)

                    else:
                        # Otherwise, render directory listing
                        filenames = os.listdir(filesystem_path)
                        filenames.sort()

                        files = []
                        dirs = []

                        for filename in filenames:
                            this_filesystem_path = os.path.join(filesystem_path, filename)
                            is_dir = os.path.isdir(this_filesystem_path)

                            if is_dir:
                                dirs.append({
                                    'basename': filename
                                })
                            else:
                                size = os.path.getsize(this_filesystem_path)
                                size_human = self.common.human_readable_filesize(size)
                                files.append({
                                    'basename': filename,
                                    'size_human': size_human
                                })

                        r = make_response(render_template('listing.html',
                            path=path,
                            files=files,
                            dirs=dirs))
                        return self.web.add_security_headers(r)

                # If it's a file
                elif os.path.isfile(filesystem_path):
                    dirname = os.path.dirname(filesystem_path)
                    basename = os.path.basename(filesystem_path)
                    return send_from_directory(dirname, basename)

                # If it's not a directory or file, throw a 404
                else:
                    return self.web.error404()
            else:
                # If the path isn't found, throw a 404
                return self.web.error404()


    def set_file_info(self, filenames):
        """
        Build a data structure that describes the list of files that make up
        the static website.
        """
        self.common.log("WebsiteModeWeb", "set_file_info")

        # This is a dictionary that maps HTTP routes to filenames on disk
        self.files = {}

        # If there's just one folder, replace filenames with a list of files inside that folder
        if len(filenames) == 1 and os.path.isdir(filenames[0]):
            filenames = [os.path.join(filenames[0], x) for x in os.listdir(filenames[0])]

        # Loop through the files
        for filename in filenames:
            basename = os.path.basename(filename.rstrip('/'))

            # If it's a filename, add it
            if os.path.isfile(filename):
                self.files[basename] = filename

            # If it's a directory, add it recursively
            elif os.path.isdir(filename):
                for root, _, nested_filenames in os.walk(filename):
                    # Normalize the root path. So if the directory name is "/home/user/Documents/some_folder",
                    # and it has a nested folder foobar, the root is "/home/user/Documents/some_folder/foobar".
                    # The normalized_root should be "some_folder/foobar"
                    normalized_root = os.path.join(basename, root.lstrip(filename)).rstrip('/')

                    # Add the dir itself
                    self.files[normalized_root] = filename

                    # Add the files in this dir
                    for nested_filename in nested_filenames:
                        self.files[os.path.join(normalized_root, nested_filename)] = os.path.join(root, nested_filename)

        return True
