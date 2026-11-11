# Uptime-Kuma-Web-API



## A REST API wrapper for [Uptime Kuma](https://github.com/louislam/uptime-kuma) using [uptime-kuma-api2](https://github.com/pbarone/uptime-kuma-api2)

This fork works with **Uptime Kuma 2.x** (tested against 2.5.9). It supports `json-query`
monitors (`jsonPath`, `jsonPathOperator`, `expectedValue`) and the other monitor types of the
2.x line.

## Changes in this fork

- Works with Uptime Kuma 2.x through [uptime-kuma-api2](https://github.com/pbarone/uptime-kuma-api2).
- `json-query` monitors with `jsonPath`, `jsonPathOperator` (defaults to `==`) and `expectedValue`.
- `GET /monitors/{id}` also returns `tags` at the top level.
- Create and update answer 400 with the Uptime Kuma message (was 500), 422 for an unsupported
  monitor type and 504 when Uptime Kuma does not answer in time. Update answers 404 only for a
  missing monitor.
- `port` no longer defaults to 53, except for DNS monitors. Port, steam, mqtt and gamedig
  monitors must send it.
- The Docker Hub image of the upstream project does not contain these changes.

---

## EndPoints:

![Alt text](./images/1.png)
![Alt text](./images/2.png)

## How to use it:

---

### Environment Variables :

#### Required
You have to define these ENV VARS in order to connect to your KUMA server.

    KUMA_SERVER: The URL of your Uptime Kuma instance. ex: https://uptime.example.com
    KUMA_USERNAME: The username of your Uptime Kuma user
    KUMA_PASSWORD: The password of your Uptime Kuma user
    ADMIN_PASSWORD: An admin password to access the API

#### Optional
Additional configuration variables available

    ACCESS_TOKEN_EXPIRATION: Minutes the access token should be valid. Defaults to 8 days.
    SECRET_KEY: A secret value to encode JWTs with. Set it: without it a new random key is
                used on every start and all issued tokens stop working after a restart.
    APP_VERSION: Version shown in /openapi.json and /docs. Set it to the deployed release tag.
    KUMA_TIMEOUT: Seconds to wait for Uptime Kuma to connect and to answer. Defaults to 10.
    ENFORCE_HTTPS: Redirect requests that did not arrive over https (reads X-Forwarded-Proto).
                   Defaults to true. Set to false when there is no TLS proxy in front.
    CORS_ALLOW_ORIGINS: Comma separated list of allowed CORS origins. Defaults to * (all).

#### Note:

You have to define your ADMIN_PASSWORD or you wont be able to connect to your rest api.

You will connect with those credentials:

    username = admin
    password = <ADMIN_PASSWORD>

### Features:

- Multi user Kuma api ( without privilege YET!!) with a small SQLite db
- Easy to use REST API with most of the Uptime-Kuma features
- Swagger Docs
- Dockerized: build the image from this repository (`docker build .`). The upstream Docker Hub image does not contain this fork.



## Installation

###  Using Docker Compose 

```yaml
version: "3.9"
services:
  kuma:
    container_name: uptime-kuma
    image: louislam/uptime-kuma:2.5.9
    ports:
      - "3001:3001"
    restart: always
    environment:
      - UPTIME_KUMA_DB_TYPE=sqlite
    volumes:
      - uptime-kuma:/app/data

  api:
    container_name: backend
    build: .  # run from a checkout of this repository
    volumes:
      - api:/db
    restart: always
    environment:
      - KUMA_SERVER=http://kuma:3001
      - KUMA_USERNAME=test
      - KUMA_PASSWORD=123test.
      - ADMIN_PASSWORD=admin
      - SECRET_KEY=<set a random value>
      - ENFORCE_HTTPS=false
    depends_on:
      - kuma
    ports:
      - "8000:8000"

volumes:
  uptime-kuma:
  api:
```

`ENFORCE_HTTPS=false` is for running without a TLS proxy, as the curl example below does.
Behind a TLS proxy, leave it at its default.

### In order for the example to work: You have to run kuma first then create your kuma username and password then re-run the compose file.

### Example CURL Script:

---

TOKEN=$(curl -X -L 'POST' -H 'Content-Type: application/x-www-form-urlencoded' --data 'username=admin&password=admin' http://127.0.0.1:8000/login/access-token/ | jq -r ".access_token")

```bash
curl -X GET \
  -H 'Accept: application/json' \
  -H "Authorization: Bearer ${TOKEN}" \
  http://127.0.0.1:8000/monitors/
```

---

## Testing

`tests/contract.sh` replays the calls an API client makes to manage monitors and tags and
checks the response shapes against a real Uptime Kuma. It needs Docker, curl and jq.

```bash
docker compose up -d --build
NOTIFICATION_ID=$(docker compose exec -T api python - < tests/seed_kuma.py)
NOTIFICATION_ID=$NOTIFICATION_ID tests/contract.sh
docker compose down -v
```

The seed script waits for Uptime Kuma to start (up to two minutes). On the first run it
creates the Kuma admin user. The compose stack uses fixed test credentials and listens on
127.0.0.1 only, so it is for local tests, not for deployment. Use `KUMA_VERSION` to test
another Uptime Kuma release and `API_PORT` / `KUMA_PORT` to change the published ports.
`API_PORT` also changes the port that `tests/contract.sh` calls. Run it before upgrading
Uptime Kuma on a server.

## API Documentation

The API provides comprehensive endpoint documentation through interactive Swagger UI. After starting the application:

1. Navigate to `http://localhost:8000/docs`
2. You can test endpoints directly in the UI
3. Authorization is handled through the "Authorize" button at the top

### Common Endpoints

- `POST /login/access-token` - Get authentication token
- `GET /monitors/` - List all monitors
- `POST /monitors/` - Create a new monitor
- `GET /status-page` - Get status page information

For a complete list of endpoints, refer to the Swagger documentation or the endpoint images above.

##  Known Issues

### CORS Issue with HTTPS Enabled

When running Uptime Kuma with the Web API over HTTPS, you may encounter CORS (Cross-Origin Resource Sharing) errors when accessing the API from another application (e.g., frontend apps, Flutter web, etc.).

**Issue Reference:**
https://github.com/MedAziz11/Uptime-Kuma-Web-API/issues/76

**Description:**
Requests from external applications to the API may fail due to missing or misconfigured CORS headers when HTTPS is enabled.

**Workaround / Fix:**

* Ensure proper CORS configuration is added to the Web API server
* Alternatively, use a reverse proxy (e.g., Nginx) to inject correct CORS headers
* A modified version with potential fixes is available here:
  https://github.com/nifetency/Uptime-Kuma-Web-API

**Note:**
This issue typically appears when accessing the API from a different origin (domain/port/protocol).


## Related Projects

- [Uptime Kuma](https://github.com/nifetency/Uptime-Kuma-Web-API)

---

This repo is forked from [MedAziz11/Uptime-Kuma-Web-API](https://github.com/MedAziz11/Uptime-Kuma-Web-API)
