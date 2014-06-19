import os
#import geojson
#import psycopg2
#import sys

from fabric.api import local, task
from fabfile import _config

@task
def convert_db_json():
    """
    Convert database to geojson
    """
    file_name = 'out.json'
    if os.path.exists(file_name):
        local('rm {0}'.format(file_name))
    cmd = 'ogr2ogr -f GeoJSON {0} "PG:host=localhost dbname={1} user={2} password={3} port={4}" -sql "select id, location from position_infos"'.format(
        file_name,
        _config('name', section='db'),
        _config('user', section='db'),
        _config('password', section='db'),
        _config('port', section='db')
    );
    local(cmd)
