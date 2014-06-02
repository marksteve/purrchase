# TadHack

## Redis

```bash
$ docker run -d --name tadhack-redis marksteve/redis
```

## App

### Build

```bash
$ docker build --rm -t tadhack .
```

### Run

```bash
$ docker run --rm -t -i \
  --link tadhack-redis:redis \
  -p 5000:5000 \
  -v `pwd`:/src tadhack \
  /bin/bash -il
```
