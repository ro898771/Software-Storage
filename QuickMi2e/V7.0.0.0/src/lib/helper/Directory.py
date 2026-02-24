"""Directory and file management utilities."""

import os
import shutil
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor


class Directory:
    """Manages directory operations including file extraction and cleanup."""

    def __init__(self):
        """Initialize Directory with default cntrace path."""
        self.__cntrace_dir = os.path.join(
            os.getcwd(), 'dataset', 'cntrace', 'zip'
        )

    def rename_and_unzip(self, file_path, extract_to):
        """
        Rename tiger/cntrace files to zip and extract them.

        Args:
            file_path: Source directory containing tiger/cntrace files
            extract_to: Destination directory for extraction
        """
        filtered_files = [
            x for x in os.listdir(file_path)
            if x.endswith(('.tiger', '.cntrace'))
        ]

        def process_file(sample):
            """Process individual file: rename to .zip and extract."""
            fullpath = os.path.join(file_path, sample)
            base_path, ext = os.path.splitext(fullpath)

            if ext != ".zip":
                new_file_path = base_path + '.zip'
                os.rename(fullpath, new_file_path)
            else:
                new_file_path = fullpath
                print("It is already zip file.")

            with zipfile.ZipFile(new_file_path, 'r') as zip_ref:
                zip_ref.extractall(extract_to)

        with ThreadPoolExecutor() as executor:
            executor.map(process_file, filtered_files)

        print(f"All files in '{file_path}' have been successfully "
              f"renamed and unzipped to '{extract_to}'.")

    def rename_and_unzip_scat(self, file_path, extract_to):
        """
        Rename scat files to zip and extract them to separate folders.

        Args:
            file_path: Source directory containing scat files
            extract_to: Destination directory for extraction
        """
        filtered_files = [
            x for x in os.listdir(file_path)
            if x.endswith('.scat')
        ]
        file_names = [
            os.path.join(extract_to, os.path.splitext(x)[0])
            for x in filtered_files
        ]
        for x in file_names:
            os.makedirs(x, exist_ok=True)

        def process_file(sample):
            """Process individual scat file: rename to .zip and extract."""
            fullpath = os.path.join(file_path, sample)
            base_path, ext = os.path.splitext(fullpath)
            text = os.path.splitext(os.path.basename(fullpath))[0]

            if ext != ".zip":
                new_file_path = base_path + '.zip'
                os.rename(fullpath, new_file_path)
            else:
                new_file_path = fullpath
                print("It is already zip file.")

            with zipfile.ZipFile(new_file_path, 'r') as zip_ref:
                dirpath = os.path.join(extract_to, text)
                zip_ref.extractall(dirpath)

        with ThreadPoolExecutor() as executor:
            executor.map(process_file, filtered_files)

    def set_cntrace_path(self, path):
        """
        Set the cntrace directory path.

        Args:
            path: New path for cntrace directory
        """
        self.__cntrace_dir = path

    def get_zip_name(self, file_path):
        """
        Extract the base name from a file path without extension.

        Args:
            file_path: Full path to the file

        Returns:
            Base name without extension
        """
        file_name_with_extension = os.path.basename(file_path)
        name, _ = os.path.splitext(file_name_with_extension)
        return name

    def delete_all_files_and_subfolders(self, folder_path):
        """
        Delete all files and subfolders in the specified folder.

        Args:
            folder_path: Path to folder to clean
        """
        def delete_item(item):
            """Delete individual file or folder."""
            item_path = os.path.join(folder_path, item)

            if os.path.isfile(item_path):
                os.remove(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)

        with ThreadPoolExecutor() as executor:
            executor.map(delete_item, os.listdir(folder_path))

        print(f"All files and subfolders in '{folder_path}' "
              f"have been deleted.")

    def copy_file(self, src):
        """
        Copy all files from source to cntrace directory.

        Args:
            src: Source directory path
        """
        all_files = [os.path.join(src, x) for x in os.listdir(src)]

        with ThreadPoolExecutor() as executor:
            executor.map(
                lambda srcmove: shutil.copy2(srcmove, self.__cntrace_dir),
                all_files
            )

        print(f"'{src}' has been successfully copied to "
              f"'{self.__cntrace_dir}'.")


if __name__ == "__main__":
    # Example usage
    start_time = time.time()

    # Define paths
    project_root = os.getcwd()
    data_source = os.path.join(
        project_root, 'Box', 'Buster 2did SKEW Trace',
        'SamplingTesting-QuickMi2ce', 'scat'
    )
    save_path = os.path.join(project_root, 'dataset', 'results')
    src = os.path.join(project_root, 'dataset', 'cntrace', 'zip')
    dest = os.path.join(project_root, 'dataset', 'cntrace', 'trace')

    # Create Directory instance
    obj = Directory()

    # Clean directories
    obj.delete_all_files_and_subfolders(src)
    obj.delete_all_files_and_subfolders(dest)
    obj.delete_all_files_and_subfolders(save_path)

    # Copy and process files
    obj.copy_file(data_source)
    end_time1 = time.time()
    elapsed_time1 = end_time1 - start_time
    print(f"Copy Elapsed Time: {elapsed_time1}")

    obj.rename_and_unzip_scat(src, dest)

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Elapsed Time: {elapsed_time}")