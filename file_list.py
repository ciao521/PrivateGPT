def get_file_list():

    import os
    import datetime

    # from .utilities import path_to_sandbox_folder
    # # could move to utilies.py into here
    # from .utilities import file_list_in_sandbox

    from .utilities import refresh_file
    path_to_sandbox_folder, file_list_in_sandbox = refresh_file()

    file_info_list = []
    for file_name in file_list_in_sandbox:
        file_path = os.path.join(path_to_sandbox_folder, file_name)
        if os.path.isfile(file_path):
            file_stat = os.stat(file_path)
            modified_time = datetime.datetime.fromtimestamp(file_stat.st_mtime)
            file_size = file_stat.st_size
            file_info = {
                'name': file_name,
                'modifiedTime': modified_time,
                'size': file_size
            }
            file_info_list.append(file_info)

    print(file_info_list)

    return file_info_list
