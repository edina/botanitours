#### Install kmeans:

```
$ wget http://api.pgxn.org/dist/kmeans/1.1.0/kmeans-1.1.0.zip
$ unzip kmeans-1.1.0.zip
$ cd kmeans-1.1.0/
$ export USE_PGXS=1
$ make
$ sudo make install
$ psql -f /usr/share/postgresql/9.1/extension/kmeans.sql -U postgres -d <database>
```
