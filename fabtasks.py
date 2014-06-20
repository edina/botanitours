import os, ast

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

@task
def convert_db_sqlite():
    file_name = 'botanitours.sqlite'
    if os.path.exists(file_name):
        local('rm {0}'.format(file_name))
    cmd = 'ogr2ogr -f SQLite -dsco SPATIALITE=yes {0} "PG:host=localhost dbname={1} user={2} password={3} port={4}" '.format(
        file_name,
        _config('name', section='db'),
        _config('user', section='db'),
        _config('password', section='db'),
        _config('port', section='db')
    );
    local(cmd)

@task
def create_clusters():
    layers = ast.literal_eval(_config('clusters', section='db'))
    for key, cluster in layers.items():
        zooms = key.split("-")
        for zoom in range(int(zooms[0]), int(zooms[1])+1):
            print zoom
            local(_create_cluster('cluster', zoom, cluster))

def _create_cluster(name, zoom, cluster):
    file_name = "{0}{1}.json".format(name, cluster)
    if os.path.exists(file_name):
        local('rm {0}'.format(file_name))
    cmd = 'ogr2ogr -f GeoJSON {0} "PG:host=localhost dbname={1} user={2} password={3} port={4}" -sql "SELECT kmeans, count(*), ST_Centroid(ST_Collect(location::geometry)) AS geom FROM ( SELECT kmeans(ARRAY[ST_X(location::geometry), ST_Y(location::geometry)], {5}) OVER (), location FROM position_infos ) AS ksub GROUP BY kmeans ORDER BY kmeans"'.format(
        file_name,
        _config('name', section='db'),
        _config('user', section='db'),
        _config('password', section='db'),
        _config('port', section='db'),
        cluster
    )
    return cmd