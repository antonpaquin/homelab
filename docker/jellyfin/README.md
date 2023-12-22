Jellyfin *really* needs local storage for sqlite db
Which is actually kinda small (I'm reading 84Mi)
But I want it to live on nfs anyway

Solution: nfs-mount jellyfin db to some arbitrary spot
At container-start, copy over the db files to container-local storage
And periodically (minute? inotify?) rsync back to the nfs
