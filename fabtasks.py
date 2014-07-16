"""
Copyright (c) 2014, EDINA,
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice, this
   list of conditions and the following disclaimer in the documentation and/or
   other materials provided with the distribution.
3. All advertising materials mentioning features or use of this software must
   display the following acknowledgement: This product includes software
   developed by the EDINA.
4. Neither the name of the EDINA nor the names of its contributors may be used to
   endorse or promote products derived from this software without specific prior
   written permission.

THIS SOFTWARE IS PROVIDED BY EDINA ''AS IS'' AND ANY EXPRESS OR IMPLIED
WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT
SHALL EDINA BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
DAMAGE.
"""

import ast
import os

from fabric.api import lcd, local, task
from fabfile import install_project, update_app, _config, _get_runtime, _get_source, _make_dir, _path_join

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
def test():
    _path_join(_get_source()[2], 'www', 'data', '')

@task
def convert_db_sqlite():
    """
    Convert database to sqlite database
    """
    file_name = os.path.join(
        _get_source()[1],
        'platforms',
        'android',
        'assets',
        'db',
        'botanitours.sqlite')

    if os.path.exists(file_name):
        local('rm {0}'.format(file_name))
    cmd = 'ogr2ogr -preserve_fid -f SQLite -dsco SPATIALITE=yes {0} "PG:host=localhost dbname={1} user={2} password={3} port={4}" gardens plant_common_names plant_images plants position_infos'.format(
        file_name,
        _config('name', section='db'),
        _config('user', section='db'),
        _config('password', section='db'),
        _config('port', section='db')
    );
    local(cmd)

    update_app()

@task
def create_clusters():
    """
    Create clusters for groups of zoom levels. The number of clusters for each zoom level needs to be added to the config.ini
    e.g.
    clusters = {"0-6": 1, "7-9": 5, "9-12": 10, "12-18": 0}
    """
    data_dir = _path_join(_get_source()[2], 'www', 'data', '')

    layers = ast.literal_eval(_config('clusters', section='db'))
    for key, cluster in layers.items():
        zooms = key.split("-")
        for zoom in range(int(zooms[0]), int(zooms[1])+1):
            print zoom
            local(_create_cluster('{0}cluster'.format(data_dir), zoom, cluster))

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

@task
def install_botanitours(dist_dir='apps', target='local'):
    install_project(dist_dir=dist_dir, target='local')
    dist_path = os.sep.join((os.environ['HOME'], dist_dir))
    runtime = _get_runtime(target)[1]

    with lcd(dist_path):
        # spatialite
        dir_name = 'spatialite-for-android-3.0.1'
        if not os.path.exists(os.path.join(dist_path, dir_name)):
            file_name = '{0}.zip'.format(dir_name)
            url = 'http://www.gaia-gis.it/gaia-sins/spatialite-android/spatialite-for-android-3.0.1.zip'
            local('wget {0}'.format(url))
            local('unzip {0}'.format(file_name))
            local('rm {0}'.format(file_name))
        from_dir = os.path.join(
                dir_name,
                'spatialite-for-android',
                'spatialite-android',
                'spatialite-android-library',
                'libs',
                '')

        to_dir = os.path.join(
                runtime,
                'platforms',
                'android',
                'libs',
                '')
        local('cp -r {0}* {1}'.format(from_dir, to_dir))
