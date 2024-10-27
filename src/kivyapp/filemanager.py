"""
Contains a file manager: UploadFileManager.

NOTE: this module is private. All functions and objects are available in the main
`readpub` namespace - use that instead.

"""

import os

from kivy.metrics import dp
from kivymd.uix.filemanager import MDFileManager
from kivymd.uix.list.list import MDListItem


class UploadFileManagerItem(MDListItem):
    """Base class for folders and files icons."""


class UploadFileManagerItemPreview(MDListItem):
    """Base class for folder icons and thumbnails images in `preview` mode."""


class UploadFileManager(MDFileManager):
    """File manger for uploading books."""

    def show(self, path: str) -> None:
        """
        Forms the body of a directory tree.

        :param path:
            The path to the directory that will be opened in the file manager.
        """

        self.current_path = path
        self.selection = []
        dirs, files = self.get_content()
        manager_list = []

        if dirs == [] and files == []:  # selected directory
            pass
        elif not dirs and not files:  # directory is unavailable
            return

        if self.preview:
            for name_dir in self._MDFileManager__sort_files(dirs):
                manager_list.append(
                    {
                        "viewclass": "UploadFileManagerItemPreview",
                        "path": self.icon_folder,
                        "realpath": os.path.join(path),
                        "type": "folder",
                        "name": name_dir,
                        "events_callback": self.select_dir_or_file,
                        "height": dp(150),
                        "_selected": False,
                    }
                )
            for name_file in self._MDFileManager__sort_files(files):
                if os.path.splitext(os.path.join(path, name_file))[1] in self.ext:
                    manager_list.append(
                        {
                            "viewclass": "UploadFileManagerItemPreview",
                            "path": os.path.join(path, name_file),
                            "name": name_file,
                            "type": "files",
                            "events_callback": self.select_dir_or_file,
                            "height": dp(150),
                            "_selected": False,
                        }
                    )
        else:
            for name in self._MDFileManager__sort_files(dirs):
                _path = os.path.join(path, name)
                access_string = self.get_access_string(_path)
                if "r" not in access_string:
                    icon = "folder-lock"
                else:
                    icon = "folder"

                manager_list.append(
                    {
                        "viewclass": "UploadFileManagerItem",
                        "path": _path,
                        "icon": icon,
                        "dir_or_file_name": name,
                        "events_callback": self.select_dir_or_file,
                        "icon_color": (
                            self.theme_cls.primaryColor
                            if not self.icon_color
                            else self.icon_color
                        ),
                        "_selected": False,
                    }
                )
            for name in self._MDFileManager__sort_files(files):
                if self.ext and os.path.splitext(name)[1] not in self.ext:
                    continue

                manager_list.append(
                    {
                        "viewclass": "UploadFileManagerItem",
                        "path": name,
                        "icon": "file-outline",
                        "dir_or_file_name": os.path.split(name)[1],
                        "events_callback": self.select_dir_or_file,
                        "icon_color": (
                            self.theme_cls.primaryColor
                            if not self.icon_color
                            else self.icon_color
                        ),
                        "_selected": False,
                    }
                )

        self.ids.rv.data = manager_list
        self._show()
