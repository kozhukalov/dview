# Install
Create Python virtualenv
```
python3 -m venv .venv
```

Activate Python virtualenv
```
source .venv/bin/activate
```

Install dview-server
```
poetry install
```
if poetry package is not present, use the next command to install it:
`pip install poetry`

<!-- Rpi must have RPi.GPIO module installed:  -->
<!-- `pip install RPi.GPIO` -->

Add systemd service
```
cp dview-server.service /etc/systemd/system/dview-server.service
```

`dview-server.service` assumes the `dview-server` is installed into `/install/dir/.venv`. Change the `dview-server.service` file if necessary.

Enable systemd service

```
systemctl daemon-reload
systemctl enable dview-server
```

## Example request
```
curl -X GET -H "Content-Type: application/json" http://localhost:5010/api/server_status
```