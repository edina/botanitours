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
import json
import os
import psycopg2

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
    cmd = 'ogr2ogr -f GeoJSON {0} "PG:host=localhost dbname={name} user={user} password={password} port={port}" -sql "select id, location from position_infos"'.format(
        file_name,
        **_config(section='db')
    )
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
    cmd = 'ogr2ogr -preserve_fid -f SQLite -dsco SPATIALITE=yes {0} "PG:host=localhost dbname={name} user={user} password={password} port={port}" gardens plant_common_names plant_images plants position_infos'.format(
        file_name,
        **_config(section='db')
    )
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

    layers = ast.literal_eval(_config('clusters', section='app'))

    clusters = set(layers.values())
    for cluster in clusters:
        _create_cluster('{0}'.format(data_dir), cluster)

    # create gardens geojson (non clustered)
    file_name = os.path.join(data_dir, 'Gardens.json')
    if os.path.exists(file_name):
        local('rm {0}'.format(file_name))
    cmd = 'ogr2ogr -f GeoJSON {0} "PG:host=localhost dbname={name} user={user} password={password} port={port}" -sql "SELECT positionable_id AS id, positionable_type AS type, location FROM position_infos WHERE positionable_type = \'Garden\'"'.format(
        file_name,
        **_config(section='db')
    )
    local(cmd)

def _create_cluster(name, cluster):

    def _get_details_from_point(point, properties):
        # get details of a point
        conn = psycopg2.connect("dbname={name} user={user} port={port} password={password}".format(**_config(section='db')))
        cur = conn.cursor()
        cur.execute("SELECT positionable_id, positionable_type, year FROM position_infos WHERE location = ST_GeomFromText('POINT(%s %s)')", point)
        entry = cur.fetchone()
        properties['id'] = entry[0]
        properties['type'] = entry[1]

        if entry[2] == None:
            properties['year'] = 'unknown'
        else:
            properties['year'] = entry[2]

        cur.close()
        conn.close()

    filters = ('', 'Plant')

    for filter in filters:
        filter_str = ''
        if len(filter) > 0:
            filter_str = "WHERE positionable_type = '{0}'".format(filter)

        file_name = "{0}{1}cluster{2}.json".format(name, filter, cluster)
        print file_name
        if os.path.exists(file_name):
            local('rm {0}'.format(file_name))
        cmd = 'ogr2ogr -f GeoJSON {0} "PG:host=localhost dbname={1} user={2} password={3} port={4}" -sql "SELECT count(*), ST_Centroid(ST_Collect(location::geometry)) AS geom FROM ( SELECT kmeans(ARRAY[ST_X(location::geometry), ST_Y(location::geometry)], {5}) OVER (), location FROM position_infos {6}) AS ksub GROUP BY kmeans ORDER BY kmeans"'.format(
            file_name,
            _config('name', section='db'),
            _config('user', section='db'),
            _config('password', section='db'),
            _config('port', section='db'),
            cluster,
            filter_str)
        local(cmd)

        # check if any clusters have a count of 1
        has_changed = None
        features = None
        with open(file_name, 'rw') as f:
            features = json.load(f)['features']
            for feature in features:
                if feature['properties']['count'] == 1:
                    # cluster has a count of 1, get more details
                    has_changed = True
                    _get_details_from_point(
                        feature['geometry']['coordinates'],
                        feature['properties'])

        if has_changed:
            with open(file_name, 'w') as f:
                out = {
                    'type': 'FeatureCollection',
                    'features': features
                }
                json.dump(out, f)


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
