import zipfile


def unzip_file(zip_file_path: str, unzip_dir_path: str) -> bool:
    """
    解压一个压缩包
    :param zip_file_path: 压缩包文件的路径。
    :param unzip_dir_path: 解压位置的文件夹
    :return: 是否解压成功
    """
    try:
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extractall(unzip_dir_path)
        return True
    except Exception:
        return False