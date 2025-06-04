
# Docker-paramedic

**Automatically monitor and restart unhealthy or exited Docker containers**  
_Because sometimes containers need a little CPR_

## Features

-   **Smart Monitoring**: Watches for both exited and unhealthy containers
    
-   **Flexible Modes**: Monitor all containers or only labeled ones
    
-   **Restart Policies**: Configurable restart strategies (always, on-failure, never)
    
-   **Attempt Limiting**: Prevent infinite restart loops with max attempt limits
    
-   **Discord Integration**: Get notified about container restarts via webhooks
    
-   **Self-Preservation**: Automatically avoids monitoring itself
    
-   **Cross-Platform**: Works on Linux, Windows (Docker Desktop), and macOS
    

## Quick Start

```bash
docker run -d \
  --name autoheal \
  -v /var/run/docker.sock:/var/run/docker.sock \
  yourusername/autoheal
```
_For Windows Docker Desktop users:_

```bash
docker run -d \
  --name autoheal \
  -v //var/run/docker.sock:/var/run/docker.sock \
  yourusername/autoheal
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|--|--|--|
| `AUTOHEAL_MODE` | `all` | `all` or `labeled` (only monitors containers with `autoheal.enable=true` label) |
| `AUTOHEAL_RESTART_EXITED` | `true` | Restart exited containers |
| `AUTOHEAL_RESTART_UNHEALTHY` | `true` | Restart unhealthy containers |
| `AUTOHEAL_DEFAULT_POLICY` | `on-failure` | `always`, `on-failure` or `never` |
| `AUTOHEAL_MAX_ATTEMPTS` | `5` | Max restart attempts for `on-failure` policy |
| `AUTOHEAL_CHECK_INTERVAL` | `5` | Check interval in seconds |
| `AUTOHEAL_DISCORD_WEBHOOK` |  | Discord webhook URL for notifications |


### Container Labels

Label your containers to customize behavior:

```bash
docker run -d \
  --label autoheal.enable=true \
  --label autoheal.restart.policy=on-failure \
  --label autoheal.restart.max_attempts=3 \
  nginx:alpine
```
| Label | Values | Description |
|--|--|--|
| `autoheal.enable` | `true` / `false` | Required when in `labeled` mode |
| `autoheal.restart.policy` | `always`, `on-failure`, `never` | Overrides default policy |
| `autoheal.restart.max_attepts` | number | Overrides default max attempts |


## Examples

### 1. Basic Monitoring

```bash
docker run -d \
  --name autoheal \
  -v /var/run/docker.sock:/var/run/docker.sock \
  yourusername/autoheal
  ```

### 2. Discord Notifications

```bash
docker run -d \
  --name autoheal \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -e AUTOHEAL_DISCORD_WEBHOOK=https://discord.com/api/webhooks/... \
  yourusername/autoheal
```

### 3. Label-Based Monitoring

```bash
docker run -d \
  --name autoheal \
  -e AUTOHEAL_MODE=labeled \
  -v /var/run/docker.sock:/var/run/docker.sock \
  yourusername/autoheal

#Then label containers you want monitored:

docker run -d \
  --label autoheal.enable=true \
  --label autoheal.restart.policy=always \
  nginx:alpine
  ```

## Health Checks

For containers to be recognized as "unhealthy," they must have a HEALTHCHECK defined:

```dockerfile

HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD curl -f http://localhost/ || exit 1
```

## Building Locally

```bash
git clone https://github.com/Miyuki0/docker-paramedic.git
cd docker-autoheal
docker build -t autoheal .
```

## Inspiration

Shoutout to  [willfarrell/docker-autoheal](https://github.com/willfarrell/docker-autoheal)  repository for the inspo. This repo uses the same concept but implemented in a lighter, more configurable way with additional features like Discord notifications, granular restart policies, and Windows support. While preserving the core functionality, this version offers enhanced flexibility for different use cases.

## Contributing

Pull requests are welcome! For major changes, please open an issue first.
