# Storage Analyzer
[![Docker Image Version](https://img.shields.io/docker/v/caco3x/storage-analyzer)](https://hub.docker.com/r/caco3x/storage-analyzer/)
[![Docker Pulls](https://img.shields.io/docker/pulls/caco3x/storage-analyzer.svg)](https://hub.docker.com/r/caco3x/storage-analyzer/)
[![Docker Image Size](https://img.shields.io/docker/image-size/caco3x/storage-analyzer?sort=date)](https://hub.docker.com/r/caco3x/storage-analyzer/)

This tool uses [Duc](https://duc.zevv.nl/) to provide a generic Storage Analyzer like provided by [Synology](https://www.synology.com/en-us/dsm/packages/StorageAnalyzer) to analyze the storage usage of a system. It's main goal is to to provide a storage usage overview on a NAS, how ever it could also work on any system which provides docker.

![Screenshot](Screenshot1.png)

The built docker images can be found on [Docker Hub](https://hub.docker.com/r/caco3x/storage-analyzer/).

# Features
- Included scheduling for automatic scanning
- Single-command deployment
- Very small image footprint
- Web UI to view and manage the snapshots
- Easy navigation through directories and snapshots
- Manual scan trigger
- Log output of the last scan

## Usage Examples
### With Docker Compose
See [docker-compose.yml](docker-compose.yml).

Run it with 
```
docker compose up --build --detach
```

This compose file also mounts a persistent volume to `/config` so settings (e.g. the scan parameters) survive container rebuild/removal.
And the `/snapshots` volume is mounted to persist the snapshots.

### Without Docker Compose
```
docker run \
    -p 80:80 \
    --mount type=bind,src=/,dst=/scan,readonly \
    --mount type=volume,src=snapshots,dst=/snapshots \
    --mount type=volume,src=config,dst=/config \
    caco3x/storage-analyzer
```

If you don't want to scan the ehole root but just some subfolders, use
```
docker run \
    -p 80:80 \
    --mount type=bind,src=/volume1,dst=/scan/volume1,readonly \
    --mount type=bind,src=/volume2,dst=/scan/volume2,readonly \
    --mount type=volume,src=snapshots,dst=/snapshots \
    --mount type=volume,src=config,dst=/config \
    caco3x/storage-analyzer
```

## Needed volumes
 - ### /config
   Persisted configuration directory. Mount this path to keep settings across container rebuild/removal.

   Currently persisted settings:
   - `/config/schedule` (scan schedule)
   - `/config/exclude` (exclude patterns)

 - ### /snapshots
   Persisted snapshots directory. Mount this path to keep snapshots across container rebuild/removal.

 - ### /scan
   The scan directory. This is where the [DUC](https://duc.zevv.nl/) tool will scan for files and folders.
   
   If you want to scan the whole root partition, mount it to `/scan`.
   
   If you want to scan several folders, mount them to `/scan/folder1`, `/scan/folder2`, etc.

## Development
```bash
sudo docker run -it -p 8080:80 --mount type=bind,src=$PWD,dst=/scan,readonly -v $PWD/snapshots:/snapshots -v $PWD/app:/var/www/html --name storage-analyzer $(docker build -q .)
sudo docker stop storage-analyzer; sudo docker rm storage-analyzer
```

Now you can edit the files in the `app` folder without having to rebuild/start the docker container.

### Upload to dockerhub
Build, tag and publish:
```
docker buildx build . --file Dockerfile --tag caco3x/storage-analyzer:latest --load

sudo docker login -u caco3x
sudo docker push caco3x/storage-analyzer:latest
```

## References
- DUC homepage: https://duc.zevv.nl/

## Support

If you find this project useful, please consider supporting it by giving it a star on [GitHub](https://github.com/caco3x/storage-analyzer).

If you find an issue, please open an issue on [GitHub](https://github.com/caco3x/storage-analyzer/issues).

## Similar Projects
- https://github.com/MaximilianKoestler/duc-service
- https://hub.docker.com/r/tigerdockermediocore/duc-docker
- https://hub.docker.com/r/digitalman2112/duc
