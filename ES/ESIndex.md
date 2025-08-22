{
  "mappings": {
    "properties": {
      "@timestamp": {
        "type": "date"
      },
      "client_ip": {
        "type": "ip"
      },
      "route_id": {
        "type": "keyword"
      },
      "server": {
        "properties": {
          "hostname": {
            "type": "keyword"
          },
          "version": {
            "type": "keyword"
          }
        }
      },
      "apisix_latency": {
        "type": "float"
      },
      "start_time": {
        "type": "date",
        "format": "epoch_millis"
      },
      "upstream_latency": {
        "type": "float"
      },
      "total_latency": {
        "type": "float"
      },
      "request": {
        "properties": {
          "url": {
            "type": "text",
            "fields": {
              "keyword": {
                "type": "keyword"
              }
            }
          },
          "method": {
            "type": "keyword"
          },
          "size": {
            "type": "integer"
          },
          "uri": {
            "type": "keyword"
          },
          "headers": {
            "properties": {
              "accept-encoding": {
                "type": "keyword"
              },
              "content-type": {
                "type": "keyword"
              },
              "user-agent": {
                "type": "text",
                "fields": {
                  "keyword": {
                    "type": "keyword"
                  }
                }
              },
              "host": {
                "type": "keyword"
              },
              "postman-token": {
                "type": "keyword"
              },
              "connection": {
                "type": "keyword"
              },
              "accept": {
                "type": "keyword"
              }
            }
          }
        }
      },
      "service_id": {
        "type": "keyword"
      },
      "response": {
        "properties": {
          "headers": {
            "properties": {
              "content-type": {
                "type": "keyword"
              },
              "content-length": {
                "type": "integer"
              },
              "date": {
                "type": "date",
                "format": "EEE, dd MMM yyyy HH:mm:ss zzz"
              },
              "connection": {
                "type": "keyword"
              },
              "server": {
                "type": "keyword"
              },
              "apisix-plugins": {
                "type": "keyword"
              }
            }
          },
          "status": {
            "type": "integer"
          },
          "body": {
            "type": "text",
            "index": false
          },
          "size": {
            "type": "integer"
          }
        }
      },
      "upstream": {
        "type": "keyword"
      },
      "latency": {
        "type": "float"
      },
      "policies_count": {
        "type": "integer"
      },
      "enabled_policies_count": {
        "type": "integer"
      },
      "status_class": {
        "type": "keyword"
      },
      "hour_of_day": {
        "type": "integer"
      },
      "day_of_week": {
        "type": "keyword"
      }
    }
  }
}
