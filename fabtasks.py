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

from fabric.api import local, task
from fabfile import _config, _get_source

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
    """
    Create clusters for groups of zoom levels. It needs to be added to the config.ini
    """
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
