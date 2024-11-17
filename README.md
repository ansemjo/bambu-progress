# bambu-progress

Simple script using [bambu-connect](https://github.com/mattcar15/bambu-connect) and [textual](https://github.com/Textualize/textual) to show your BambuLab printer's current status in a terminal window with pretty progress bars and stuff. Sends a notification with `notify-send` when the print is finished.

![](screenshot.png)

[![No Maintenance Intended](https://unmaintained.tech/badge.svg)](https://unmaintained.tech/)<br>
_I do not intend to maintain this project for issues or pull requests. It is a personal project I published in case it's useful to somebody else._

### Usage

* Install requirements from `requirements.txt` into a vitualenv `.venv/`.
* Put `BAMBU_HOSTNAME`, `BAMBU_ACCESS_CODE` and `BAMBU_SERIAL` in a `.env` file. See [bambu-connect's instructions](https://github.com/mattcar15/bambu-connect?tab=readme-ov-file#setup) on how to get those.
* Run `./bambu-progress`.

### Other hints

The data is received as JSON blobs by subscribing to an MQTT topic on the BambuLab printer. This connection uses a selfsigned certificate, thus you need to configure your MQTT client to ignore TLS certificate errors.

For `mosquitto-sub`, you can use `openssl s_client` to receive the certificate chain and dump it to a file to use as a "trusted CA". I've done that on my printer, so you can use the following to receive raw messages:

```
mosquitto_sub --insecure --cafile bambu-ca.pem \
    -L mqtts://bblp:ACCESSCODE@HOSTNAME/device/SERIAL/report
```

Note that there appears to be a limit of three simultaneous connections to the MQTT broker.

I haven't bothered to look into sending commands. You should just use [bambu-connect](https://github.com/mattcar15/bambu-connect) for that.
