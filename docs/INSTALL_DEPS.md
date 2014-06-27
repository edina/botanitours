Installing kmeans:

```
$ wget http://api.pgxn.org/dist/kmeans/1.1.0/kmeans-1.1.0.zip
$ unzip kmeans-1.1.0.zip
$ cd kmeans-1.1.0/
```

Before building, you need to set the USE_PGXS environment variable (my previous post instructed to delete this part of the Makefile, which wasn't the best of options). One of these two commands should work for your Unix shell:

```
# bash
$ export USE_PGXS=1
# csh
$ setenv USE_PGXS 1
```
Now build and install the extension:

```
$ make
$ sudo make install
$ psql -f /usr/share/postgresql/9.1/extension/kmeans.sql -U postgres -d <database>

```
