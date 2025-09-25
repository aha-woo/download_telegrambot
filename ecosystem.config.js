module.exports = {
  apps: [{
    name: 'mytestxiazai-bot',
    script: 'main.py',
    interpreter: '/root/mytestxiazai_bot/venv/bin/python3',
    cwd: '/root/mytestxiazai_bot',
    env: {
      NODE_ENV: 'production',
      PYTHONUNBUFFERED: '1',
      PYTHONIOENCODING: 'utf-8',
      VIRTUAL_ENV: '/root/mytestxiazai_bot/venv',
      PATH: '/root/mytestxiazai_bot/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'
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
