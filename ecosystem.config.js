module.exports = {
  apps: [{
    name: 'mytestxiazai-bot',
    script: 'main_fixed.py',
    interpreter: 'python3',
    cwd: '/root/mytestxiazai_bot',
    env: {
      NODE_ENV: 'production',
      PYTHONUNBUFFERED: '1',
      PYTHONIOENCODING: 'utf-8'
    },
    error_file: '/root/mytestxiazai_bot/logs/error.log',
    out_file: '/root/mytestxiazai_bot/logs/out.log',
    log_file: '/root/mytestxiazai_bot/logs/combined.log',
    time: true,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    restart_delay: 5000,
    max_restarts: 10,
    min_uptime: '10s',
    kill_timeout: 5000,
    wait_ready: true,
    listen_timeout: 10000
  }]
};
