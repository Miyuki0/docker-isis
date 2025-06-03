import docker
import time
import logging
import requests
import json
from datetime import datetime

class Autoheal:
    def __init__(self, config):
        self.config = config
        self.client = docker.from_env()
        self.logger = self.setup_logging()
        self.containers_attempts = {}
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger('autoheal')
    
    def send_discord_notification(self, message):
        if not self.config.get('discord_webhook'):
            return
            
        payload = {
            "content": message,
            "username": "Docker Autoheal",
            "embeds": [{
                "title": "Container Status Update",
                "description": message,
                "timestamp": datetime.utcnow().isoformat()
            }]
        }
        
        try:
            response = requests.post(
                self.config['discord_webhook'],
                data=json.dumps(payload),
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()
        except Exception as e:
            self.logger.error(f"Failed to send Discord notification: {str(e)}")
    
    def should_monitor_container(self, container):
        # Skip self-monitoring
        if container.id == self.config.get('self_container_id'):
            return False
            
        labels = container.labels or {}
        
        # Mode-specific checks
        if self.config['mode'] == 'labeled':
            return labels.get('autoheal.enable', '').lower() == 'true'
        else:  # all mode
            return True
    
    def get_restart_policy(self, container):
        labels = container.labels or {}
        policy = labels.get('autoheal.restart.policy', self.config['default_policy'])
        max_attempts = int(labels.get('autoheal.restart.max_attempts', self.config['max_attempts']))
        return policy, max_attempts
    
    def check_and_heal(self):
        try:
            for container in self.client.containers.list(all=True):
                if not self.should_monitor_container(container):
                    continue
                
                container.reload()  # Refresh container data
                name = container.name
                status = container.status
                health = container.attrs.get('State', {}).get('Health', {}).get('Status', 'none')
                
                self.logger.debug(f"Checking container {name} - Status: {status}, Health: {health}")
                
                # Check if container needs healing
                needs_healing = False
                reason = ""
                
                if status == 'exited' and self.config['restart_exited']:
                    needs_healing = True
                    reason = "exited"
                elif health == 'unhealthy' and self.config['restart_unhealthy']:
                    needs_healing = True
                    reason = "unhealthy"
                
                if needs_healing:
                    policy, max_attempts = self.get_restart_policy(container)
                    current_attempts = self.containers_attempts.get(name, 0) + 1
                    
                    if policy == 'never':
                        continue
                    elif policy == 'always' or (policy == 'on-failure' and current_attempts <= max_attempts):
                        try:
                            self.logger.info(f"Restarting container {name} (reason: {reason}, attempt {current_attempts}/{max_attempts})")
                            container.restart()
                            self.containers_attempts[name] = current_attempts
                            
                            # Send Discord notification
                            message = f"Restarted container **{name}** (Reason: {reason}, Attempt: {current_attempts}/{max_attempts})"
                            self.send_discord_notification(message)
                            
                        except Exception as e:
                            self.logger.error(f"Failed to restart container {name}: {str(e)}")
                            message = f"Failed to restart container **{name}**: {str(e)}"
                            self.send_discord_notification(message)
                    else:
                        self.logger.warning(f"Max restart attempts ({max_attempts}) reached for container {name}")
                        message = f"Max restart attempts reached for container **{name}** - no further attempts will be made"
                        self.send_discord_notification(message)
                else:
                    # Reset attempt counter if container is healthy/running
                    if name in self.containers_attempts:
                        del self.containers_attempts[name]
                        
        except Exception as e:
            self.logger.error(f"Error during container check: {str(e)}")
            message = f"Autoheal encountered an error: {str(e)}"
            self.send_discord_notification(message)

def main():
    import os
    
    config = {
        'mode': os.getenv('AUTOHEAL_MODE', 'all'),  # 'all' or 'labeled'
        'restart_exited': os.getenv('AUTOHEAL_RESTART_EXITED', 'true').lower() == 'true',
        'restart_unhealthy': os.getenv('AUTOHEAL_RESTART_UNHEALTHY', 'true').lower() == 'true',
        'default_policy': os.getenv('AUTOHEAL_DEFAULT_POLICY', 'on-failure'),  # 'always', 'on-failure', 'never'
        'max_attempts': int(os.getenv('AUTOHEAL_MAX_ATTEMPTS', '5')),
        'check_interval': int(os.getenv('AUTOHEAL_CHECK_INTERVAL', '5')),
        'discord_webhook': os.getenv('AUTOHEAL_DISCORD_WEBHOOK', ''),
        'self_container_id': os.getenv('HOSTNAME', '')  # Docker sets HOSTNAME to container ID
    }
    
    autoheal = Autoheal(config)
    autoheal.logger.info(f"Starting autoheal with config: {config}")
    
    while True:
        autoheal.check_and_heal()
        time.sleep(config['check_interval'])

if __name__ == '__main__':
    main()
