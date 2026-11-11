#!/bin/bash
# Contract test: replays the calls an API client makes to manage monitors and tags
# (login, create json-query and http monitors, list, tag, read, update, delete) and
# checks the response shapes. Needs curl and jq, and the stack from docker-compose.yml:
#
#   docker compose up -d --build
#   NOTIFICATION_ID=$(docker compose exec -T api python - < tests/seed_kuma.py)
#   NOTIFICATION_ID=$NOTIFICATION_ID tests/contract.sh
#
# Run the seed script first: NOTIFICATION_ID is required (the id it prints).
# Exits non-zero on the first failed check.

BASE_URL="${BASE_URL:-http://127.0.0.1:${API_PORT:-8000}}"
API_USERNAME="${API_USERNAME:-admin}"
API_PASSWORD="${API_PASSWORD:-admin}"
NOTIFICATION_ID="${NOTIFICATION_ID:-}"
if [[ ! "${NOTIFICATION_ID}" =~ ^[1-9][0-9]*$ ]]; then
  echo "NOTIFICATION_ID must be a positive integer. Run tests/seed_kuma.py first and pass the id it prints." >&2
  exit 2
fi
# URL the json-query monitor checks, as seen from the Uptime Kuma container. Any JSON
# document without a queue named "failed" makes the query below return 0.
JSON_URL="${JSON_URL:-http://api:8000/openapi.json}"
# Seconds to wait for the first heartbeat of the json-query monitor.
HEARTBEAT_WAIT="${HEARTBEAT_WAIT:-60}"

RUN_ID="contract-$(date +%s)-$$"
STEP=0
BODY_FILE=$(mktemp)
MONITOR_IDS=()
TAG_ID=""
TOKEN=""
trap 'cleanup' EXIT

cleanup() {
  if [ -n "${TOKEN}" ]; then
    for id in "${MONITOR_IDS[@]}"; do
      curl -s -o /dev/null -X DELETE -H "Authorization: Bearer ${TOKEN}" "${BASE_URL}/monitors/${id}"
    done
    if [ -n "${TAG_ID}" ]; then
      curl -s -o /dev/null -X DELETE -H "Authorization: Bearer ${TOKEN}" "${BASE_URL}/tags/${TAG_ID}"
    fi
  fi
  rm -f "${BODY_FILE}"
}

pass() { STEP=$((STEP + 1)); echo "ok ${STEP} - $1"; }
fail() { STEP=$((STEP + 1)); echo "not ok ${STEP} - $1"; echo "    response: $(head -c 600 "${BODY_FILE}")"; exit 1; }

# call METHOD PATH [JSON_BODY] -> prints the HTTP status, stores the body in BODY_FILE
call() {
  local method=$1 path=$2 body=${3:-}
  if [ -n "${body}" ]; then
    curl -s -o "${BODY_FILE}" -w '%{http_code}' -X "${method}" \
      -H 'Accept: application/json' -H 'Content-Type: application/json' \
      -H "Authorization: Bearer ${TOKEN}" --data "${body}" "${BASE_URL}${path}"
  else
    curl -s -o "${BODY_FILE}" -w '%{http_code}' -X "${method}" \
      -H 'Accept: application/json' -H "Authorization: Bearer ${TOKEN}" "${BASE_URL}${path}"
  fi
}

# 1. Login
status=$(curl -s -o "${BODY_FILE}" -w '%{http_code}' -X POST "${BASE_URL}/login/access-token" \
  -H 'Accept: application/json' -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode 'grant_type=password' --data-urlencode "username=${API_USERNAME}" \
  --data-urlencode "password=${API_PASSWORD}")
TOKEN=$(jq -r '.access_token // empty' "${BODY_FILE}")
[ "${status}" = 200 ] && [ -n "${TOKEN}" ] && pass "login returns access_token" || fail "login (HTTP ${status})"

# 2. Create a json-query monitor (the "queue must be empty" check)
QUEUE_URL="${JSON_URL}?run=${RUN_ID}"
json_query_body=$(jq -n --arg name "${RUN_ID} - RabbitMQ" --arg url "${QUEUE_URL}" --argjson nid "${NOTIFICATION_ID}" '{
  type: "json-query", name: $name, url: $url, interval: 300, notificationIDList: [$nid],
  method: "GET", accepted_statuscodes: ["200-299"], authMethod: "basic",
  basic_auth_user: "guest", basic_auth_pass: "guest",
  jsonPath: "$sum([0, $[name='failed'].messages])", jsonPathOperator: "==", expectedValue: "0"}')
status=$(call POST /monitors "${json_query_body}")
JSON_MONITOR_ID=$(jq -r '.monitorID // empty' "${BODY_FILE}")
[[ "${status}" = 200 && "${JSON_MONITOR_ID}" =~ ^[0-9]+$ ]] && pass "create json-query monitor returns monitorID" || fail "create json-query monitor (HTTP ${status})"
MONITOR_IDS+=("${JSON_MONITOR_ID}")

# 3. Create an http monitor (the "site is up" check)
http_body=$(jq -n --arg name "${RUN_ID}.example.com" --argjson nid "${NOTIFICATION_ID}" '{
  type: "http", name: $name, url: ("https://" + $name + "/"), interval: 60, notificationIDList: [$nid],
  method: "GET", accepted_statuscodes: ["200-299"], maxretries: 0, timeout: 48, resendInterval: 0,
  expiryNotification: true}')
status=$(call POST /monitors "${http_body}")
HTTP_MONITOR_ID=$(jq -r '.monitorID // empty' "${BODY_FILE}")
[[ "${status}" = 200 && "${HTTP_MONITOR_ID}" =~ ^[0-9]+$ ]] && pass "create http monitor returns monitorID" || fail "create http monitor (HTTP ${status})"
MONITOR_IDS+=("${HTTP_MONITOR_ID}")

# 4. List monitors: {"monitors": [...]} with id and url
status=$(call GET /monitors)
[ "${status}" = 200 ] && jq -e --arg url "${QUEUE_URL}" --arg id "${JSON_MONITOR_ID}" \
  'any(.monitors[]; .url == $url and (.id | tostring) == $id)' "${BODY_FILE}" > /dev/null 2>&1 && pass "list monitors finds the monitor by url" || fail "list monitors (HTTP ${status})"

# 5. Tags: list, create, attach
status=$(call GET /tags)
[ "${status}" = 200 ] && jq -e '.tags | type == "array"' "${BODY_FILE}" > /dev/null && pass "list tags returns {tags: [...]}" || fail "list tags (HTTP ${status})"
TAG_NAME="${RUN_ID}-tag"
status=$(call POST /tags "$(jq -n --arg name "${TAG_NAME}" '{name: $name, color: "#FF6600"}')")
TAG_ID=$(jq -r '.id // .tag.id // empty' "${BODY_FILE}")
[[ "${status}" = 200 && "${TAG_ID}" =~ ^[0-9]+$ ]] && pass "create tag returns id" || fail "create tag (HTTP ${status})"
status=$(call POST "/monitors/${JSON_MONITOR_ID}/tag" "$(jq -n --argjson id "${TAG_ID}" '{tag_id: $id, value: ""}')")
[ "${status}" = 200 ] && jq -e 'type == "object" or type == "array"' "${BODY_FILE}" > /dev/null && pass "attach tag to monitor" || fail "attach tag (HTTP ${status})"

# 6. Read the monitor: tags at the top level and under "monitor", json-query fields stored
status=$(call GET "/monitors/${JSON_MONITOR_ID}")
[ "${status}" = 200 ] && jq -e --arg name "${TAG_NAME}" 'any(.tags[]; .name == $name) and any(.monitor.tags[]; .name == $name)' "${BODY_FILE}" > /dev/null \
  && pass "get monitor returns tags at the top level" || fail "get monitor tags (HTTP ${status})"
# notificationIDList comes back as a list of ids or as an object keyed by id.
jq -e --argjson nid "${NOTIFICATION_ID}" '.monitor | .type == "json-query" and .jsonPathOperator == "==" and .expectedValue == "0"
  and (.jsonPath | startswith("$sum("))
  and (.notificationIDList | if type == "object" then has($nid | tostring) else any(.[]; tostring == ($nid | tostring)) end)' \
  "${BODY_FILE}" > /dev/null \
  && pass "json-query fields are stored" || fail "json-query fields"

# 7. Update the http monitor with a full body
status=$(call PATCH "/monitors/${HTTP_MONITOR_ID}" "$(echo "${http_body}" | jq '.interval = 120')")
[ "${status}" = 200 ] && pass "update monitor with a full body" || fail "update monitor (HTTP ${status})"
status=$(call GET "/monitors/${HTTP_MONITOR_ID}")
jq -e '.monitor | .interval == 120 and .timeout == 48 and .expiryNotification == true' "${BODY_FILE}" > /dev/null \
  && pass "update is stored" || fail "updated monitor (HTTP ${status})"
status=$(call PATCH /monitors/999999 "${http_body}")
[ "${status}" = 404 ] && pass "update of a missing monitor returns 404" || fail "update missing monitor (HTTP ${status})"

# 8. The json-query monitor goes UP (status 1) in Uptime Kuma
up=""
attempts=$((HEARTBEAT_WAIT / 5))
[ "${attempts}" -lt 1 ] && attempts=1
for _ in $(seq 1 "${attempts}"); do
  status=$(call GET "/monitors/${JSON_MONITOR_ID}/beats?hours=1")
  up=$(jq -r '.monitor_beats[-1].status // empty' "${BODY_FILE}" 2>/dev/null)
  [ -n "${up}" ] && break
  sleep 5
done
[[ "${up}" = 1 || "${up}" = "MonitorStatus.UP" ]] && pass "json-query monitor is UP" || fail "json-query monitor status '${up}'"

# 9. Delete, then delete again
status=$(call DELETE "/monitors/${HTTP_MONITOR_ID}")
[ "${status}" = 200 ] && pass "delete monitor" || fail "delete monitor (HTTP ${status})"
status=$(call DELETE "/monitors/${HTTP_MONITOR_ID}")
[ "${status}" = 404 ] && pass "delete of a missing monitor returns 404" || fail "second delete (HTTP ${status})"
status=$(call DELETE "/monitors/${JSON_MONITOR_ID}")
[ "${status}" = 200 ] && pass "delete json-query monitor" || fail "delete json-query monitor (HTTP ${status})"
MONITOR_IDS=()
status=$(call DELETE "/tags/${TAG_ID}")
[ "${status}" = 200 ] && pass "delete tag" || fail "delete tag (HTTP ${status})"
TAG_ID=""

echo "all ${STEP} checks passed"
