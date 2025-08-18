

pip install mcp pydantic

{
  "mcpServers": {
    "filesystem": {
      "command": "python",
      "args": [
        "-m",
        "filesystem_mcp_server"
      ],
      "env": {
        "FILESYSTEM_BASE_DIR": ".",
        "FILESYSTEM_MAX_FILE_SIZE": "10485760",
        "FILESYSTEM_ALLOWED_EXTENSIONS": "py,js,ts,json,md,txt,html,css,xml,yml,yaml,toml,ini,cfg,log"
      }
    }
  }
}



{
  "servers": {
    "mysql-readonly": {
      "command": "/Users/arpan/Documents/Github/Python/GenAI/ai-cookbook/venv/bin/python",
      "args": [
        "/Users/arpan/Documents/Github/Python/GenAI/ai-cookbook/mcp/crash-course/mysql_mcp_server.py",
        "stdio"
      ],
      "env": {
        "MYSQL_HOST": "localhost",
        "MYSQL_PORT": "3306",
        "MYSQL_USER": "root",
        "MYSQL_PASSWORD": "password",
        "MYSQL_DATABASE": "billing_db",
        "MYSQL_POOL_SIZE": "5"
      }
    }
  }
}
