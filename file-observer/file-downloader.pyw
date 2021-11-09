import os
import ftplib
import logging
import argparse
import ctypes.wintypes
from datetime import datetime
from dateutil import parser

CSIDL_PERSONAL = 5  # My Documents
SHGFP_TYPE_CURRENT = 0
buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
ctypes.windll.shell32.SHGetFolderPathW(0, CSIDL_PERSONAL, 0, SHGFP_TYPE_CURRENT, buf)
logging.basicConfig(filename=buf.value + '/logs/file-observer.log', format='%(asctime)s | %(levelname)s | %(message)s', datefmt='%d-%m-%Y %H:%M:%S', level=logging.INFO)


def check_timestamp_of_file(filename, ftp_host, ftp_user, ftp_pass, ftp_dir):  # check modified time of files, if file in ftp is newer fun will retr it to local storage
    local_timestamp = datetime.strptime(datetime.fromtimestamp(os.path.getmtime(f'{filename}')).strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')
    ftp_session = _get_ftp_connection(ftp_host, ftp_user, ftp_pass)
    ftp_session.cwd(ftp_dir)
    ftp_timestamp = ftp_session.voidcmd('MDTM ' + filename)[4:].strip()
    ftp_timestamp = parser.parse(ftp_timestamp)
    difference_between_timestamps = divmod((ftp_timestamp - local_timestamp).total_seconds(), 60)
    if local_timestamp < ftp_timestamp and difference_between_timestamps[0] > 2.0:
        download_file(ftp_session, filename)
        ftp_session.quit()
        return True
    else:
        ftp_session.quit()
        return False


def download_file(ftp_session, filename):
    with open(filename, 'wb') as file:
        ftp_session.retrbinary(f'RETR {filename}', file.write)


def _get_ftp_connection(host, user, password):
    ftp_session = ftplib.FTP(host)
    ftp_session.login(user, password)
    return ftp_session


def parse_args():
    parser = argparse.ArgumentParser(description='Checks if modified time of file on dest ftp server is newer than local file with that same name')
    parser.add_argument('--fname', help='filename', type=str, required=True)
    parser.add_argument('--ftpHost', help='address of ftp host', type=str, required=True)
    parser.add_argument('--ftpUser', help='username of ftp host', type=str, required=True)
    parser.add_argument('--ftpPass', help='password of ftp host', type=str, required=True)
    parser.add_argument('--ftpDir', help='dest dir to check of ftp host', type=str, required=True)
    return parser.parse_args()


if __name__ == "__main__":
    logging.info(f'[{os.path.basename(__file__)} started]')
    args = parse_args()
    if check_timestamp_of_file(args.fname, args.ftpHost, args.ftpUser, args.ftpPass, args.ftpDir):
        logging.info(f'[FTP->LOCAL] fname={args.fname}; ftpHost={args.ftpHost}')