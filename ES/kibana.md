# Kibana Dashboard Guide for APISIX API Gateway Logs

## 1. Index Pattern Setup

1. **Create Index Pattern:**
   - Go to Kibana > Stack Management > Index Patterns
   - Create pattern: `apisix-logs-*`
   - Set time field: `@timestamp`

## 2. Essential Visualizations

### A. Performance Metrics Dashboard

#### 1. Response Time Overview
- **Visualization Type:** Line Chart
- **Metrics:** Average of `total_latency`, `upstream_latency`, `apisix_latency`
- **Buckets:** Date Histogram on `@timestamp` (1 minute intervals)
- **Split Series:** By metric type

#### 2. Latency Distribution
- **Visualization Type:** Histogram
- **Y-axis:** Count
- **X-axis:** Histogram of `total_latency` (10-20 buckets)

#### 3. Response Status Distribution
- **Visualization Type:** Pie Chart
- **Metrics:** Count
- **Buckets:** Terms aggregation on `status_class`

#### 4. Request Volume Over Time
- **Visualization Type:** Area Chart
- **Metrics:** Count
- **Buckets:** Date Histogram on `@timestamp` (5 minute intervals)

### B. API Usage Dashboard

#### 1. Top Routes by Volume
- **Visualization Type:** Horizontal Bar Chart
- **Metrics:** Count
- **Buckets:** Terms aggregation on `route_id` (top 10)

#### 2. Client IP Analysis
- **Visualization Type:** Data Table
- **Metrics:** Count, Average `total_latency`
- **Buckets:** Terms on `client_ip` (top 20)

#### 3. User Agent Distribution
- **Visualization Type:** Tag Cloud
- **Metrics:** Count
- **Buckets:** Terms on `request.headers.user-agent.keyword`

#### 4. Request Size vs Response Size
- **Visualization Type:** Scatter Plot
- **X-axis:** Average `request.size`
- **Y-axis:** Average `response.size`
- **Split Chart:** Terms on `route_id`

### C. Error Monitoring Dashboard

#### 1. Error Rate Over Time
- **Visualization Type:** Line Chart
- **Metrics:** 
  - Total Count (all requests)
  - Count with filter: `response.status >= 400`
- **Buckets:** Date Histogram (1 minute intervals)

#### 2. Error Status Breakdown
- **Visualization Type:** Vertical Bar Chart
- **Metrics:** Count
- **Buckets:** Terms on `response.status`
- **Filter:** `response.status >= 400`

#### 3. Error Heatmap by Hour
- **Visualization Type:** Heat Map
- **Metrics:** Count with filter `response.status >= 400`
- **X-axis:** Terms on `hour_of_day`
- **Y-axis:** Terms on `day_of_week`

### D. Policy Management Dashboard

#### 1. Policy Count Distribution
- **Visualization Type:** Metric
- **Metrics:** Average of `policies_count`, Average of `enabled_policies_count`

#### 2. Policy Trends
- **Visualization Type:** Line Chart
- **Metrics:** Average `enabled_policies_count`
- **Buckets:** Date Histogram (1 hour intervals)

### E. Infrastructure Monitoring

#### 1. Server Performance
- **Visualization Type:** Data Table
- **Metrics:** Count, Average `total_latency`, Max `total_latency`
- **Buckets:** Terms on `server.hostname`

#### 2. Upstream Health
- **Visualization Type:** Metric
- **Metrics:** Average `upstream_latency`
- **Buckets:** Terms on `upstream`

## 3. Dashboard Layout Suggestions

### Performance Overview Dashboard
```
[Response Time Trends] [Request Volume]
[Latency Distribution] [Status Distribution]
[Top Slow Endpoints] [Performance by Hour]
```

### Error Monitoring Dashboard
```
[Error Rate Trend] [Error Count by Status]
[Error Heatmap by Time] [Top Error Routes]
[Client IPs with Most Errors]
```

### Operational Dashboard
```
[Live Request Count] [Average Response Time]
[Policy Statistics] [Server Health]
[Top Client IPs] [Request Size Trends]
```

## 4. Useful Filters and Controls

Add these as dashboard controls:

1. **Time Range Picker**
2. **Route ID Filter** (Dropdown)
3. **Client IP Filter** (Text input)
4. **Status Code Filter** (Dropdown)
5. **Server Hostname Filter** (Dropdown)

## 5. Alerting Setup

### Recommended Alerts

1. **High Error Rate:**
   - Condition: Error rate > 5% over 5 minutes
   - Query: `response.status >= 400`

2. **High Latency:**
   - Condition: Average latency > 1000ms over 5 minutes
   - Query: Average of `total_latency`

3. **Low Request Volume:**
   - Condition: Request count drops below threshold
   - Useful for detecting service outages

## 6. Index Lifecycle Management

Set up ILM policy for log retention:

```json
{
  "policy": {
    "phases": {
      "hot": {
        "actions": {
          "rollover": {
            "max_size": "5GB",
            "max_age": "1d"
          }
        }
      },
      "warm": {
        "min_age": "7d",
        "actions": {
          "allocate": {
            "number_of_replicas": 0
          }
        }
      },
      "delete": {
        "min_age": "30d"
      }
    }
  }
}
```

## 7. Performance Optimization Tips

1. **Use keyword fields** for exact match filters
2. **Set appropriate refresh intervals** (30s-1m for dashboards)
3. **Use date math** in index patterns for better performance
4. **Create data views** with relevant field filters
5. **Use query filters** instead of post-filters when possible

## 8. Custom Scripted Fields

Add these in Index Pattern management:

1. **Response Time Category:**
```javascript
if (doc['total_latency'].size() > 0) {
  def latency = doc['total_latency'].value;
  if (latency < 100) return 'Fast';
  else if (latency < 500) return 'Normal';
  else if (latency < 1000) return 'Slow';
  else return 'Very Slow';
}
return 'Unknown';
```

2. **Peak Hour Indicator:**
```javascript
if (doc['hour_of_day'].size() > 0) {
  def hour = doc['hour_of_day'].value;
  return (hour >= 9 && hour <= 17) ? 'Business Hours' : 'Off Hours';
}
return 'Unknown';
```
