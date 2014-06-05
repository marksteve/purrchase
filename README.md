# TadHack

## Setup

1. Build

  ```bash
  $ docker build --rm -t tadhack .
  ```

2. [Install Fig](http://orchardup.github.io/fig/install.html)

3. Run

  ```bash
  $ fig up -d
  ```

## Widget

### Build

```bash
$ watchify -t reactify static/jsx/phonepay.js -o static/js/phonepay.js -v
```
