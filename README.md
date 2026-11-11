# Uptime-Kuma-Web-API



## A REST API wrapper for [Uptime Kuma](https://github.com/louislam/uptime-kuma) using [uptime-kuma-api2](https://github.com/pbarone/uptime-kuma-api2)

This fork works with **Uptime Kuma 2.x** (tested against 2.5.9). It supports `json-query`
monitors (`jsonPath`, `jsonPathOperator`, `expectedValue`) and the other monitor types of the
2.x line.

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
- Multi-architecture support (amd64, arm64)



## Installation

###  Using Docker Compose 

```yaml
version: "3.9"
services:
  kuma:
    container_name: uptime-kuma
    image: louislam/uptime-kuma:latest
    ports:
      - "3001:3001"
    restart: always
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
    depends_on:
      - kuma
    ports:
      - "8000:8000"

volumes:
  uptime-kuma:
  api:
```

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

The first run of the seed script creates the Kuma admin user and can take a minute. Use
`KUMA_VERSION` to test another Uptime Kuma release and `API_PORT` / `KUMA_PORT` to change the
published ports. Run it before upgrading Uptime Kuma on a server.

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
